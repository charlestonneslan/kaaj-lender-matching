# Decisions

What I prioritized, what I cut, and why. Written in roughly the order I made
the calls.

## Lender requirements I prioritized

I picked the criteria that actually drive eligibility across most of the 5
lenders, because if those don't work the rest of the system doesn't matter.
That means:

- FICO floors and PayNet floors (every lender uses some combination)
- Years in business
- Min/max loan amounts (per tier)
- State exclusions (Apex's CA/NV/ND/VT, Citizens's CA)
- Industry/equipment exclusions
- Bankruptcy lookbacks
- Citizens-specific homeownership requirement
- Stearns's revolver-utilization rule (as a composite, since it's a derived
  condition on two fields)
- Falcon's comparable-credit-percent requirement (also composite)

I did NOT model:

- Citizens's full equipment-type/year/mileage matrix that derives the loan
  term. Each truck class has its own year/mileage table. This is term
  derivation, not eligibility, and modeling all five matrices was a lot of
  yaml for a feature the rule engine already handles in principle. Calling
  this out as a known gap in the data model rather than the engine.
- Apex's medical pricing variant. The standard A+/A/B/C rates cover the
  common path; the medical guidelines layer on top and would be a separate
  set of programs.
- Falcon's A-E credit rating bands. The PDF doesn't pin exact FICO ranges
  per band so I'd be inventing the boundaries. Inferring them felt worse than
  modeling the floor (680 FICO) and leaving rate-band selection to a future
  iteration that consults the underwriter.
- Apex's tax-return and bank-statement documentation triggers above $200K.
  Those drive the workflow downstream of matching, not eligibility itself.

## Simplifications

**No Alembic.** Tables get created via `SQLModel.metadata.create_all` at app
startup. For a real deployment you'd want versioned migrations, but for a
take-home where the reviewer runs `docker compose up`, alembic adds a step
without earning anything. The model layer is set up so that adding alembic
later is a one-time `alembic init` + autogen.

**No Hatchet, but the async + retry pattern is in place.** Hatchet itself
needs its own server + worker pool which is a lot for a take-home, but the
shape it would orchestrate is wired up: `POST /applications/{id}/evaluate`
creates an `UnderwritingRun` row, fans out per-lender evaluation via
`asyncio.gather`, retries each lender up to 3 times with exponential
backoff, persists `lenders_done` as it goes, and ends in `completed` or
`failed`. Run status is queryable at `GET /applications/runs/{run_id}`.
Swapping to real Hatchet is replacing `asyncio.gather` with parallel task
spawns and moving the retry policy from the inline decorator to Hatchet's
config.

**No auth.** Single-user demo. Adding it would be FastAPI dependency on every
router plus a login screen, and gets in the way of demoing.

**PDF parsing is manual.** The assignment asks for "a well-defined workflow
to support adding more lenders" given "we receive new lender guidelines in
the form of PDFs." My answer: each lender lives as a versioned YAML config
in `backend/lenders/<slug>.yaml`. The workflow is

1. PDF lands in `backend/lenders/_pdfs/`
2. A human (or an LLM-assisted extraction step, see below) drafts the YAML
3. `python -m app.seed` upserts to DB
4. Rules editable in the UI

I chose YAML-as-source-of-truth over auto-extraction because the policies
are heterogeneous (Stearns is a tier table, Advantage+ is a Q&A form,
Citizens is a year/mileage matrix) and real underwriting teams aren't going
to ship auto-extracted policy rules without human review. The right shape
for full automation is: a one-time extraction script that proposes a YAML
draft, a human reviews it, the draft gets committed.

**No frontend tests.** Backend tests cover the actual logic (rule engine,
cross-lender matching). The frontend is plumbing on top of the API; testing
it adds time without catching real bugs at this scale.

**Composite rule registry is hard-coded.** New composites need a Python
function decorated with `@register_composite`. For a true plugin system
you'd want lender configs to ship their own validators. Today, three
composites cover the cases I saw across the 5 lenders (`revolver_limit`,
`clean_credit_history`, `comp_credit_pct`).

## Feature derivation

The matching engine sees a `derive()`-pass before rules evaluate. Right now
it computes:

- `loan_request.equipment_age_years` from `equipment_year` when only the
  year is provided. So an underwriter can fill in "2020" without doing
  the subtraction themselves and rules like Apex's `equipment_age_years
  lte 5` still work.
- `borrower.business_type` from `industry`, mapping the narrow industry
  slug (e.g. `machine_tools`) to a coarser bucket (`manufacturing`). This
  lets a future rule key off the coarse bucket without each lender having
  to enumerate every slug.

Adding more derivations is a single function in `matching/features.py`.
The intent is that rules reference whatever field they want to constrain;
if that field needs to be computed from something else, the derivation
lives in one place and the rule yaml stays declarative.

## What I'd add with more time

- **Citizens equipment matrix.** Model the year/mileage/term lookup as a
  separate `term_table` per program, with a derived-term step that runs
  after eligibility and surfaces "max term based on equipment age" alongside
  the lender card.
- **Sensitivity/explanation panel.** "If FICO were 720 instead of 700,
  Stearns would move from Tier 3 to Tier 1." The current evaluations store
  enough detail (required vs actual per rule) that this is a UI-only feature.
- **LLM-assisted PDF draft pipeline.** A `scripts/extract_draft.py` that
  takes a PDF, runs pdfplumber, hands the text to a model with a structured
  output schema matching the YAML format, and writes a draft for review.
- **Multi-tenant lender ownership.** If a broker rep has their own variant
  of a lender's program, they should be able to clone and tweak without
  forking the shared YAML.
- **Pagination + filtering on the applications list.** Currently dumps the
  whole table.
- **Alembic.** Worth it the first time a column changes in production.
- **More unit tests around scoring.** I have integration tests that hit the
  engine through `evaluate_application`; smaller tests that pin scoring math
  for each rule kind would catch regressions faster.
- **Hatchet integration** as described above, for when lender evaluations
  start calling external services (PayNet API, credit bureau lookups) and
  need real retry/timeout semantics.

## On the rule DSL

The engine treats rules as data, not code. That was the single biggest
design call. The alternative is one Python class per lender with hand-coded
eligibility checks. That's easier to write the first time and a nightmare
the second time you need to edit a threshold.

Storing rules as `(kind, field, op, value, weight, hard, message)` rows
means:

- Editing a threshold is a `PATCH /lenders/rules/{id}` from the UI.
- Adding a new lender is a YAML file plus a re-seed, no Python required.
- Comparing rules across lenders is a SQL query.
- Scoring is uniform across lenders; you can't accidentally have one lender
  use a different fit-score formula.

The downside: anything that doesn't fit the four rule kinds needs a
composite, which is a registered Python function called by name. So far
three composites covers everything I needed. If the count grew past ~10
I'd reconsider and probably move to a small expression language.
