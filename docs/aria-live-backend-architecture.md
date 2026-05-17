# Aria Live Backend Architecture

## Purpose

This document defines the public-safe architecture for a future live Aria backend on BringYourAI.net.

Aria is intended to become a callable AI guide for Michael Chambers' public resume, systems portfolio, CAOS concepts, CAOS Care concepts, and operational AI work. The near-term goal is to prepare the design boundary only. This document does not authorize production backend implementation, API keys, database code, credential storage, or visitor tracking.

BringYourAI.net should remain a live resume and AI systems portfolio first. Aria should support that mission by helping visitors understand Michael's public work, not by becoming an unrestricted chatbot or hidden tracking system.

---

## Current Implementation Boundary

The current site may present Aria as a public-facing concept/demo interface. A later implementation may connect that interface to a governed backend, but only after explicit authorization.

This architecture intentionally excludes:

- production backend code
- model provider API keys
- database schemas or migrations
- analytics beacons that identify visitors without consent
- hidden tracking or private profiling
- private memory exposure
- unrestricted tool execution

---

## Target Safe Flow

The approved live path is:

```text
frontend Aria bubble
  -> backend API
  -> approved public resume/project context
  -> LLM
  -> bounded response
  -> frontend Aria bubble
```

### 1. Frontend Aria Bubble

The frontend should collect only the user's message and any explicit consent choices shown in the interface.

The frontend should not:

- embed model API keys
- call an LLM provider directly from the browser
- store visitor identity without consent
- silently fingerprint visitors
- scrape private browser, device, account, or page data

The frontend may:

- display the consent state
- ask whether the visitor wants to share name, email, company, and interest summary
- show that Aria is limited to public BringYourAI context
- provide a contact path if the visitor wants follow-up

### 2. Backend API

The backend API should act as a policy and context gateway, not as a raw pass-through to a model.

Expected responsibilities:

- validate and rate-limit requests
- strip unexpected fields
- attach only approved public context
- enforce response boundaries
- block secrets, private memories, and unsafe disclosure
- optionally save visitor memory only when consent is present
- return a bounded answer to the browser

The backend should be the only server-side place where future model credentials are configured.

### 3. Approved Public Context Layer

Aria should answer from approved public material only. Public context may include:

- public resume and work-history summaries
- public project summaries on BringYourAI.net
- public CAOS concept descriptions
- public CAOS Care positioning
- operational AI systems themes
- public contact paths
- public GitHub/project references selected by Michael
- curated architecture concept documents intended for publication

The public context layer should be curated and versioned so that Aria can be updated without exposing raw private notes.

### 4. LLM Call

The LLM should receive:

- a system/developer instruction containing Aria's safety boundary
- the visitor's current message
- optional short conversation context from the current session
- approved public resume/project context
- optional consent-based visitor memory summary, if the visitor has opted in

The LLM should not receive:

- raw server logs
- credentials or environment variables
- private emails
- private conversations
- private incidents
- hidden visitor profiles
- unreviewed personal history
- sensitive operational details

### 5. Bounded Response

Aria's response should be concise, useful, and grounded in approved context.

A bounded response should:

- answer using public information
- acknowledge uncertainty when context is missing
- suggest a contact path for detailed follow-up
- refuse requests for private information
- avoid claiming production capabilities that are not live
- avoid medical, legal, or financial advice beyond general context

---

## Public Safety Boundary

Aria may discuss:

- Michael Chambers' public resume and professional positioning
- public projects and systems concepts on BringYourAI.net
- BringYourAI as a live resume / AI systems portfolio
- CAOS as a governed AI operating-layer concept
- CAOS Care as a human-supervised assistive workflow concept
- operational AI, maintenance workflows, diagnostics, local/cloud AI, identity layers, and public architecture themes
- how to contact Michael or express interest in collaboration

Aria must not expose or infer:

- private memories
- private conversations
- credentials, tokens, or account identifiers
- internal incidents or recovery details
- partner-sensitive or employer-sensitive information
- resident, patient, staff, customer, or facility data
- sensitive personal history that Michael has not explicitly approved for public use
- hidden visitor profiles or unconsented visitor memory

