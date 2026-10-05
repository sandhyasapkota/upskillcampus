# Stockroom demo walkthrough

The generated walkthrough is at `docs/recordings/stockroom-walkthrough.gif`.

Use this narration while playing the animation:

1. Stockroom is a Flask Inventory Management System for a small team.
2. The dashboard shows total products, units, current-price inventory value, and products at or below their reorder level.
3. Administrators create and edit products with a unique SKU, category, price, and reorder threshold.
4. Staff and administrators record stock receipts and issues. The system validates the form and prevents inventory from going below zero.
5. Every accepted transaction is retained in the activity log with the user, reason, timestamp, and resulting balance.
6. Administrators create accounts and assign admin or staff roles. Staff can move stock but cannot manage products or accounts.
7. The project has automated tests for authentication, permissions, validation, transactions, archival history, CSV export, and setup commands.

For an individual recorded demonstration, run `python app.py`, sign in, and follow the same sequence. Mention that the report and README explain setup and verification.
