# Aria Visitor Memory Model

## Purpose

This document defines the consent-based visitor memory and lead-capture model for a future live Aria backend.

The default rule is simple: no persistent visitor memory without consent.

This is a planning document only. It does not introduce backend code, database code, analytics code, API keys, or production storage.

---

## Memory Principles

Visitor memory should be:

- explicit: the visitor knows what is being saved
- optional: Aria remains usable without lead capture
- minimal: save only what helps Michael follow up or understand interest
- public-safe: do not collect sensitive personal history by default
- reviewable: Michael can later inspect consented summaries/leads
- correctable: a future system should support deletion or correction requests
- separated from security logs: abuse-prevention logs are not lead memory

Visitor memory must not be:

- hidden tracking
- browser fingerprinting
- private profiling
- inferred identity enrichment
- cross-site surveillance
- a store of private conversations without permission

---

## Consent States

### No Consent

When no consent is present:

- use only ephemeral session context needed for the current chat
- do not save visitor identity
- do not save interest summaries as leads
- do not associate pages/topics with a persistent visitor profile
- do not infer identity from IP, device, employer, or behavior

### Consent Requested

When Aria detects possible collaboration or follow-up interest, it may ask whether the visitor wants to save a short summary for Michael.

The prompt should explain:

- what will be saved
- that name, email, and company are optional
- that the visitor can keep chatting without saving
- that saved data is for Michael's later review and possible follow-up

### Consent Granted

When consent is explicit, Aria may save a minimal visitor memory record.

Consent should be captured with:

- clear affirmative action
- timestamp
- scope of what the visitor agreed to save
- optional contact details provided by the visitor

### Consent Withdrawn or Correction Requested

A future production system should provide a contact path for deletion or correction requests. Until such a system exists, the public UI should avoid implying that persistent storage is active.

---

## Minimal Visitor Memory Record

A future consented record may contain:

```text
visitorMemoryId: generated server-side identifier
consent:
  granted: true
  timestamp: ISO-8601 timestamp
  consentTextVersion: version shown to visitor
visitorProvided:
  name: optional string
  email: optional string
  company: optional string
  contactPreference: optional string
interest:
  summary: short visitor interest summary
  pagesDiscussed: list of public page identifiers
  topicsDiscussed: list of high-level topics
  requestedFollowUp: boolean
metadata:
  createdAt: ISO-8601 timestamp
  updatedAt: ISO-8601 timestamp
  source: BringYourAI.net Aria
```

The model should distinguish visitor-provided values from AI-generated summaries.

---

## Allowed Fields

Allowed with consent:

- visitor name, if provided
- visitor email, if provided
- visitor company, if provided
- contact preference, if provided
- short interest summary
- timestamp of consent and memory creation
- public pages discussed
- high-level topics discussed
- whether follow-up was requested

Examples of high-level topics:

- resume review
- operational AI
- CAOS
- CAOS Care
- local AI workbench
- consulting or collaboration
- hiring or recruiting
- project partnership

---

## Disallowed Fields

Do not save as visitor memory:

- IP-derived identity
- browser or device fingerprint
- hidden cookies used for identity
- inferred employer without visitor confirmation
- inferred sensitive traits
- political, religious, medical, financial, or family details unless the visitor explicitly asks to include them and there is a legitimate reason
- raw secrets, credentials, tokens, or account identifiers
- private conversations not approved for storage
- unrelated security logs

---

## Example Consent Language

A future UI may use language like:

> Would you like me to save a short summary of your interest for Michael to review later? You can optionally share your name, email, and company. If you decline, I will not save a visitor memory or lead summary.

Before saving, Aria should confirm a summary such as:

```text
I will save: your optional contact details, a short summary of what you are interested in, the public pages/topics we discussed, and the time you consented. I will not save hidden tracking data.
```

---

## Owner Review View

A future admin/owner view for Michael may show:

- consent timestamp
- visitor-provided contact details
- interest summary
- pages/topics discussed
- follow-up request status
- source as BringYourAI.net Aria

The admin view should label fields clearly:

- `provided by visitor`
- `summarized by Aria from consented chat`
- `system timestamp`

This reduces confusion and prevents AI summaries from being treated as verified claims.

---

## Retention Guidance

A later backend should define retention before launch.

Recommended default:

- keep consented leads only while they are useful for professional follow-up
- provide a path to delete or correct records
- avoid indefinite storage of stale lead summaries
- avoid retaining raw conversation transcripts unless specifically consented and useful

---

## Implementation Readiness Checklist

Before implementing persistent visitor memory, confirm:

- [ ] consent copy is approved
- [ ] visitor can decline without losing basic chat access
- [ ] name, email, and company are optional
- [ ] storage separates visitor-provided data from Aria summaries
- [ ] no hidden tracking identifiers are used as lead identity
- [ ] Michael has an owner review path
- [ ] deletion/correction path is documented
- [ ] raw private data is excluded from memory
- [ ] security logs are not displayed as lead memory
