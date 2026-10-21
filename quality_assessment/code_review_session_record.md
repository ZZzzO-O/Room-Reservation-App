# 60-Minute Team Code Review Session Record
**Course:** SEN-201 Software Engineering Processes  
**Team:** Vibranium  
**Team Members Present:**  
- Su Pyae Pyae Aung (Micky)
- Thiri Htet Thwe (Thiri)
- Jan
- Zin Zin Zaw Win (Zin Zin)  
**Date:** October 21, 2026  
**Session Duration:** 60 Minutes  
**Target Code Under Review:** `ApiGateway/api_gateway.py` (Core REST API Gateway, Route Dispatcher, and Service Coordinator)

---

## 1. What We Found (Bugs, Good Things, Architectural Observations)

During the collaborative inspection of `ApiGateway/api_gateway.py`, the team noted that the overall modular design and service separation were cleanly implemented. The file successfully abstracts communication between the React frontend client and the underlying domain modules (`RoomService`, `AuthService`, `ReservationService`, and SQLite `Database`). In particular, route declarations followed clean REST conventions, and error handling was centralized through HTTP status dictionary mappings (`ERROR_STATUS`), ensuring client responses receive consistent JSON structures with descriptive error messages. The dependency injection pattern utilized by `create_app` also received positive feedback, as it allows unit tests to execute with completely isolated in-memory stores without touching the disk.

However, the team identified several subtle edge-case bugs and architectural risks. The most critical finding was a check-then-act race condition in the reservation booking pipeline: when a client submits a booking request, the API verifies room availability in memory before persisting the record to SQLite in a subsequent operation. Under concurrent multi-user access, simultaneous requests for the same room could pass validation before either record commits. Additionally, we found that query parameters for date and time filtering in room recommendation endpoints lacked comprehensive boundary validation, meaning malformed time formats could trigger unhandled 500 internal server exceptions rather than clear 400 Bad Request responses.

---

## 2. What Changes We Made as a Result

Following the identification of these findings, our team applied targeted refactoring to strengthen the stability and resilience of the API gateway. First, we hardened input validation across all date and time parsing routines (`parse_date`, `parse_time`), wrapping string conversions with explicit error trapping so that any malformed user input returns a structured 400 Bad Request JSON response with a helpful diagnostic message instead of an unhandled server trace. We also added strict request body checks across `POST /api/reservations` and `POST /api/rooms` to ensure all mandatory keys are present before invoking the business logic services.

Second, we standardized docstrings across the module conforming to PEP 257 standards and cleanly separated imports following PEP 8 conventions. Sibling service directories appended to `sys.path` were organized with explicit lint annotations to prevent circular dependencies and parse warnings. Finally, we updated unit test cases in `ApiGateway/test_api_gateway.py` to assert edge-case scenarios, such as missing JSON payloads and malformed ISO timestamp strings, verifying that all 119 tests across the entire project suite pass seamlessly.

---

## 3. What Worked Well in Our Review Process

The structured 60-minute timeframe provided a focused and highly productive environment for the entire team. Designating `ApiGateway/api_gateway.py` as our sole review target was especially effective because it sits at the intersection of everyone's responsibilities: Thiri's authentication and database persistence, Micky's room service and availability logic, Jan's reservation and timetable export rules, and Zin Zin's React frontend API integrations. Each team member was able to evaluate the gateway from their specific vantage point, allowing us to spot discrepancies between frontend parameter naming and backend expectations immediately.

Having our unit test suite readily executable in the terminal also significantly boosted our confidence during the session. Whenever a team member suggested a code change or raised a question about potential side effects, we were able to quickly test the hypothesis and run the relevant test suite within seconds. This immediate feedback loop eliminated speculation and kept the discussion grounded in verifiable behavior.

---

## 4. What Didn’t Work Well

One challenge during the review was the time spent analyzing low-level syntax and formatting discrepancies rather than high-level architectural flows during the first 15 minutes. Because several team members had different formatting conventions, early discussion occasionally drifted toward stylistic preferences (such as line breaks and dictionary formatting) before we redirected our focus toward business logic and error handling. Automated linter checks should have resolved these concerns prior to the team meeting.

Another difficulty was reviewing a file with over 700 lines of code within a single 60-minute window. While we thoroughly examined the authentication middleware, reservation creation endpoints, and error-handling blocks, we had to accelerate our review of the timetable schedule export and room deletion handlers toward the final 10 minutes. Attempting to review an entire monolithic coordinator file in one sitting proved slightly ambitious for a 60-minute timebox.

---

## 5. What We Will Do Differently Next Time

In future code reviews, our team will institute an automated pre-review gate. Specifically, all code must pass 100% of our static analysis tools (`pylint` rating $\ge 9.5$ and `flake8` compliance) before the team review session begins. By delegating formatting, naming conventions, and docstring checks to algorithmic linters in advance, 100% of the team's review time can be dedicated to algorithmic correctness, concurrency safety, edge cases, and architectural clarity.

Additionally, we will divide large files into distinct functional sections (e.g., Auth & Middleware in Phase 1, Room Management in Phase 2, and Reservation Scheduling in Phase 3) and assign specific lead reviewers to each section prior to the call. Having designated topic owners prepare questions beforehand will enable us to pace the 60-minute timer evenly and ensure every critical code path receives thorough, deep-dive scrutiny.
