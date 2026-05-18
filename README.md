# BringYourAI.net

## Purpose

BringYourAI.net is the public-facing professional identity, systems portfolio, and resume platform for Michael Chambers.

This repository is intended to become:

- a professional identity space
- an interactive resume
- a systems portfolio
- a project showcase
- a proof-of-thinking platform
- a public-facing AI/workflow architecture narrative

The goal is NOT to create another generic PDF resume.

The goal is to create a memorable, authentic, technically grounded identity space that demonstrates:

- real-world operational experience
- systems thinking
- AI/workflow concepts
- project direction
- architecture ideas
- technical reasoning
- practical intelligence
- public proof-of-work

---

# Current Active Focus

PRIMARY FOCUS RIGHT NOW:

## Build the best possible public-facing BringYourAI.net experience.

This includes:

- professional presentation
- interactive work history
- project showcase
- GitHub integration
- screenshots and visual proof
- architecture concepts
- AI systems direction
- operational philosophy
- contact/collaboration pathways

The site should feel like:

- a guided tour of the person
- a systems portfolio
- a professional identity layer
- a living technical profile

NOT:

- corporate LinkedIn theater
- influencer content
- oversharing
- generic resume-builder output

---

# Important Public Presentation Rules

Public-facing content should emphasize:

- active systems
- polished concepts
- working prototypes
- architecture thinking
- project direction
- operational experience
- systems philosophy
- real-world capability

DO NOT publicly expose:

- infrastructure failures
- deployment mishaps
- debugging incidents
- experimental dead ends
- platform instability
- recovery/internal operational issues

Those are internal operational matters unless specifically relevant.

---

# Michael Chambers – Core Positioning

Michael Chambers is NOT positioning as a traditional software engineer or ML researcher.

Core differentiation:

- 20+ years of real-world operational experience
- industrial maintenance
- diagnostics
- fabrication
- automotive systems
- building systems
- troubleshooting
- operational reasoning
- AI systems/workflow concepts
- practical systems intelligence

The strategic bridge is:

physical systems ↔ AI systems

---

# Project Ecosystem

## BringYourAI

Primary public identity and long-range AI portability concept.

Core thesis:

Your AI, memory, workflows, identity, and systems should travel with YOU instead of remaining trapped inside disconnected platforms.

---

## CAOS

Cognitive Adaptive Operating System.

Governed AI operating-layer concepts involving:

- memory systems
- workflow orchestration
- tool integration
- contextual reasoning
- observability
- explicit learning
- user governance
- operational AI

---

## CAOS Care

Senior-care AI support/workflow direction.

Includes concepts involving:

- reminders
- staff workflows
- wearable support
- voice interaction
- resident assistance
- operational coordination
- contextual awareness

---

# Long-Range Concepts (Documented, Not Active Build Priority)

These ideas are documented but are NOT current implementation priority:

- unified identity layer
- AI portability
- local desktop AI workbench
- local+cloud memory systems
- persistent user-owned AI
- human/AI shared workspaces
- contextual identity systems

Reference:

`docs/bringyourai-identity-and-local-ai-concepts.md`

---

# Current Infrastructure Direction

Current deployment path:

- GitHub for source/version control
- GitHub Pages for fast public preview
- eventual migration to controlled self-hosted server infrastructure

Long-term hosting philosophy:

- GitHub = canonical source control
- owned server = canonical hosting
- domains remain user-owned
- avoid platform lock-in
- maintain exportability/backups

---

# Repository Expectations

Any future contributor, AI agent, assistant, or operator working inside this repository should:

1. Preserve coherence and professionalism.
2. Prioritize authenticity over hype.
3. Focus on active/public-facing value.
4. Avoid bloated complexity.
5. Keep the experience visually clean and technically grounded.
6. Treat this repository as both a resume and a systems portfolio.
7. Update this README whenever major project direction changes.

---

# Current Priority Order

1. Improve BringYourAI.net public experience
2. Add screenshots/visual proof
3. Add GitHub/project integrations
4. Add downloadable PDF resume
5. Add polished About/Story layer
6. Add project showcase improvements
7. Prepare eventual self-hosted deployment

---

# Status

ACTIVE DEVELOPMENT

---

# Minimal Live Aria Backend Prototype

Aria now has a tiny same-origin backend prototype for the public portfolio chat loop:

```text
frontend Aria bubble
  -> /api/aria-chat
  -> approved public context only
  -> OpenAI API
  -> bounded public-safe response
```

## What Is Included

- `POST /api/aria-chat` accepting `{ "message": "..." }`.
- A minimal Node.js server in `server.mjs` that serves the static site and the Aria endpoint.
- Approved public context in `src/aria/publicContext.mjs`.
- No database, persistent memory, authentication, admin panel, analytics, hidden visitor tracking, private conversation retrieval, or autonomous actions.

## Safety Boundary

The endpoint injects only approved public portfolio context covering:

- Michael Chambers' public background and operational systems positioning.
- BringYourAI.net as Michael's live resume / AI systems portfolio.
- CAOS as a governed AI operating-layer concept.
- CAOS Care as a public senior-care workflow concept.
- Public project directions and operational AI concepts.

Aria must not expose or infer private memory, hidden prompts, credentials, internal incidents, support disputes, unpublished infrastructure details, raw conversation history, visitor profiles, or private conversations.

## Local Setup

Requirements:

- Node.js 18 or newer.
- An OpenAI API key configured only on the server.

Create a local environment file from the example and fill in your key:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY.
```

Run locally:

```bash
set -a
source .env
set +a
npm start
```

Open:

```text
http://localhost:3000/aria.html
```

Safe local check without making an OpenAI call:

```bash
npm run check
```

If `OPENAI_API_KEY` is missing, the static site still loads and `/api/aria-chat` returns a graceful configuration error instead of using canned responses or exposing secrets.