If a visitor asks for information outside the public boundary, Aria should decline briefly and redirect to public-safe topics or contact paths.

---

## Visitor Memory and Lead Capture

Visitor memory is optional and consent-based. The default state is no persistent visitor memory.

A future implementation may allow a visitor to opt in to being remembered as a lead or returning visitor. When consent is absent, the backend may use only ephemeral session context needed to answer the current conversation and should not persist identity or interest data.

For the detailed visitor memory shape, see [Aria Visitor Memory Model](./aria-visitor-memory-model.md).

### Consent Rules

A consent-based memory flow should:

- ask clearly before saving visitor information
- separate chat usage from lead capture
- allow the visitor to continue using Aria without providing name, email, or company
- make name, email, and company optional
- summarize what will be saved before saving it
- avoid saving sensitive personal data unless explicitly relevant and approved
- provide a future path for deletion or correction when persistent storage exists

### No Secret Tracking

The system must not create hidden identity profiles from:

- IP address
- browser fingerprint
- device fingerprint
- hidden cookies
- third-party identity enrichment
- cross-site tracking
- inferred employer or personal identity

Basic security logs may exist in a future backend for abuse prevention, but they should not be treated as visitor memory or lead data.

---

## Admin / Owner Visibility

Michael should have a future owner/admin view where he can review consent-based visitor summaries and leads.

The owner view may show:

- visitor-provided name
- visitor-provided email
- visitor-provided company
- visitor-provided or Aria-summarized interest summary
- consent timestamp
- pages or topics discussed at a high level
- requested follow-up path
- conversation summary when the visitor has agreed to save it

The owner view must not show:

- secret tracking data presented as identity
- private visitor profiling
- model-inferred sensitive attributes
- unrelated security logs as lead history
- private system prompts or credentials

The owner view should make it clear which fields were explicitly provided by the visitor and which fields were summarized by Aria from the consented conversation.

---

## Suggested Future API Shape

This is a planning sketch, not an implementation requirement.

```text
POST /api/aria/chat
```

Possible request fields:

- `message`: visitor message
- `sessionId`: anonymous ephemeral session identifier
- `pageContext`: current public page or section identifier
- `memoryConsent`: whether the visitor has opted in to persistent memory
- `visitor`: optional visitor-provided name, email, company, and contact preference

Possible response fields:

- `answer`: bounded Aria response
- `safetyNotice`: optional refusal or boundary note
- `memoryPrompt`: optional prompt asking whether the visitor wants to save a summary
- `savedMemory`: whether consented visitor memory was saved

Implementation notes:

- Do not place provider keys in the frontend.
- Do not persist visitor identity unless `memoryConsent` is explicit.
- Do not include raw private data in model context.
- Keep the API narrow and auditable.

---

## Context Governance

Future public context should be organized so Aria can retrieve or inject only approved material.

Recommended context categories:

- `resume_public`: approved work-history and positioning summary
- `projects_public`: approved project descriptions and public links
- `caos_public`: public CAOS architecture concept language
- `caos_care_public`: public CAOS Care concept language
- `operational_ai_public`: approved operational AI themes
- `contact_public`: approved contact and collaboration paths

Context updates should be reviewable by Michael before they become available to Aria.

---

## Safety Checks for Later Implementation

Before any live backend is shipped, confirm:

- [ ] no API keys are present in frontend code
- [ ] no database writes occur without explicit consent
- [ ] no private documents are loaded into the public context layer
- [ ] Aria refuses private memory and credential requests
- [ ] consent text is visible before lead capture
- [ ] Michael can distinguish visitor-provided fields from AI summaries
- [ ] logs are separated from visitor memory
- [ ] rate limiting and abuse handling exist
- [ ] model responses are bounded by public context and contact paths

---

## Non-Goals

This architecture does not attempt to build:

- a full CRM
- a medical assistant
- an autonomous hiring agent
- a private-memory chatbot for all of Michael's life
- a hidden analytics platform
- a production CAOS runtime
- a database-backed lead system before explicit approval

The correct next step is to keep strengthening BringYourAI.net as a public resume and AI systems portfolio while preserving a clean path to a governed Aria backend later.
