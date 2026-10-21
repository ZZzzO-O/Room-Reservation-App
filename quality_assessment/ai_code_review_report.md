# Quality Assessment Report: Algorithmic Static Analysis vs. LLM Code Review
**Course:** SEN-201 Software Engineering Processes  
**Team:** Vibranium (Su Pyae Pyae Aung, Thiri Htet Thwe, Jan, Zin Zin Zaw Win)  
**Date:** October 21, 2026  
**Target Codebase:** CMKL Room Reservation Web Application (Backend Services & API Gateway)  
**Primary Review Target:** `ApiGateway/api_gateway.py` & Service Modules  

---

## 1. Executive Summary

As part of the SEN-201 Quality Assessment assignment, Team Vibranium conducted a two-phase code quality evaluation:
1. **Algorithmic Static Analysis** using **Pylint (v4.1.3)** on all project source code, comparing pre-fix (`pylint_run1_output.txt`) to post-fix (`pylint_run2_output.txt`).
2. **AI-Powered Code Review Evaluation (Extra Challenge, +2 points)** using an LLM (Gemini 2.5 / GPT-4o architecture) executed twice independently on identical, unmodified code to evaluate **determinism vs. non-determinism**, semantic depth, and comparative strengths against algorithmic tools.

---

## 2. Phase 1: Algorithmic Static Analysis (Pylint)

### 2.1 Initial Run (`pylint_run1_output.txt`)
- **Initial Rating:** `0.00 / 10.00` (81 raw lines of diagnostics, 32 distinct code issues).
- **Flagged Problem Categories:**
  - `C0114 (missing-module-docstring)`: Missing top-level docstrings across all modules.
  - `C0413 (wrong-import-position)`: Dynamic `sys.path` inserts preceding module imports without lint suppression.
  - `C0411 (wrong-import-order)`: Sibling imports ordered without strict PEP 8 grouping.
  - `C0415 (import-outside-toplevel)`: Late circular-import resolution in `_db()` and unit test mocks.
  - `W0108 (unnecessary-lambda)`: Dataclass default factory invoking lambda rather than direct callable (`utc_now`).
  - `R0902 (too-many-instance-attributes)`: Domain dataclass `Reservation` possessing 9 attributes against the default threshold of 7.
  - `R0903 (too-few-public-methods)`: Single-method Protocol classes (`RoomCapacityProvider`, `RoomCapacityLookup`).
  - `R0904 (too-many-public-methods)`: Comprehensive unit test suite with 23 assertions.
  - `C0103 (invalid-name)`: PascalCase package directory names (`RoomService`, `AuthService`, `ApiGateway`, `Database`, `Reservation`).

### 2.2 Refactoring & Post-Fix Run (`pylint_run2_output.txt`)
- **Action Taken:**
  - Added descriptive module-level docstrings conforming to PEP 257.
  - Added package `__init__.py` files with appropriate re-exports and naming annotations.
  - Standardized import locations, eliminated unnecessary lambdas, and replaced redundant inner imports with top-level imports.
  - Annotated legitimate architectural constructs (single-method protocols and domain dataclasses) with scoped `# pylint: disable=...` directives.
- **Final Rating:** **`10.00 / 10.00`** (+10.00 improvement, 0 issues remaining).
- **Test Integrity:** 100% of the 119 unit tests across RoomService, AuthService, Database, Reservation, and ApiGateway passed cleanly with 0 regressions.

---

## 3. Phase 2: LLM Code Review & Non-Determinism Analysis

To evaluate the capabilities and consistency of Large Language Model static code review, we submitted the core orchestration module (`ApiGateway/api_gateway.py`) to an LLM code reviewer twice under identical prompts and zero codebase modifications between runs.

```text
Prompt:
"Act as a Principal Software Engineer. Conduct a rigorous static code review of 
this Python file (ApiGateway/api_gateway.py). Identify security issues, concurrency 
or transaction bugs, architectural risks, and style deviations. Categorize by severity."
```

### 3.1 LLM Review Run 1 Summary
The first review run highlighted the following findings:
1. **Critical/High — SQLite Concurrency & Multi-Step Race Condition:** In `POST /api/reservations`, the service checks room conflict in memory/database and then persists the reservation in a separate step. Under concurrent requests, two requests for the same room could pass the check simultaneously before either writes to SQLite.
2. **Medium — Transaction Rollback Granularity:** If a multi-step operation (such as creating a reservation and writing an audit log) fails midway, SQLite does not automatically rollback without an explicit `with conn:` context manager.
3. **Medium — Token Expiration Timezone Naivety:** `auth_service.utc_now()` strips timezone information to create naive datetimes; if system local time drifts from UTC, comparisons between `expires_at` and `datetime.now()` could prematurely invalidate or prolong sessions.
4. **Low — CORS Wildcard Scope:** `CORS(app)` without restrictive origin filters permits cross-origin requests from any domain in production.

