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
    run_meta = p_meta.add_run("Version 1.1  |  Latest Update: 2026-11-02  |  Target Release: Public Class Demo\nStatus: Render demo is live; PWA update awaits push and redeployment\nAuthor: Team Vibranium (Su Pyae Pyae Aung, Zin Zin Zaw Win, & Team)")
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
    add_p("The deployed product is a browser-based progressive web application (PWA): a React single-page frontend and Flask REST API run together as a Docker web service on Render. Users visit the HTTPS service URL; the browser renders the client UI and sends API requests to the same origin. Docker, Python, and Node.js are build/server dependencies, not client installation requirements.")

    add_h2("1.1 Client-Side Supported Environments")
    add_p("These are target environments for browser-based use. The project has verified the hosted application URL, but has not completed a formal compatibility matrix across every listed browser and device. Record the browser/version and result when executing Section 6.")
    add_bullet(" Windows 10/11 desktop or laptop using current stable Google Chrome or Microsoft Edge.", "Windows client: ")
    add_bullet(" macOS 14/15 desktop or laptop using current stable Safari or Google Chrome.", "macOS client: ")
    add_bullet(" Android phone or tablet using current stable Google Chrome; browser installation may be offered as Install app or Add to Home screen.", "Android client: ")
    add_bullet(" iPhone or iPad using current stable Safari; users can add the website to the Home Screen from the Share menu.", "iOS/iPadOS client: ")
    add_bullet(" A modern browser with JavaScript, localStorage, and HTTPS support. An internet connection is required for live API operations; the cached application shell is not an offline reservation service.", "Browser and network: ")

    add_h2("1.2 Client Hardware and Display")
    add_bullet(" A supported web browser on a phone, tablet, laptop, or desktop; no specific processor architecture is required by the client.", "Device: ")
    add_bullet(" Recommended viewport: 1280 × 720 or larger for timetable and room cards. Smaller/mobile viewports should be included in responsive checks; this is a viewing recommendation, not a server requirement.", "Display: ")
    add_bullet(" Client storage must allow browser localStorage for the current login/session and demo fallback behavior. Do not rely on browser storage as a shared or server-side database.", "Browser storage: ")

    add_h2("1.3 Hosted Server and Build Environment")
    add_bullet(" Render hosts the public web service and provides a generated HTTPS onrender.com URL. The current demo uses Render's Free plan; the service may sleep when idle.", "Hosting: ")
    add_bullet(" Render builds the Docker image using Node.js 22 for Vite and Python 3.12 for Flask/Gunicorn. End users do not install Docker, Python, or Node.js.", "Server build/runtime: ")
    add_bullet(" SQLite is configured at /tmp/app.db for the free demo. This filesystem is ephemeral; records can be lost when the service sleeps, restarts, or redeploys. This deployment is for fictional class-demo data only.", "Demo database: ")
    add_bullet(" A persistent disk is not configured because it is not included with the free service plan. Real or important reservations require an approved persistent data service and production account/security changes.", "Data limitation: ")

    # =========================================================================
    # 2. DEPLOYMENT STRATEGY SUMMARY
    # =========================================================================
    add_h1("2. Deployment Strategy Summary")
    add_p("The current release is a public class-demo web deployment. The Render demo is live; the PWA files and corrected deployment documentation in this revision are implemented locally and must be pushed and successfully redeployed before the live URL has the installable version. A user opens the HTTPS URL in a supported browser; installation is optional. This section documents the actual Render configuration rather than unimplemented server platforms.")

    add_h2("2.1 Web Deployment Architecture")
    add_bullet(" A browser connects over HTTPS to the Render-provided onrender.com hostname. Render routes requests to one Docker web service; Flask serves the compiled React application and /api endpoints from the same origin.", "Request path: ")
    add_bullet(" The repository's Dockerfile builds the Vite frontend with Node.js 22, then installs Flask dependencies and runs the WSGI app with Gunicorn on Render's assigned PORT.", "Build and runtime: ")
    add_bullet(" The Render Blueprint (render.yaml) specifies the Free plan, Docker runtime, /api/health health check, and DB_PATH=/tmp/app.db. No persistent disk or custom domain is configured.", "Hosted configuration: ")
    add_bullet(" Render's generated HTTPS hostname and DNS are sufficient for public class-demo access; no user-managed DNS record is required. A custom domain is optional and requires adding the hostname in Render and creating the DNS record requested by Render.", "Public URL and DNS: ")
    add_bullet(" The frontend includes a web app manifest, app icons, and a service worker to support browser installation and caching of the UI shell/static assets. Authentication and reservation API actions still require network access; offline changes do not synchronize.", "Optional browser installation: ")

    add_h2("2.2 Optional Installation Experience")
    add_bullet(" Users can open the URL directly without installing anything. On supported desktop browsers, use the browser's Install app or Create shortcut menu; on Android use Install app/Add to Home screen; on iOS/iPadOS use Safari Share > Add to Home Screen.", "Browser installation: ")
    add_bullet(" Installation creates a browser-managed app shortcut, not a native Windows/macOS binary. It does not remove the need for internet access or make the free-tier database persistent.", "Installation limitation: ")

    add_h2("2.3 Build and Release Artifacts")
    add_bullet(" Dockerfile and .dockerignore define the two-stage frontend/backend image build used by Render.", "Container build: ")
    add_bullet(" render.yaml declares the Render web service, Free plan, health check, and ephemeral database path.", "Render Blueprint: ")
    add_bullet(" requirements-render.txt and wsgi.py provide Gunicorn dependencies and the production WSGI entry point.", "Python runtime: ")
    add_bullet(" reservation-app/public/manifest.webmanifest, service-worker.js, and 192px/512px icons support PWA installation and cached UI assets.", "PWA files: ")
    add_bullet(" GitHub main branch is the deployment source; pushes trigger Render builds. The live service should be checked after each deployment.", "Release source: ")

    # =========================================================================
    # 3. INSTALLATION PACKAGE CONTENTS
    # =========================================================================
    add_h1("3. Web Application Delivery and Installation")
    add_p("The normal user delivery is a URL, not a downloadable setup wizard. The same-origin web application includes the frontend, API, and browser-install metadata.")

    add_h2("3.1 Required Source or Compiled Files")
    add_bullet(" Vite-generated React and Tailwind production files in reservation-app/dist/ are copied into the Docker image.", "Frontend bundle: ")
    add_bullet(" Flask API gateway, Room Service, Reservation Service, Auth Service, and SQLite persistence modules are included in the server image.", "Backend modules: ")
    add_bullet(" The web manifest lists the app name, standalone display mode, start URL, and 192px/512px PNG icons. The service worker caches the app shell and static assets, not API responses.", "Install metadata and assets: ")
    add_bullet(" Docker, Python, Node.js, and Gunicorn are installed or used on the hosted build/runtime; browser users do not install these tools.", "Server-side dependencies: ")

    add_h2("3.2 User Installation Steps")
    add_bullet(" No installation is required: open the HTTPS Render URL in a supported browser.", "Use as a website: ")
    add_bullet(" To install on desktop, use the browser menu's Install app/Create shortcut option when offered. On Android use Chrome's Install app/Add to Home screen; on iOS/iPadOS use Safari Share > Add to Home Screen.", "Optional PWA installation: ")
    add_bullet(" The installed shortcut opens the hosted website and requires internet access for authentication and live bookings. The service worker provides a cached UI shell only; it is not an offline booking system.", "Online requirement: ")

    add_h2("3.3 Client-Side Supported Environments")
    add_bullet(" Target clients are Windows 10/11 with current Chrome/Edge; macOS 14/15 with current Safari/Chrome; Android with current Chrome; and iOS/iPadOS with current Safari. These targets require formal execution of TC-DEP-02 through TC-DEP-04 before claiming verified compatibility.", "Browser matrix: ")
    add_bullet(" End users need internet access and JavaScript/localStorage enabled. No Python, Node.js, Docker, or repository checkout is required on a client device.", "Client requirements: ")

    add_h2("3.4 Documentation and Test Assets")
    add_bullet(" README.md contains developer setup, demo account details, and Render deployment notes. Do not treat documented demo credentials as production accounts.", "README.md: ")
    add_bullet(" Lab_Vibranium_Functional_Test_Plan.xlsx contains the detailed functional integration/system cases; Section 6 includes a deployment checklist and functional smoke-test subset.", "Functional test workbook: ")

    # =========================================================================
    # 4. DEPLOYMENT CONFIGURATION
    # =========================================================================
    add_h1("4. Deployment Configuration")
    add_p("The following files are implemented and used by the current Render deployment. No Docker Compose file, server setup scripts, custom DNS, persistent disk, or cross-platform executable release is part of this demo configuration.")

    add_bullet(" Builds the React production assets with Node.js 22, then installs Python dependencies and runs Gunicorn in a Python 3.12 image.", "Dockerfile: ")
    add_bullet(" Declares the Render Docker web service, Free plan, /api/health check, and ephemeral DB_PATH=/tmp/app.db.", "render.yaml: ")
    add_bullet(" Lists the production Python requirements, including Gunicorn, without changing the local development requirements.", "requirements-render.txt: ")
    add_bullet(" Creates the Flask app with the database location provided through DB_PATH; retains the existing local database default for desktop use.", "wsgi.py and desktop_app.py: ")
    add_bullet(" Defines the PWA manifest, standalone display, app icons, and service worker. The worker caches the UI shell/static assets and does not cache API responses.", "reservation-app/public/: ")
    add_bullet(" The Blueprint uses Render's generated HTTPS hostname. DNS records are only needed if the team later configures a custom domain.", "Public URL: ")

    # =========================================================================
    # 5. DEPLOYMENT TASKS
    # =========================================================================
    add_h1("5. Deployment Tasks")
    add_p("This checklist describes the Render Free class-demo release. Complete the PWA changes on the deployment branch before redeploying; use fictional data only because the free-tier SQLite file is ephemeral.")

    tasks = [
        ("Task 1: Quality gate", "Run the Python unittest suites and frontend npm run lint / npm run build. Record the actual totals and resolve or document failures before release."),
        ("Task 2: PWA build check", "Confirm the built dist contains manifest.webmanifest, service-worker.js, and valid 192px/512px PNG icons; verify the manifest and service-worker routes return successfully."),
        ("Task 3: Publish source", "Commit and push the reviewed deployment/PWA changes to the GitHub branch connected to the Render Blueprint. Do not include app.db or local secrets."),
        ("Task 4: Review Render Blueprint", "Confirm the Docker service uses the Free plan, /api/health health check, and DB_PATH=/tmp/app.db, with no paid disk or unexpected resource."),
        ("Task 5: Deploy and check health", "Wait for the Render build to complete and service status to become Live. Open the generated HTTPS URL and verify the frontend and /api/health."),
        ("Task 6: Test public access and installation", "Open the public URL on a separate network/device; test client browsers and install the PWA shortcut. Record device/browser versions and results."),
        ("Task 7: Functional regression", "Execute the functional smoke cases in Section 6 and the detailed Lab_Vibranium_Functional_Test_Plan.xlsx. Record pass/fail/not-run evidence."),
        ("Task 8: Handover and limitations", "Submit the corrected plan and functional test evidence. Tell users the free service may sleep and lose SQLite demo data; do not use it for real reservations.")
    ]

    for title, desc in tasks:
        add_p(desc, bold_prefix=title + " — ", space_after=4)

    # =========================================================================
    # 6. DEPLOYMENT AND FUNCTIONAL TEST PLAN
    # =========================================================================
    add_h1("6. Deployment and Functional Test Plan")
    add_p("Run the deployment checks and the functional smoke subset against the current Render HTTPS URL after the PWA revision is redeployed. These cases are proposed acceptance checks, not pre-filled pass results. Record the tester, date, browser/device/version, actual result, and status. The functional workbook records an earlier run (2026-10-30) with 46 passed, 3 failed, and 1 not run out of 50; rerun the failed and not-run cases against the deployed revision. Use Lab_Vibranium_Functional_Test_Plan.xlsx for detailed functional steps and data.")

    def add_test_table(headers, cases):
        table = doc.add_table(rows=1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table)
        hdr_cells = table.rows[0].cells
        for i, text in enumerate(headers):
            hdr_cells[i].text = text
            set_cell_background(hdr_cells[i], "1A365D")
            set_cell_margins(hdr_cells[i], top=110, bottom=110, left=90, right=90)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8)
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)

        for case in cases:
            row_cells = table.add_row().cells
            for i, value in enumerate(case):
                row_cells[i].text = value
                set_cell_margins(
                    row_cells[i], top=80, bottom=80, left=90, right=90
                )
                if i % 2 == 1:
                    set_cell_background(row_cells[i], "F8FAFC")
                p = row_cells[i].paragraphs[0]
                p.paragraph_format.line_spacing = 1.05
                for run in p.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(7.5)
                    run.font.color.rgb = BODY_DARK
                    if i == 0:
                        run.font.bold = True
                        run.font.color.rgb = ACCENT_BLUE
        widths = [Inches(0.65), Inches(1.1), Inches(2.0), Inches(2.0), Inches(0.75)]
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = width
        return table

    add_h2("6.1 Deployment, Client, DNS, and Installation Checks")
    deploy_cases = [
        ("DEP-01", "Public URL / health", "Open the Render HTTPS URL from a separate network. Request /api/health.", "Page loads over HTTPS; API health returns HTTP 200. Render URL works without custom DNS.", "Not run"),
        ("DEP-02", "Windows browser", "Open the site in current stable Chrome and Edge on Windows 10/11; record versions and inspect console.", "Login UI renders and core controls are usable without uncaught errors.", "Not run"),
        ("DEP-03", "macOS browser", "Open the site in current stable Safari and Chrome on macOS 14/15; record versions.", "Login UI renders and core controls are usable without uncaught errors.", "Not run"),
        ("DEP-04", "Mobile browser", "Open the URL on Android Chrome and iOS/iPadOS Safari; check room cards and timetable viewport.", "Content remains usable at mobile width; no horizontal clipping blocks essential actions.", "Not run"),
        ("DEP-05", "PWA installation", "Check manifest and 192/512 icons in browser DevTools. Install from Edge/Chrome menu; on iOS use Safari Share > Add to Home Screen.", "Name/icon are shown; installed shortcut opens the HTTPS app in a standalone window. Installation is browser-managed, not a native installer.", "Not run"),
        ("DEP-06", "PWA offline behavior", "After online load, disable network and reopen the installed app; try loading cached UI and making a booking.", "Cached shell/static assets may render. API booking requires network; no offline write/sync is promised.", "Not run"),
        ("DEP-07", "Refresh / route fallback", "Refresh the app and open a client-side fallback URL directly.", "The frontend shell loads; API unknown routes remain JSON 404 responses.", "Not run"),
        ("DEP-08", "Free service wake-up", "Leave the service idle long enough to sleep, then open the HTTPS URL.", "Service wakes and responds; initial request may be delayed by the free-tier cold start.", "Not run"),
        ("DEP-09", "Ephemeral demo data", "Create a fictional reservation. Document the current record, then restart/redeploy only if safe to lose demo data.", "Do not assert persistence: /tmp/app.db is ephemeral and records may disappear after sleep, restart, or redeploy.", "Not run"),
        ("DEP-10", "Custom DNS (optional)", "Only if a team-owned domain is configured: add it in Render and publish the exact DNS record Render supplies; verify HTTPS.", "Custom hostname resolves and serves HTTPS. Otherwise the generated onrender.com URL is the supported public address.", "Optional"),
    ]
    add_test_table(
        ["ID", "Scenario", "Procedure", "Expected Result", "Status"],
        deploy_cases,
    )

    add_h2("6.2 Functional Regression Smoke Tests")
    add_p("Run these functional checks with fictional data. They supplement, not replace, the detailed functional cases and results in the workbook.")
    functional_cases = [
        ("FUN-01", "Authentication / roles", "Log in once as Staff and once as Professor using approved demo accounts; sign out between users.", "Each valid role reaches the app; invalid credentials are rejected; sign-out clears the session.", "Not run"),
        ("FUN-02", "Role permissions", "As Professor, attempt a staff-only room mutation; repeat permitted room browsing as Staff.", "Professor is denied staff-only changes; Staff can manage rooms.", "Not run"),
        ("FUN-03", "Room search", "Filter by a group size/equipment/date, then request a room recommendation.", "Only eligible rooms are returned and recommendation fits constraints.", "Not run"),
        ("FUN-04", "Reservation creation", "Create a valid fictional booking and view it in My Reservations and the schedule.", "Booking appears with the selected room, time, group size, and competency.", "Not run"),
        ("FUN-05", "Conflict / capacity", "Attempt an overlapping booking in the same room and a group larger than room capacity.", "Conflicting and over-capacity bookings are rejected with a clear error.", "Not run"),
        ("FUN-06", "Closures / export", "As Staff, close a room for a date range; verify availability, then view/export a weekly schedule.", "Closed room is unavailable during the closure; schedule and text export show the expected bookings.", "Not run"),
        ("FUN-07", "Restart persistence", "Run only on a separately configured persistent-data deployment: create a fictional booking and restart.", "Booking remains after restart only when a persistent database is configured. Not applicable to the current Free /tmp database.", "Not applicable"),
    ]
    add_test_table(
        ["ID", "Scenario", "Procedure", "Expected Result", "Status"],
        functional_cases,
    )

    # Save document
    output_filename = "Deployment_Plan_Team_Vibranium.docx"
    doc.save(output_filename)
    print(f"Deployment plan saved successfully as {output_filename}")

    # Also update DeploymentPlan_Template.docx with the complete version
    doc.save("DeploymentPlan_Template.docx")
    print("DeploymentPlan_Template.docx updated successfully")

if __name__ == "__main__":
    build_deployment_plan()
