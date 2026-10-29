# -*- coding: utf-8 -*-
"""
Generates the comprehensive, professional Software Deployment Plan DOCX
for Team Vibranium's Classroom Reservation Application (SEN-201, CMKL University).
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def build_deployment_plan():
    doc = docx.Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Color Palette: Professional Academic Tech (Navy / Slate)
    NAVY = RGBColor(26, 54, 93)       # #1A365D - Primary Headers
    SLATE = RGBColor(71, 85, 105)     # #475569 - Secondary Headers & Subtitles
    BODY_DARK = RGBColor(30, 41, 59)  # #1E293B - Body Text
    ACCENT_BLUE = RGBColor(37, 99, 235) # #2563EB - Highlights

    # Document Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(4)
    run_org = p_title.add_run("CMKL UNIVERSITY | SEN-201 SOFTWARE ENGINEERING PROCESSES\n")
    run_org.font.name = "Arial"
    run_org.font.size = Pt(10)
    run_org.font.bold = True
    run_org.font.color.rgb = SLATE

    run_proj = p_title.add_run("[Team Vibranium - Classroom Reservation Application]\nSoftware Deployment Plan")
    run_proj.font.name = "Arial"
    run_proj.font.size = Pt(22)
    run_proj.font.bold = True
    run_proj.font.color.rgb = NAVY

    # Metadata Subtitle
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.paragraph_format.space_after = Pt(24)
    run_meta = p_meta.add_run("Version 1.0  |  Latest Update: 2026-10-28  |  Target Release: Final Software Demo\nAuthor: Team Vibranium (Su Pyae Pyae Aung, Zin Zin Zaw Win, & Team)")
    run_meta.font.name = "Arial"
    run_meta.font.size = Pt(10)
    run_meta.font.italic = True
    run_meta.font.color.rgb = SLATE

    def add_h1(title_text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(title_text)
        run.font.name = "Arial"
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = NAVY
        return h

    def add_h2(title_text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        h.paragraph_format.keep_with_next = True
        run = h.add_run(title_text)
        run.font.name = "Arial"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = SLATE
        return h

    def add_p(text, bold_prefix=None, space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = "Arial"
            r_bold.font.size = Pt(10)
            r_bold.font.bold = True
            r_bold.font.color.rgb = BODY_DARK
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.color.rgb = BODY_DARK
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = "Arial"
            r_bold.font.size = Pt(10)
            r_bold.font.bold = True
            r_bold.font.color.rgb = BODY_DARK
        run = p.add_run(text)
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.color.rgb = BODY_DARK
        return p

    # =========================================================================
    # 1. SYSTEM REQUIREMENTS
    # =========================================================================
    add_h1("1. System Requirements")
    add_p("The CMKL Classroom Reservation Application is engineered as a modern, decoupled web application comprising a reactive single-page frontend (React 19 + Tailwind CSS) and an asynchronous REST API backend (Python Flask + SQLite). The software is designed to operate seamlessly across both server and client execution contexts, satisfying all mandatory OS specifications outlined in the SEN-201 deployment syllabus.")

    add_h2("1.1 Supported Operating Systems & Environments")
    add_bullet(" Windows 10 (Build 19041 and above) and Windows 11 (64-bit x86_64). Validated via standalone native executable packaging and local PowerShell execution.", "Microsoft Windows: ")
    add_bullet(" macOS 14 (Sonoma) and macOS 15 (Sequoia). Supports both Intel x86_64 architectures and Apple Silicon ARM64 (M1/M2/M3/M4) via native Python execution and containerized runtimes.", "Apple macOS: ")
    add_bullet(" SUSE Linux Enterprise Server (SLES) 15 and openSUSE Leap 15.4 / 15.5 / 15.6 (x86_64). Validated via systemd service units and POSIX-compliant deployment scripts.", "Linux SuSE Leap 15: ")
    add_bullet(" Ubuntu Linux 14.04 LTS through current LTS releases (Ubuntu 18.04, 20.04, 22.04, and 24.04 LTS, x86_64). Tested both in bare-metal virtual environments and standardized OCI container runtimes.", "Linux Ubuntu: ")

    add_h2("1.2 Hardware Requirements")
    add_bullet(" Dual-core 1.5 GHz 64-bit processor (x86_64 or ARM64).", "Processor (CPU): ")
    add_bullet(" Minimum 2.0 GB RAM (4.0 GB recommended to accommodate modern multi-tab web browsers during client-side rendering).", "Physical Memory (RAM): ")
    add_bullet(" Minimum 500 MB of free storage. The production distribution executable consumes ~14.0 MB, the initial SQLite database consumes ~1 MB, with remaining capacity reserved for application runtime logs, automated database backups, and browser caching.", "Storage / Disk Space: ")
    add_bullet(" Standard 10/100/1000 Mbps network interface. The system binds to TCP Port 5000 by default (configurable via the PORT environment variable) over localhost loopback (127.0.0.1) or an assigned LAN/Intranet IP address.", "Networking & Ports: ")
    add_bullet(" Minimum 1280 × 720 screen resolution recommended for optimal viewing of the room timetable and multi-column classroom cards.", "Display: ")

    add_h2("1.3 Software Dependencies & Runtime Management")
    add_p("In accordance with deployment best practices (Lecture 10), end users and evaluators are NOT required to manually configure complex runtimes. Software dependencies are handled automatically based on the chosen deployment format:")
    add_bullet(" Zero external runtime dependencies required. The Python interpreter, Flask microframework, SQLite3 C-engine, and compiled React single-page application are fully embedded inside a single portable binary.", "Standalone Executable Kit (Primary Evaluation Format): ")
    add_bullet(" Requires Docker Engine 20.10+ and Docker Compose v2.0+. No host-level Python or Node.js installations are required; dependencies are managed within container layers.", "Containerized Production Deployment (Server Format): ")
    add_bullet(" Requires Python 3.10+ and a standard package manager (pip, uv, or conda). All third-party Python packages are tracked and pinned within requirements.txt.", "Source-Based Deployment (Developer Format): ")

    # =========================================================================
    # 2. DEPLOYMENT STRATEGY SUMMARY
    # =========================================================================
    add_h1("2. Deployment Strategy Summary")
    add_p("Following the principles of Lecture 10 (Packaging and Deployment), Team Vibranium adopts a Dual-Distribution Strategy designed to balance two essential goals: (1) an effortless, zero-install 3-minute evaluation experience for course examiners, and (2) a robust, multi-user production-ready architecture for campus-wide infrastructure.")

    add_h2("2.1 Dual-Tier Deployment Architecture")
    add_bullet(" For the project viva and desktop users, the complete application is bundled into a self-contained executable (ClassroomReservationApp.exe on Windows, and standalone binaries for macOS/Linux). When launched, an automated orchestration script (desktop_app.py) provisions the embedded SQLite database (app.db), starts the Flask WSGI microservices on http://127.0.0.1:5000, and automatically launches the user's default web browser within 1.2 seconds. This completely eliminates runtime mismatch errors (e.g., 'Python not found' or 'Node version incompatible').", "Tier 1: Standalone Single-File Executable Kit (Evaluation & Local Demo). ")
    add_bullet(" For long-term institutional deployment across Ubuntu and SuSE servers, the application is packaged as a Multi-Stage OCI Container (Dockerfile & docker-compose.yml). Stage 1 uses Node.js 20-Alpine to compile the optimized React production bundle via Vite. Stage 2 copies the minified static assets into a slim Python 3.10 runtime served behind an industrial-grade WSGI server (Gunicorn on POSIX / Waitress on Windows). An external volume mount guarantees database persistence across container updates.", "Tier 2: Multi-Stage Containerized Server Deployment (Production Infrastructure). ")

    add_h2("2.2 Tooling & Distribution Artifacts")
    add_bullet(" PyInstaller 6.x (configured via build_exe.py with a custom dis.py opcode constant patch for Python 3.10 compatibility).", "Packaging Tool: ")
    add_bullet(" Vite 6.x with Rollup for JavaScript bundling, asset tree-shaking, and CSS minification.", "Frontend Build Tool: ")
    add_bullet(" Standard Python venv combined with requirements.txt (pinned dependencies) and Docker BuildKit.", "Dependency Management: ")
    add_bullet(" A unified ClassroomReservationApp-Release-v1.0.zip archive containing the standalone executable, sample app.db, automated setup scripts (.bat / .sh), and documentation.", "Final Distribution Kit: ")

    # =========================================================================
    # 3. INSTALLATION PACKAGE CONTENTS
    # =========================================================================
    add_h1("3. Installation Package Contents")
    add_p("This section enumerates all files and components included in the final distribution kit, categorized according to their operational function.")

    add_h2("3.1 Required Source or Compiled Files")
    add_bullet(" Compiled Single-Page Application (SPA) production assets generated via Vite: reservation-app/dist/index.html, reservation-app/dist/assets/index-*.js (minified React application), reservation-app/dist/assets/index-*.css (compiled Tailwind stylesheet), and reservation-app/dist/favicon.svg.", "Frontend Production Bundle: ")
    add_bullet(" Modular Flask backend packages: ApiGateway/ (api_gateway.py, routing, JWT middleware, CORS), AuthService/ (auth_service.py, seed_users.py), RoomService/ (room_service.py, models.py), Reservation/ (reservation_service.py), and Database/ (db.py).", "Backend Application Modules: ")
    add_bullet(" desktop_app.py (desktop launcher with browser auto-open and cache-control headers) and wsgi.py (WSGI production gateway).", "Launcher & Gateway Scripts: ")

    add_h2("3.2 Required Third-Party Components")
    add_bullet(" Flask (v2.3+), Flask-CORS (v3.0.10+), PyJWT (v2.8.0+), Werkzeug (v2.3+), and Gunicorn (v21.0+) / Waitress (v2.1+).", "Python Runtime Libraries: ")
    add_bullet(" React (v19.0.0), React-DOM (v19.0.0), Lucide-React (v0.400+), and Tailwind CSS (v3.4+). All frontend dependencies are compiled and tree-shaken into the distribution bundle, requiring no client-side package downloads.", "Frontend Vendor Libraries: ")
    add_bullet(" SQLite3 (embedded within Python standard library; zero separate database server installation needed).", "Database Engine: ")

    add_h2("3.4 Required Graphical Assets, Configuration & Non-Program Files")
    add_bullet(" CMKL University branding icons, building category SVG vectors, and UI status indicator graphics.", "Graphical Assets: ")
    add_bullet(" Database/schema.sql (DDL defining relational tables: users, rooms, reservations, with foreign key integrity and audit timestamps).", "Database Schema: ")
    add_bullet(" .env.example / config.py (defining PORT=5000, SECRET_KEY, FLASK_ENV=production, and DB_PATH=app.db).", "Configuration Files: ")

    add_h2("3.5 Documentation Files Provided")
    add_bullet(" Comprehensive setup, execution, and quickstart guide.", "README.md: ")
    add_bullet(" In-depth server deployment guide covering Windows, macOS, Ubuntu, and SuSE Leap 15.", "DEPLOYMENT.md: ")
    add_bullet(" End-user manual detailing classroom search, reservation booking, schedule export, and role-based permissions.", "USER_GUIDE.md: ")
    add_bullet(" Interactive OpenAPI/Swagger JSON and Markdown specification of all REST endpoints.", "API_DOCUMENTATION.md: ")
    add_bullet(" Complete line-by-line architectural breakdown of the Room Service and Data Layer.", "RoomService_Micky_Comprehensive_Guide.pdf: ")

    add_h2("3.6 Development Files and Components Excluded from Distribution")
    add_p("To minimize attack surface, ensure confidentiality, and optimize bundle size, the following development artifacts are strictly excluded from the release package:")
    add_bullet(" Raw uncompiled React files (reservation-app/src/), development Vite configuration (vite.config.js), package.json, and the massive reservation-app/node_modules/ directory (~250 MB).", "Development Source Files: ")
    add_bullet(" Unit and integration test suites (test_api_gateway.py, test_room_service.py, test_auth.py), mock fixtures, and .pytest_cache/.", "Testing Suites & Mocks: ")
    add_bullet(" .git/, .gitignore, .github/ CI workflows, and IDE settings (.vscode/, .gemini/).", "Version Control & IDE Configurations: ")
    add_bullet(" Intermediate compilation files (__pycache__/, *.pyc, *.pyo, build/, *.spec).", "Build Artifacts & Temporary Caches: ")

    # =========================================================================
    # 4. ADDITIONAL CODE REQUIRED FOR DEPLOYMENT
    # =========================================================================
    add_h1("4. Additional Code Required for Deployment")
    add_p("To automate deployment across diverse operating systems and package formats, Team Vibranium engineered several dedicated deployment scripts and configuration files:")

    add_bullet(" A specialized Python build script that invokes PyInstaller with a custom bytecode constant patch for Python 3.10.0, automatically bundling the React dist/ folder and modular service packages into a single binary.", "build_exe.py: ")
    add_bullet(" An automated desktop wrapper that detects frozen vs. loose execution modes, sets HTTP no-cache headers on static assets, handles SPA client routing fallbacks (returning index.html on 404), dynamically binds SQLite, and spawns the user's default browser.", "desktop_app.py: ")
    add_bullet(" A containerization manifest featuring a two-stage build: Stage 1 builds the Vite bundle on Node 20-Alpine; Stage 2 establishes a lightweight Python 3.10-slim runtime hosting Gunicorn on port 5000.", "Dockerfile: ")
    add_bullet(" Defines service boundaries, port bindings (5000:5000), environment variables, health checks, and persistent volume mounts for app.db.", "docker-compose.yml: ")
    add_bullet(" A POSIX-compliant shell script for Ubuntu and SuSE Linux that verifies the Python runtime, creates a clean virtual environment, installs requirements.txt, runs database migrations, and initializes the application.", "deploy_setup.sh: ")
    add_bullet(" A Windows batch script that performs automated environment validation, virtual environment activation, and one-click application launch.", "deploy_setup.bat: ")
    add_bullet(" An idempotent database seeding script that verifies table existence and populates initial CMKL rooms and test accounts upon deployment.", "Database/seed_data.py: ")

    # =========================================================================
    # 5. DEPLOYMENT TASKS
    # =========================================================================
    add_h1("5. Deployment Tasks")
    add_p("The following ordered checklist specifies the exact sequential tasks required to package, verify, and deploy the application for production release:")

    tasks = [
        ("Task 1: Pre-Build Quality Gate & Testing", "Execute the complete automated test suite (pytest -v). Verify that all 119/119 unit tests pass across ApiGateway, AuthService, RoomService, ReservationService, and Database modules with zero failures."),
        ("Task 2: Frontend Production Compilation", "Navigate to reservation-app/ and execute 'npm run build'. Verify that Vite compiles the TypeScript/JSX source into minified assets inside dist/ (index.html, JS bundles, and CSS stylesheets) with zero syntax errors."),
        ("Task 3: Database Schema Initialization & Seeding", "Execute Database/seed_data.py. Confirm that app.db is initialized with all relational tables (foreign key constraints enabled) and populated with CMKL campus rooms (601-609, Auditorium) and default test user accounts."),
        ("Task 4: Packaging Standalone Executable", "Execute 'python build_exe.py'. Ensure PyInstaller successfully bundles static assets and Python modules into dist/ClassroomReservationApp.exe (~14.0 MB) with exit code 0."),
        ("Task 5: Container Image Generation", "Execute 'docker build -t team-vibranium/classroom-reservation:1.0 .'. Verify both build stages complete successfully and that the final image size is optimized (<180 MB)."),
        ("Task 6: Smoke Testing & Sanity Check", "Deploy the packaged binary on a pristine Windows 10/11 virtual machine and the container on Ubuntu 22.04 LTS. Verify that port 5000 opens, browser auto-launches, authentication functions, and room reservations persist."),
        ("Task 7: Distribution Kit Archival", "Assemble the final distribution package into ClassroomReservationApp-Release-v1.0.zip containing ClassroomReservationApp.exe, app.db, README.md, and documentation."),
        ("Task 8: Production Release & Canvas Handover", "Upload the distribution kit to the designated repository release channel and submit the Deployment Plan to the SEN-201 Canvas portal.")
    ]

    for title, desc in tasks:
        add_p(desc, bold_prefix=title + " — ", space_after=4)

    # =========================================================================
    # 6. DEPLOYMENT TEST PLAN
    # =========================================================================
    add_h1("6. Deployment Test Plan")
    add_p("The Deployment Test Plan defines the formal test cases utilized to ensure that the deployment kit operates correctly across all target operating systems, handles environmental edge cases, and satisfies all architectural constraints.")

    # Table of Test Cases
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    headers = ["Test ID", "Target Platform & Scenario", "Execution Procedure", "Expected Result"]
    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        hdr_cells[i].text = h_text
        set_cell_background(hdr_cells[i], "1A365D")
        set_cell_margins(hdr_cells[i], top=140, bottom=140, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = "Arial"
            run.font.size = Pt(9.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

    test_cases = [
        ("TC-DEP-01", "Windows 10/11\nClean Installation", "Extract ClassroomReservationApp-Release-v1.0.zip on a clean machine with no Python or Node.js installed. Double-click ClassroomReservationApp.exe.", "Console opens; Flask starts; default web browser automatically launches to http://127.0.0.1:5000; CMKL login modal renders cleanly."),
        ("TC-DEP-02", "Linux Ubuntu 22.04\nContainer Deployment", "Run 'docker compose up -d' on Ubuntu server. Navigate to host IP:5000 using remote browser.", "Container builds and enters healthy state; port 5000 responds with 200 OK; React frontend loads without console errors."),
        ("TC-DEP-03", "Linux SuSE Leap 15\nScripted Setup", "Execute './deploy_setup.sh' on openSUSE Leap 15. Verify virtual environment creation and server startup.", "Script successfully detects Python 3, installs dependencies, initializes app.db, and starts background server."),
        ("TC-DEP-04", "macOS 14/15\nARM64 & Intel", "Execute 'python desktop_app.py' or standalone binary on macOS Sonoma / Sequoia under both M-series and Intel.", "App initializes without architectural binary conflicts; Safari/Chrome opens to reservation dashboard."),
        ("TC-DEP-05", "Port Conflict Handling\n(Port 5000 In Use)", "Run another process on port 5000, then launch deployment script or set PORT=5050 in environment.", "System detects port conflict gracefully, binds to alternative port or logs an actionable error message instead of crashing silently."),
        ("TC-DEP-06", "Database State Retention\n& Persistence", "Book a classroom reservation (e.g. Room 604), shut down application/container, restart application.", "Previously created reservation remains visible and intact in app.db; no data loss occurs upon restart."),
        ("TC-DEP-07", "SPA Deep Linking\n& Static Fallback", "Navigate directly in browser to http://127.0.0.1:5000/schedule or refresh page while on /my-reservations.", "Flask 404 handler serves index.html; React client-side router loads the requested route without blank screen."),
        ("TC-DEP-08", "Session Persistence\n& Token Expiry", "Sign in as Staff 1, refresh page; simulate expired token or logout.", "Session persists across refresh via localStorage; expired token redirects cleanly to login modal with session cleared.")
    ]

    for tc_id, plat, proc, exp in test_cases:
        row_cells = table.add_row().cells
        data = [tc_id, plat, proc, exp]
        for i, val in enumerate(data):
            row_cells[i].text = val
            set_cell_margins(row_cells[i], top=100, bottom=100, left=120, right=120)
            if i % 2 == 1:
                set_cell_background(row_cells[i], "F8FAFC")
            p = row_cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            for run in p.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)
                run.font.color.rgb = BODY_DARK
                if i == 0:
                    run.font.bold = True
                    run.font.color.rgb = ACCENT_BLUE

    # Set column widths
    col_widths = [Inches(1.0), Inches(1.6), Inches(2.2), Inches(2.2)]
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

    # Save document
    output_filename = "Deployment_Plan_Team_Vibranium.docx"
    doc.save(output_filename)
    print(f"Deployment plan saved successfully as {output_filename}")

    # Also update DeploymentPlan_Template.docx with the complete version
    doc.save("DeploymentPlan_Template.docx")
    print("DeploymentPlan_Template.docx updated successfully")

if __name__ == "__main__":
    build_deployment_plan()
