# Stockroom — Flask Inventory Management System

A Python internship final project for small-team inventory tracking. Includes a responsive dashboard, product management, stock-in/out transactions, low-stock indicators, user roles, a permanent activity log, and CSV export.

## Quick start (Windows PowerShell)

Python 3.8 or newer is required. Python 3.11+ is recommended for a new installation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app create-admin
.\.venv\Scripts\python.exe -m flask --app app seed-demo
.\.venv\Scripts\python.exe -m flask --app app run
```

Open http://127.0.0.1:5000 and sign in with the username and password you entered. There are no default credentials. `seed-demo` is optional; it adds six sample products and their opening stock history and only runs on an empty product database.

If you forget an administrator password, reset it without deleting the database:

```powershell
.\.venv\Scripts\python.exe -m flask --app app reset-admin-password
```

Enter the existing administrator username, then choose and confirm a new password of at least 8 characters.

If Flask is already installed, the shortest startup is:

```powershell
python -m flask --app app create-admin
python -m flask --app app seed-demo
python app.py
```

On macOS/Linux use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.

## Features and permissions

| Feature | Admin | Staff |
| --- | --- | --- |
| View dashboard, products, alerts, and activity | Yes | Yes |
| Record stock in/out and export product CSV | Yes | Yes |
| Create/edit/archive products | Yes | No |
| Create admin/staff accounts | Yes | No |

- Products start at zero stock. Record a stock-in movement for opening inventory.
- Stock cannot go negative. Balance updates and movement entries commit together in a SQLite transaction.
- Alerts appear when quantity is at or below the product's reorder level; zero stock is highlighted separately. Alerts are in-app, with no email or background service required.
- Archive only zero-stock products. Archived products disappear from the active catalog while their history remains. Archived SKUs cannot be reused.
- Movements cannot be edited/deleted. Correct mistakes by recording an opposite movement with a reason.
- Prices are stored as integer cents; amounts are displayed without a currency symbol so you can choose a currency for your submission. Inventory value uses current prices and is not an accounting valuation.
- Activity timestamps explicitly use UTC.
- Password hashing, session authentication, form CSRF tokens, role checks, SQL parameters, and CSV formula escaping are included.
- Google Fonts are optional; system fonts work offline. All application functionality runs locally.

## Project structure

```text
app.py                 Application factory, routes, SQLite schema, CLI commands
templates/             Jinja HTML pages
static/style.css       Responsive interface
static/app.js          Archive confirmation
tests/test_app.py      Workflow and access-control tests
requirements.txt       Python dependencies
docs/PROJECT_REPORT.md Submission report starter and demo script
instance/              Auto-created private SQLite database and session secret
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```

Tests use a temporary database and cover authentication, admin/staff permissions, CSRF rejection, stock balances, rejected overdrafts, validation, archival history, user creation, CSV escaping, page rendering, and CLI setup.

## One-week submission plan

1. **Day 1:** Run the app, review requirements, and learn the database relationships.
2. **Day 2:** Study login, session handling, and role checks. Create a staff account.
3. **Day 3:** Trace product creation and stock transaction code. Practice demonstrating rejected stock-out requests.
4. **Day 4:** Customize colors, product categories, and currency labels for your chosen business.
5. **Day 5:** Run the tests, manually check mobile layouts, and resolve any issues you find.
6. **Day 6:** Complete the project report and capture dashboard, catalog, movement, and team screenshots.
7. **Day 7:** Record a 3–5 minute demo and submit code, requirements, README, and report. Exclude `.venv`, `instance`, and real credentials.

## Runtime notes and future scope

`python app.py` and `flask run` start a local development server. Public deployment needs a production WSGI server, HTTPS, an environment-provided `SECRET_KEY`, secure session cookies, backups, and login rate limiting. SQLite fits this small project; for a larger system, consider PostgreSQL, pagination, suppliers/purchase orders, barcode scanning, account deactivation/password reset, and email alerts. These are future enhancements, not part of the current one-week scope.

Stop the server with Ctrl+C. Back up `instance/inventory.sqlite` while the app is stopped. Keep `instance/secret.key` private; it persists sessions between server restarts.
