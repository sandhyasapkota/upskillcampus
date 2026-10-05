# Inventory Management System — Project Report

**Student:** [Your name]  
**Internship/provider:** [Organization]  
**Submission date:** [Date]

## Problem and objective

Small teams often track inventory in spreadsheets, making it difficult to see low stock or trace quantity changes. Stockroom provides a central web interface for product records, stock movements, and role-based team access.

## Technology

Python, Flask, SQLite, Jinja2, HTML, CSS, and JavaScript. Werkzeug hashes account passwords; Python's unittest checks main workflows. The browser sends requests to Flask, Flask validates user access and input, SQLite persists data, and Jinja renders the response.

## Database design

| Table | Main fields | Purpose |
| --- | --- | --- |
| users | id, username, password_hash, role | Accounts and permissions |
| products | id, sku, name, category, price_cents, quantity, threshold, active | Product catalog and current balance |
| movements | id, product_id, user_id, kind, amount, balance, note, created_at | Permanent stock history |

One product has many movements. One user records many movements. Product and user foreign keys identify the item and actor for each event.

## Main modules

1. Authentication and admin/staff access control.
2. Dashboard with active products, total units, inventory value, and low-stock alerts.
3. Product creation, editing, search, filtering, and archival.
4. Transactional stock receipt and issue, preventing negative inventory.
5. Activity history with actor, reason, timestamp, and resulting balance.
6. Admin-managed team accounts and inventory CSV reports.

## Validation and testing

Run `python -m unittest discover -s tests -v` and insert your result here. Include screenshots of test output and representative application pages. Explain why testing negative quantities, insufficient stock, duplicate SKUs, and unauthorized staff actions matters.

## Demo script (3–5 minutes)

1. Sign in as admin and explain the overview metrics and low-stock list.
2. Add a product with a unique SKU, price, and reorder level.
3. Receive 10 units and show the updated quantity and activity entry.
4. Issue 7 units to trigger a low-stock alert.
5. Attempt to issue 4 more units and show that the system rejects the request without changing the balance.
6. Search/filter products and download a CSV report.
7. Create a staff account, sign out, and demonstrate that staff can move stock but cannot manage products/users.
8. Explain permanent history and suggest one future enhancement.

## Screenshots to add

- Dashboard with sample inventory.
- Product catalog and low-stock filter.
- Stock movement form and activity log.
- Team management and staff navigation.
- Passing tests.

## Limitations and future enhancements

This version is a local small-team prototype with in-app alerts, one inventory location, and no supplier/purchasing workflow. Future improvements include email alerts, barcode scanning, stock locations, PostgreSQL, paginated history, and account recovery. Review the implementation and customize it before presenting; be prepared to explain the stock transaction and permission checks.
