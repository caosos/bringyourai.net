#!/usr/bin/env python3
"""Build Keith Household Payment Records court ledger from bank statement PDFs.

Source PDFs belong in /work/keith_court_evidence/pdfs/ unless --pdf-dir is used.
The script writes the required workbook and CSVs to /work/keith_court_evidence/.

Accuracy rule: this tool never invents merchant names or item-level details. Rows
that cannot be responsibly parsed or categorized are marked Needs Review / low
confidence and retain source PDF/page traceability.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import dataclasses
import html
import importlib.util
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Sequence

WORK_DIR = Path("/work/keith_court_evidence")
DEFAULT_PDF_DIR = WORK_DIR / "pdfs"
OUTPUT_XLSX = WORK_DIR / "Keith_Household_Payment_Records_Court_Ledger.xlsx"
MASTER_CSV = WORK_DIR / "master_transactions.csv"
SUMMARY_CSV = WORK_DIR / "monthly_summary.csv"
SOURCE_INDEX_CSV = WORK_DIR / "source_index.csv"
ZIP_INDEX_CSV = WORK_DIR / "zip_extraction_index.csv"
EXTRACTED_TEXT_DIR = WORK_DIR / "extracted_text"

MASTER_COLUMNS = [
    "Bank", "Account", "Statement Month", "Posted Date", "Transaction Date", "Description",
    "Merchant / Payee", "Category", "Subcategory", "Credit", "Debit", "Net", "Balance",
    "Source PDF", "Source Page", "Confidence", "Notes",
]
SOURCE_COLUMNS = ["Bank", "Account", "Statement Month", "Statement Period", "PDF Filename", "Pages", "Extraction Status", "Rows Extracted", "Notes"]
ZIP_COLUMNS = ["ZIP Filename", "Member", "Extracted PDF"]
SUMMARY_COLUMNS = [
    "Month", "Bank", "Home Repair / Supplies", "Groceries / Household", "Utilities", "Insurance",
    "Medical / Health", "Fuel / Transportation", "Cash / Unknown", "Income / Deposits",
    "Banking Fees / Interest", "Uncategorized / Review", "Total Debits", "Total Credits", "Net",
]
CATEGORIES = SUMMARY_COLUMNS[2:12]
MONTHS = ["Dec 2024", "Jan 2025", "Feb 2025", "Mar 2025", "Apr 2025", "May 2025", "Jun 2025", "Jul 2025", "Aug 2025", "Sep 2025", "Oct 2025", "Nov 2025"]

CATEGORY_RULES: list[tuple[str, str, str]] = [
    ("Home Repair / Supplies", r"\b(home\s*depot|lowe'?s|harbor\s*freight|rockauto|hardware|lumber|building\s*materials?|tools?)\b", "home repair/supplies merchant keyword"),
    ("Groceries / Household", r"\b(wal[-\s]*mart|walmart|sam'?s\s*club|dollar\s*tree|kroger|grocery|groceries|market|supercenter)\b", "groceries/household merchant keyword"),
    ("Utilities", r"\b(entergy|electric|water|trash|sanitation|city\s+utilit|lightband|internet|utility|utilities)\b", "utility merchant keyword"),
    ("Insurance", r"\b(state\s*farm|insurance|policy)\b", "insurance merchant keyword"),
    ("Medical / Health", r"\b(pharmacy|walgreens|cvs|hospital|clinic|doctor|dental|dentist|animal\s+hospital|veterinar|vet\b)\b", "medical/health merchant keyword; veterinary noted when present"),
    ("Fuel / Transportation", r"\b(murphy|shell|exxon|chevron|bp\b|circle\s*k|conoco|valero|pilot|love'?s|gas\s+station|fuel|auto\s*zone|o'?reilly|oreilly|advance\s+auto)\b", "fuel/transportation merchant keyword"),
    ("Cash / Unknown", r"\b(atm|cash\s+withdraw|withdrawal|cash\s+advance)\b", "cash withdrawal keyword"),
    ("Income / Deposits", r"\b(ssa\s+treasury|treasury|payroll|direct\s+deposit|cash\s*app|deposit|credit\s+posted)\b", "income/deposit keyword"),
    ("Banking Fees / Interest", r"\b(atm\s+fee|service\s+fee|fee\b|rebate|dividend|interest|adjustment)\b", "banking fee/interest keyword"),
]

DATE_RE = re.compile(r"^(?P<date>(?:\d{1,2}/\d{1,2}(?:/\d{2,4})?)|(?:[A-Z][a-z]{2}\s+\d{1,2}))\s+(?P<rest>.+)$")
MONEY_RE = re.compile(r"(?<!\d)-?\$?\(?\d{1,3}(?:,\d{3})*(?:\.\d{2})\)?(?!\d)")
PERIOD_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:-|through|to)\s*(\d{1,2}/\d{1,2}/\d{2,4})", re.I)
ACCOUNT_RE = re.compile(r"(?:account|acct)\s*(?:number|no\.?|#)?\s*[:#]?\s*([*xX\d\- ]{4,})", re.I)
SUMMARY_HINT_RE = re.compile(r"\b(total|summary|payments?|credits?|debits?|withdrawals?)\b", re.I)

@dataclasses.dataclass
class PageText:
    page: int
    text: str


def parse_money(value: str) -> Decimal:
    cleaned = value.replace("$", "").replace(",", "").strip()
    negative = cleaned.startswith("-") or (cleaned.startswith("(") and cleaned.endswith(")"))
    cleaned = cleaned.strip("-()")
    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0.00")
    return -amount if negative else amount


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(name).name).strip(" .")
    return cleaned or "statement.pdf"


def discover_zip_files(zip_dirs: Sequence[Path]) -> list[Path]:
    archives: list[Path] = []
    seen: set[Path] = set()
    for directory in zip_dirs:
        if not directory.exists():
            continue
        for archive in sorted(directory.rglob("*.zip")):
            resolved = archive.resolve()
            if resolved not in seen:
                seen.add(resolved)
                archives.append(archive)
    return archives


def extract_pdf_zips(zip_files: Sequence[Path], pdf_dir: Path) -> list[dict[str, object]]:
    """Extract PDFs from provided ZIP archives into the PDF working folder.

    ZIP members are flattened and sanitized so an archive cannot write outside
    the court-evidence workspace. Existing extracted files are left in place so
    rerunning the builder does not create duplicate PDFs.
    """
    pdf_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, object]] = []
    for archive in zip_files:
        try:
            with zipfile.ZipFile(archive) as zf:
                pdf_members = [member for member in zf.infolist() if not member.is_dir() and member.filename.lower().endswith(".pdf")]
                for member in pdf_members:
                    target_name = safe_filename(member.filename)
                    archive_hint = safe_filename(archive.stem)
                    if archive_hint and archive_hint.lower() not in target_name.lower():
                        target_name = f"{archive_hint} - {target_name}"
                    target = pdf_dir / target_name
                    if target.exists():
                        extracted.append({"ZIP Filename": str(archive), "Member": member.filename, "Extracted PDF": f"Already present: {target}"})
                        continue
                    with zf.open(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted.append({"ZIP Filename": str(archive), "Member": member.filename, "Extracted PDF": str(target)})
        except zipfile.BadZipFile:
            extracted.append({"ZIP Filename": str(archive), "Member": "", "Extracted PDF": "Needs Review: invalid ZIP archive"})
    return extracted


def statement_sort_key(month: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(month, "%b %Y")
        return (dt.year, dt.month)
    except ValueError:
        return (9999, 99)


def parse_statement_date(value: str, statement_month: str) -> datetime | None:
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%b %d"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%b %d" and statement_month != "Needs Review":
                parsed = parsed.replace(year=int(statement_month.split()[1]))
            return parsed
        except ValueError:
            pass
    if re.match(r"^\d{1,2}/\d{1,2}$", value) and statement_month != "Needs Review":
        month, day = [int(part) for part in value.split("/")]
        year = int(statement_month.split()[1])
        if statement_month.startswith("Jan") and month == 12:
            year -= 1
        return datetime(year, month, day)
    return None


def normalize_date(value: str, statement_month: str) -> str:
    parsed = parse_statement_date(value, statement_month)
    return parsed.strftime("%Y-%m-%d") if parsed else value


def extract_with_pdftotext(pdf_path: Path) -> list[PageText] | None:
    try:
        result = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], check=True, capture_output=True, text=True, timeout=60)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    pages = result.stdout.split("\f")
    return [PageText(i + 1, text) for i, text in enumerate(pages) if text.strip()]


def extract_with_optional_python_libs(pdf_path: Path) -> list[PageText] | None:
    if importlib.util.find_spec("pdfplumber") is not None:
        import pdfplumber  # type: ignore

        try:
            with pdfplumber.open(pdf_path) as pdf:
                return [PageText(i + 1, page.extract_text(x_tolerance=1, y_tolerance=3) or "") for i, page in enumerate(pdf.pages)]
        except Exception:
            pass
    if importlib.util.find_spec("pypdf") is not None:
        from pypdf import PdfReader  # type: ignore

        try:
            reader = PdfReader(str(pdf_path))
            return [PageText(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
        except Exception:
            return None
    return None


def extract_pdf_text(pdf_path: Path) -> tuple[list[PageText], str]:
    for label, extractor in (("pdftotext", extract_with_pdftotext), ("python PDF text extraction", extract_with_optional_python_libs)):
        pages = extractor(pdf_path)
        if pages and any(page.text.strip() for page in pages):
            return pages, label
    return [], "No deterministic PDF text extractor available or no text layer found; OCR/manual review required"


def infer_bank(filename: str, text: str) -> str:
    haystack = f"{filename} {text[:2000]}".lower()
    if "navy" in haystack or "nfcu" in haystack:
        return "Navy Federal"
    if "arvest" in haystack:
        return "Arvest"
    return "Needs Review"


def infer_month(filename: str, text: str) -> str:
    haystack = f"{filename}\n{text[:3000]}"
    for year in (2024, 2025):
        for month in range(1, 13):
            full = calendar.month_name[month]
            abbr = calendar.month_abbr[month]
            if re.search(rf"\b(?:{full}|{abbr})\b[\s_\-.,]*{year}\b", haystack, re.I):
                return f"{abbr} {year}"
            if re.search(rf"\b{year}[\s_\-]{month:02d}\b|\b{month:02d}[\s_\-]{year}\b", haystack):
                return f"{abbr} {year}"
    match = PERIOD_RE.search(haystack)
    if match:
        end = parse_statement_date(match.group(2), "Needs Review")
        if end:
            return f"{calendar.month_abbr[end.month]} {end.year}"
    return "Needs Review"


def extract_account(text: str) -> str:
    match = ACCOUNT_RE.search(text)
    return re.sub(r"\s+", " ", match.group(1)).strip()[-12:] if match else "Needs Review"


def extract_period(text: str) -> str:
    match = PERIOD_RE.search(text)
    return f"{match.group(1)} - {match.group(2)}" if match else "Needs Review"


def clean_description(description: str) -> str:
    return re.sub(r"\s+", " ", description).strip(" -")


def merchant_from_description(description: str) -> str:
    merchant = re.sub(r"\b(POS|DEBIT|CARD|ACH|WEB|ONLINE|PURCHASE|PMT|PAYMENT)\b", " ", description, flags=re.I)
    return clean_description(merchant).strip(" -*") or "Needs Review"


def categorize(description: str, credit: Decimal, debit: Decimal) -> tuple[str, str, str, str]:
    for category, pattern, note in CATEGORY_RULES:
        if re.search(pattern, description, re.I):
            subcategory = "Veterinary" if category == "Medical / Health" and re.search(r"animal\s+hospital|veterinar|vet\b", description, re.I) else ""
            return category, subcategory, "High", note
    if credit > 0 and debit == 0:
        return "Income / Deposits", "", "Medium", "credit amount with no stronger merchant keyword"
    return "Uncategorized / Review", "", "Low", "Needs Review: no responsible category keyword found"


def parse_transaction_line(line: str, bank: str, account: str, month: str, source_pdf: str, page: int) -> dict[str, object] | None:
    line = clean_description(line)
    match = DATE_RE.match(line)
    if not match or not MONEY_RE.search(line):
        return None
    if SUMMARY_HINT_RE.search(line) and len(MONEY_RE.findall(line)) <= 2:
        return None
    rest = match.group("rest")
    money_matches = list(MONEY_RE.finditer(rest))
    if not money_matches:
        return None
    description = clean_description(rest[: money_matches[0].start()]) or clean_description(rest)
    amount = parse_money(money_matches[0].group(0))
    balance = parse_money(money_matches[-1].group(0)) if len(money_matches) >= 2 else None
    credit_hint = re.search(CATEGORY_RULES[7][1], description, re.I)
    if amount < 0:
        credit, debit = Decimal("0.00"), abs(amount)
    elif credit_hint:
        credit, debit = amount, Decimal("0.00")
    else:
        credit, debit = Decimal("0.00"), amount
    category, subcategory, confidence, note = categorize(description, credit, debit)
    return {
        "Bank": bank, "Account": account, "Statement Month": month,
        "Posted Date": normalize_date(match.group("date"), month),
        "Transaction Date": normalize_date(match.group("date"), month),
        "Description": description, "Merchant / Payee": merchant_from_description(description),
        "Category": category, "Subcategory": subcategory,
        "Credit": float(credit) if credit else "", "Debit": float(debit) if debit else "",
        "Net": float(credit - debit), "Balance": float(balance) if balance is not None else "",
        "Source PDF": source_pdf, "Source Page": page, "Confidence": confidence, "Notes": note,
    }


def parse_pdf(pdf_path: Path) -> tuple[list[dict[str, object]], dict[str, object], list[PageText]]:
    pages, method = extract_pdf_text(pdf_path)
    all_text = "\n".join(page.text for page in pages)
    bank, account, month, period = infer_bank(pdf_path.name, all_text), extract_account(all_text), infer_month(pdf_path.name, all_text), extract_period(all_text)
    transactions: list[dict[str, object]] = []
    for page in pages:
        for raw_line in page.text.splitlines():
            row = parse_transaction_line(raw_line, bank, account, month, pdf_path.name, page.page)
            if row:
                transactions.append(row)
    status = "Extracted" if transactions else ("Needs Review" if pages else "Needs OCR/Manual Review")
    source = {"Bank": bank, "Account": account, "Statement Month": month, "Statement Period": period, "PDF Filename": pdf_path.name, "Pages": len(pages), "Extraction Status": status, "Rows Extracted": len(transactions), "Notes": method if transactions else f"{method}; no transaction rows parsed"}
    return transactions, source, pages


def save_csv(path: Path, rows: Sequence[dict[str, object]], columns: Sequence[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def build_summary(master_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for month in MONTHS:
        for bank in ("Arvest", "Navy Federal"):
            if bank == "Navy Federal" and (statement_sort_key(month) < statement_sort_key("Feb 2025") or statement_sort_key(month) > statement_sort_key("Oct 2025")):
                continue
            subset = [r for r in master_rows if r.get("Statement Month") == month and r.get("Bank") == bank]
            row: dict[str, object] = {"Month": month, "Bank": bank}
            for category in CATEGORIES:
                row[category] = round(sum(float(r.get("Debit") or 0) for r in subset if r.get("Category") == category), 2)
            row["Total Debits"] = round(sum(float(r.get("Debit") or 0) for r in subset), 2)
            row["Total Credits"] = round(sum(float(r.get("Credit") or 0) for r in subset), 2)
            row["Net"] = round(float(row["Total Credits"]) - float(row["Total Debits"]), 2)
            rows.append(row)
    return rows


def col_letter(index: int) -> str:
    out = ""
    while index:
        index, rem = divmod(index - 1, 26)
        out = chr(65 + rem) + out
    return out


def sheet_xml(rows: Sequence[Sequence[object]]) -> str:
    xml_rows = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{col_letter(c_idx)}{r_idx}"
            if isinstance(value, (int, float)) and value != "":
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(str(value or ""))}</t></is></c>')
        xml_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(xml_rows) + '</sheetData></worksheet>'


def safe_sheet_name(name: str, used: set[str]) -> str:
    cleaned = re.sub(r"[\\/*?:\[\]]", "-", name)[:31] or "Sheet"
    candidate, counter = cleaned, 2
    while candidate in used:
        suffix = f" {counter}"
        candidate = f"{cleaned[:31-len(suffix)]}{suffix}"
        counter += 1
    used.add(candidate)
    return candidate


def write_xlsx(path: Path, sheets: list[tuple[str, Sequence[Sequence[object]]]]) -> None:
    used: set[str] = set()
    names = [safe_sheet_name(name, used) for name, _ in sheets]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>')
        zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        workbook_sheets = ''.join(f'<sheet name="{html.escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, name in enumerate(names, start=1))
        zf.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{workbook_sheets}</sheets></workbook>')
        rels = ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1))
        zf.writestr("xl/_rels/workbook.xml.rels", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{rels}</Relationships>')
        for i, (_, rows) in enumerate(sheets, start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


def readme_rows() -> list[list[object]]:
    return [
        ["Keith Household Payment Records - Court Ledger"], [""],
        ["Purpose", "Court-usable household payment ledger for Keith built from bank statement PDFs."],
        ["Source PDF set", "Arvest statements Dec 2024-Nov 2025 and Navy Federal statements Feb 2025-Oct 2025, either as PDFs or ZIP archives containing PDFs."],
        ["ZIP handling", "ZIP archives are indexed, PDF members are extracted into the PDF working folder, and extracted PDFs are then processed like direct source PDFs."],
        ["Traceability", "Every parsed transaction includes bank, statement month, source PDF filename, and source page."],
        ["Categorization", "Merchant/description text is matched to requester-provided category rules; uncertain entries are Uncategorized / Review."],
        ["Audit rule", "Do not invent merchant names or infer item-level details not visible in statement text."],
        [""], ["Categories"], *[[category] for category in CATEGORIES],
    ]


def monthly_sheet_rows(rows: Sequence[dict[str, object]]) -> list[list[object]]:
    columns = ["Posted Date", "Transaction Date", "Description", "Merchant / Payee", "Category", "Subcategory", "Credit", "Debit", "Net", "Balance", "Source PDF", "Source Page", "Confidence", "Notes"]
    out: list[list[object]] = []
    for category in CATEGORIES:
        out.append([category])
        out.append(columns)
        for row in rows:
            if row.get("Category") == category:
                out.append([row.get(col, "") for col in columns])
        out.append([])
    return out


def write_outputs(master_rows: list[dict[str, object]], source_rows: list[dict[str, object]], summary_rows: list[dict[str, object]], zip_rows: list[dict[str, object]]) -> None:
    save_csv(MASTER_CSV, master_rows, MASTER_COLUMNS)
    save_csv(SUMMARY_CSV, summary_rows, SUMMARY_COLUMNS)
    save_csv(SOURCE_INDEX_CSV, source_rows, SOURCE_COLUMNS)
    save_csv(ZIP_INDEX_CSV, zip_rows, ZIP_COLUMNS)
    sheets: list[tuple[str, Sequence[Sequence[object]]]] = [
        ("README / Instructions", readme_rows()),
        ("PDF Source Index", [SOURCE_COLUMNS] + [[row.get(col, "") for col in SOURCE_COLUMNS] for row in source_rows]),
        ("ZIP Extraction Index", [ZIP_COLUMNS] + [[row.get(col, "") for col in ZIP_COLUMNS] for row in zip_rows]),
        ("Master Transactions", [MASTER_COLUMNS] + [[row.get(col, "") for col in MASTER_COLUMNS] for row in master_rows]),
        ("Monthly Summary", [SUMMARY_COLUMNS] + [[row.get(col, "") for col in SUMMARY_COLUMNS] for row in summary_rows]),
    ]
    for month in MONTHS:
        for bank in ("Arvest", "Navy Federal"):
            if bank == "Navy Federal" and (statement_sort_key(month) < statement_sort_key("Feb 2025") or statement_sort_key(month) > statement_sort_key("Oct 2025")):
                continue
            label = "Navy" if bank == "Navy Federal" else bank
            subset = [r for r in master_rows if r.get("Statement Month") == month and r.get("Bank") == bank]
            sheets.append((f"{label} {month}", monthly_sheet_rows(subset)))
    write_xlsx(OUTPUT_XLSX, sheets)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Keith court evidence ledger from bank statement PDFs or ZIP archives of PDFs.")
    parser.add_argument("--pdf-dir", type=Path, default=DEFAULT_PDF_DIR, help="Directory containing source PDF statements.")
    parser.add_argument("--zip-dir", action="append", type=Path, default=[], help="Directory to scan recursively for ZIP files containing statement PDFs. Can be passed more than once.")
    args = parser.parse_args()
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    args.pdf_dir.mkdir(parents=True, exist_ok=True)
    EXTRACTED_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    zip_dirs = args.zip_dir or [WORK_DIR]
    zip_files = discover_zip_files(zip_dirs)
    extracted_from_zips = extract_pdf_zips(zip_files, args.pdf_dir) if zip_files else []

    master_rows: list[dict[str, object]] = []
    source_rows: list[dict[str, object]] = []
    for pdf_path in sorted(args.pdf_dir.glob("*.pdf")):
        transactions, source, pages = parse_pdf(pdf_path)
        (EXTRACTED_TEXT_DIR / f"{pdf_path.stem}.txt").write_text("\n".join(f"--- SOURCE PAGE {p.page} ---\n{p.text}" for p in pages), encoding="utf-8")
        master_rows.extend(transactions)
        source_rows.append(source)
    master_rows.sort(key=lambda row: (statement_sort_key(str(row.get("Statement Month", ""))), str(row.get("Bank", "")), str(row.get("Posted Date", "")), str(row.get("Source PDF", "")), int(row.get("Source Page") or 0)))
    source_rows.sort(key=lambda row: (statement_sort_key(str(row.get("Statement Month", ""))), str(row.get("Bank", "")), str(row.get("PDF Filename", ""))))
    summary_rows = build_summary(master_rows)
    write_outputs(master_rows, source_rows, summary_rows, extracted_from_zips)

    review_pdfs = [str(row.get("PDF Filename")) for row in source_rows if row.get("Extraction Status") != "Extracted"]
    uncategorized = sum(1 for row in master_rows if row.get("Category") == "Uncategorized / Review")
    print("Keith Court Evidence Ledger build complete")
    print(f"ZIP archives found: {len(zip_files)}")
    extracted_pdf_count = sum(1 for row in extracted_from_zips if not str(row.get('Extracted PDF', '')).startswith(('Needs Review', 'Already present')))
    print(f"PDFs extracted from ZIP archives: {extracted_pdf_count}")
    print(f"PDFs processed: {len(source_rows)}")
    print(f"Transactions extracted: {len(master_rows)}")
    print(f"PDFs/pages needing manual review: {', '.join(review_pdfs) if review_pdfs else 'None recorded'}")
    print(f"Transactions categorized as Uncategorized / Review: {uncategorized}")
    print("Reconciliation warnings: statement-summary reconciliation requires statement-specific totals and manual review of source index notes.")
    print(f"Workbook: {OUTPUT_XLSX}")
    print(f"CSVs: {MASTER_CSV}, {SUMMARY_CSV}, {SOURCE_INDEX_CSV}, {ZIP_INDEX_CSV}")
    if not source_rows:
        print(f"No PDFs found in {args.pdf_dir}; place Keith's statement PDFs or ZIP archives in {WORK_DIR} and rerun.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