### 3.2 LLM Review Run 2 Summary
The second review run on the identical source code yielded:
1. **High — Check-Then-Act Race Condition in Room Reservation:** Identified the identical concurrency hazard where room availability lookup and insertion lack an atomic database lock or unique constraint on `(room_id, date, time_slot)`.
2. **High — Unhandled JSON Parsing Exceptions:** Route handlers relying on `request.get_json(silent=True)` safely handle malformed JSON syntax, but missing required dictionary keys (e.g. `competency`, `room_id`) could raise `KeyError` unless guarded by defaults.
3. **Medium — Hardcoded Test User Credentials in Memory:** Noted that test accounts (`seed_users.py`) remain accessible in memory unless explicitly separated between `testing` and `production` configuration profiles.
4. **Low — Inconsistent Error Response Payloads:** While most routes return `{"error": "message"}`, some helper routines return serialized exception strings directly without an error code mapping.

---

## 4. Determinism vs. Non-Determinism Comparison

| Dimension | LLM Review Run 1 | LLM Review Run 2 | Pylint (Algorithmic) |
|---|---|---|---|
| **Deterministic?** | **No** (Output phrasing and item ranking varied) | **No** (Different secondary priorities) | **Yes (100% Deterministic)** |
| **Primary High Severity Issue** | Check-then-act reservation race condition | Check-then-act reservation race condition | Missed entirely (semantic logic blind) |
| **Secondary Findings** | SQLite transaction rollback, timezone naive dates | JSON payload missing keys, hardcoded seed profiles | Missed entirely (semantic logic blind) |
| **Formatting / PEP 8 Issues** | Mentioned high-level docstrings briefly | Mentioned high-level docstrings briefly | Identified exact line numbers, AST rules, missing docstrings |
| **Scoring / Reproducibility** | Qualitative severity matrix | Qualitative severity matrix | Numerical score (0.00/10 -> 10.00/10) |

### 4.1 Observations on LLM Non-Determinism
1. **Semantic Convergence:** Both LLM runs accurately identified the most significant software engineering vulnerability in the code: the **check-then-act race condition** between checking room availability and committing the reservation to SQLite.
2. **Probabilistic Divergence:** Because LLMs sample tokens based on temperature and probabilistic distributions, Run 1 focused on **database transaction boundaries and timezone handling**, whereas Run 2 shifted focus toward **payload schema validation and configuration separation**.
3. **Actionability:** An LLM does not provide a reproducible pass/fail gate for CI/CD pipelines because a pull request could pass on one invocation and fail on another.

---

## 5. Comparative Analysis: Algorithmic Tools vs. LLMs

### 5.1 What the LLM Found that Pylint Missed
- **Business Logic & Semantic Bugs:** Pylint is completely unaware of application semantics. It cannot discern that checking room availability followed by an insert creates a race condition in a multi-user web application.
- **Database Transaction Boundaries:** Pylint cannot evaluate whether database commits should be wrapped in rollback blocks or if multi-table operations maintain ACID properties.
- **Security & Threat Modeling:** The LLM flagged permissive CORS headers, hardcoded test seeds in staging environments, and credential exposure vectors.

### 5.2 What Pylint Found that the LLM Missed
- **Exhaustive Structural & Syntactic Rule Enforcement:** Pylint systematically verified every single line against 400+ PEP 8 and AST rules. The LLM only reviewed prominent patterns and skipped minor import ordering, missing package `__init__.py` files, and unused lambda syntax.
- **Exact Line-by-Line Quantifiable Metrics:** Pylint generated precise line numbers, standardized warning IDs (e.g., `C0114`, `R0903`), and a concrete formula-based score (`10.00/10`).
- **Zero Hallucination:** Pylint never invents phantom APIs or speculates about variables that do not exist in the file.

---

## 6. Conclusion & Recommendations

For modern professional software development:
1. **Algorithmic static analysis (Pylint / Flake8)** is indispensable as a **deterministic CI/CD gatekeeper**. It guarantees consistent syntax, enforces style guides, prevents unused variables, and provides objective quality metrics before code can be merged.
2. **LLM-based code review** acts as an **expert senior engineer pair-reviewer**. It excels at detecting complex architectural flaws, business logic oversights, concurrency hazards, and security vulnerabilities that AST parsers are fundamentally incapable of recognizing.
3. **The Optimal Strategy:** Combine both tools. Use Pylint in automated Git commit hooks and CI pipelines, and use LLM reviews during pull request discussions to review logic, security, and edge-case behavior.
