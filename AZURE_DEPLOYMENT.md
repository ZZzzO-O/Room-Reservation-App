# Azure deployment preparation

This repository is prepared to use Azure Database for PostgreSQL, but Azure
resources have not been created. Deploy only after the subscription owner
approves the region, resource plan, ongoing costs, and the university's
authorization to publish the room inventory and accept real reservations.

## Prepared in the application

- `DATABASE_URL` selects PostgreSQL; local development and the existing Render
  demo continue to use SQLite.
- PostgreSQL connections use dictionary rows, TLS options from the connection
  URL, and PostgreSQL identity columns for room closures.
- `APP_ENV=production` prevents startup from seeding the public test accounts.
- Production frontend builds remove the demo-account shortcuts and do not
  accept localStorage as a substitute for unavailable API data.
- `scripts/provision_user.py` creates individual Staff or Professor accounts
  using a password prompt, rather than a public sign-up page or command-line
  password.
- The Docker image includes the PostgreSQL driver.

## Recommended small-deployment shape

Use one Linux container web app and one Azure Database for PostgreSQL Flexible
Server in the same Azure region. Keep the web app to one instance and one
Gunicorn worker: the current services also hold rooms, accounts, sessions, and
reservations in process memory. Multi-instance scaling and concurrent
reservation guarantees need further engineering before enabling them.

The existing Dockerfile builds the React frontend and Flask server together.
An Azure Container Registry can hold the built image. For a small school
project, the exact Azure products and SKUs must be selected against the
subscription's current pricing and eligibility; do not assume they are free.
An Azure for Students subscription may have different credit and product
limits.

## Manual steps requiring your Azure access

1. **Confirm access and cost approval.** Sign in to the Azure portal and check
   that you have an active subscription with permission to create a resource
   group, PostgreSQL Flexible Server, a Linux web app/container, and a
   container registry. Ask the subscription owner/CMKL IT to approve the
   region, monthly spend limit, backups, and public-service ownership first.
2. **Confirm the data owner.** Get approval for the real room list, names,
   capacities, equipment, closures, who may receive Staff accounts, and
   whether public access is appropriate. Production startup does not seed
   sample rooms or users. Add only an authorized room inventory after
   provisioning the first Staff account.
3. **Create the Azure resources.** In one approved region, create a resource
   group, Azure Database for PostgreSQL Flexible Server and its application
   database, a container registry, and a Linux custom-container web app. Use
   a database network policy that allows only the application to connect;
   never add a broad `0.0.0.0` or “allow all Azure services” firewall rule.
   Prefer private networking if CMKL IT can configure the app and database
   into the same approved network. If using a public database endpoint, restrict
   its firewall to the web app's outbound IP addresses and recheck those
   addresses after app-plan changes.
4. **Build and publish the image.** From the repository root, build the
   existing `Dockerfile` and publish the image to the registry. Configure the
   web app to pull it using managed identity with the minimum `AcrPull`
   permission where supported. Do not commit registry credentials or database
   passwords.
5. **Configure runtime settings in Azure.** Add `APP_ENV=production` and
   `DATABASE_URL` to the web app's protected application settings. The URL
   should use the PostgreSQL server hostname, the application database/user,
   and `sslmode=require`. Store secrets in Azure's protected settings or Key
   Vault; never put the password in Git, a Dockerfile, or a terminal command
   that will be saved in shell history. Configure the container's listening
   port to match the Dockerfile (10000) and enable HTTPS-only access.
6. **Create accounts privately.** Run
   `python scripts/provision_user.py --email <email> --role Staff --name "<name>"`
   (or `--role Professor`) from a trusted management session that has the
   production `DATABASE_URL` set. The password is requested twice without
   echoing and must be at least 12 characters. Provision accounts only after
   identity and role approval; there is no public registration endpoint.
   Restart the App Service after provisioning so its in-memory account list
   reloads from PostgreSQL. Repeat the restart after adding accounts later.
7. **Verify before sharing the URL.** Check the web app health endpoint, sign
   in with each authorized role, verify permissions, create/edit/cancel
   fictional reservations, refresh the page, restart the app, and verify data
   persists in PostgreSQL. Confirm browser/API errors do not silently create
   local-only reservations. Test backups and a restore before real bookings.
8. **Set operational ownership.** Assign someone to monitor health, review
   application/database logs, rotate credentials, apply updates, handle account
   requests, and restore backups. Publish the URL only after these checks and
   the data owner's approval.

## Not yet production-validated

The PostgreSQL path has unit coverage for SQL adaptation and schema generation,
but it has not been tested against a live Azure PostgreSQL server. The app
loads core records into memory at startup and has not been hardened for
multiple app instances or concurrent booking transactions. Before treating
this as a real reservation system, test with a non-production Azure database,
review authentication/session and availability behavior with CMKL IT, verify
database backups/restores, and resolve concurrency and monitoring needs.

Do not migrate the Render demo database or its test users into Azure. Start with
an empty production database, load only authorized room inventory, and
provision real accounts individually.
