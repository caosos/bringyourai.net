# Keith Court Evidence Financial Ledger Workflow

This repository includes a dedicated local workflow for building the workbook:

- Script: `scripts/build_keith_court_ledger.py`
- ZIP/PDF workspace: `/work/keith_court_evidence/`
- Source PDF folder: `/work/keith_court_evidence/pdfs/`
- Workbook output: `/work/keith_court_evidence/Keith_Household_Payment_Records_Court_Ledger.xlsx`
- CSV outputs:
  - `/work/keith_court_evidence/master_transactions.csv`
  - `/work/keith_court_evidence/monthly_summary.csv`
  - `/work/keith_court_evidence/source_index.csv`
  - `/work/keith_court_evidence/zip_extraction_index.csv`

The script preserves neutral audit language and source traceability. It does not invent merchant names or item-level details. If a transaction cannot be responsibly categorized from statement text, it is marked `Uncategorized / Review` with low confidence.

## Run

```bash
python3 scripts/build_keith_court_ledger.py
```

Place Keith's Arvest and Navy Federal ZIP files, or already-extracted PDF statements, in `/work/keith_court_evidence/` before running. The builder scans that workspace for ZIP archives, extracts PDF members into `/work/keith_court_evidence/pdfs/`, and then creates a month-first workbook with the required README, source index, ZIP extraction index, master transactions, monthly summary, and one sheet per month/account combination.

You can also point the builder at another ZIP location:

```bash
python3 scripts/build_keith_court_ledger.py --zip-dir /path/to/drive/export
```

## PDF extraction

The builder prefers deterministic text extraction. It tries the `pdftotext` command first, then optional Python libraries (`pdfplumber`, then `pypdf`). If no text can be extracted, the PDF is listed in the source index as needing OCR/manual review.
