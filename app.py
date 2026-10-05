import csv
import io
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for, Response
from werkzeug.security import check_password_hash, generate_password_hash


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','staff'))
);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY, sku TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 category TEXT NOT NULL DEFAULT '', price_cents INTEGER NOT NULL CHECK(price_cents>=0),
 quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
 threshold INTEGER NOT NULL DEFAULT 5 CHECK(threshold>=0),
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS movements (
 id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id),
 user_id INTEGER NOT NULL REFERENCES users(id),
 kind TEXT NOT NULL CHECK(kind IN ('in','out')), amount INTEGER NOT NULL CHECK(amount>0),
 balance INTEGER NOT NULL CHECK(balance>=0), note TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now'))
);
"""


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    secret_path = Path(app.instance_path) / 'secret.key'
    if not secret_path.exists():
        secret_path.write_text(secrets.token_hex(32))
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY') or secret_path.read_text(),
                      DATABASE=str(Path(app.instance_path) / 'inventory.sqlite'),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      MAX_CONTENT_LENGTH=1024 * 1024)
    if test_config:
        app.config.update(test_config)

    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE'], timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()

    @app.before_request
    def load_user_and_check_csrf():
        g.user = db().execute('SELECT * FROM users WHERE id=?', (session.get('user_id'),)).fetchone()
        session.setdefault('csrf', secrets.token_hex(32))
        if request.method == 'POST':
            token = request.form.get('csrf_token', '')
            if not secrets.compare_digest(token, session['csrf']):
                abort(400, 'Invalid form token. Reload the page and try again.')

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return wrapped

    def admin_required(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user['role'] != 'admin':
                abort(403)
            return view(*args, **kwargs)
        return wrapped

    def product_values():
        from decimal import Decimal, InvalidOperation
        sku = request.form.get('sku', '').strip().upper()
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        try:
            price = Decimal(request.form.get('price', ''))
            threshold = int(request.form.get('threshold', ''))
            if not price.is_finite() or price < 0 or price > 10000000 or price.as_tuple().exponent < -2:
                raise ValueError()
            cents = int(price * 100)
            if threshold < 0 or threshold > 1000000000:
                raise ValueError()
        except (ValueError, InvalidOperation, OverflowError):
            raise ValueError('Enter a valid price (up to two decimal places) and nonnegative reorder level.')
        if not sku or not name or len(sku) > 40 or len(name) > 100 or len(category) > 60:
            raise ValueError('SKU and name are required. Keep SKU under 40, name under 100, and category under 60 characters.')
        return sku, name, category, cents, threshold

    def escape_like(value):
        return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user = db().execute('SELECT * FROM users WHERE username=?', (request.form.get('username', '').strip(),)).fetchone()
            if user and check_password_hash(user['password_hash'], request.form.get('password', '')):
                session.clear()
                session['user_id'] = user['id']
                session['csrf'] = secrets.token_hex(32)
                return redirect(url_for('dashboard'))
            flash('Incorrect username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    @login_required
    def dashboard():
        stats = db().execute('SELECT COUNT(*) AS products, COALESCE(SUM(quantity),0) AS units, COALESCE(SUM(quantity*price_cents),0) AS value, COALESCE(SUM(quantity<=threshold),0) AS low FROM products WHERE active=1').fetchone()
        low = db().execute('SELECT * FROM products WHERE active=1 AND quantity<=threshold ORDER BY quantity, name').fetchall()
        recent = db().execute('SELECT m.*, p.name, p.sku, u.username FROM movements m JOIN products p ON p.id=m.product_id JOIN users u ON u.id=m.user_id ORDER BY m.id DESC LIMIT 8').fetchall()
        return render_template('dashboard.html', stats=stats, low=low, movements=recent)

    @app.get('/products')
    @login_required
    def products():
        search = request.args.get('q', '').strip()
        low_only = request.args.get('low') == '1'
        search_pattern = '%' + escape_like(search) + '%'
        query = 'SELECT * FROM products WHERE active=1 AND (name LIKE ? ESCAPE \'\\\' OR sku LIKE ? ESCAPE \'\\\' OR category LIKE ? ESCAPE \'\\\')'
        if low_only:
            query += ' AND quantity<=threshold'
        rows = db().execute(query + ' ORDER BY name', (search_pattern, search_pattern, search_pattern)).fetchall()
        return render_template('products.html', products=rows, search=search, low_only=low_only)

    @app.route('/products/new', methods=['GET', 'POST'])
    @admin_required
    def new_product():
        if request.method == 'POST':
            try:
                values = product_values()
                db().execute('INSERT INTO products(sku,name,category,price_cents,threshold) VALUES(?,?,?,?,?)', values)
                db().commit()
                flash('Product created. Record a stock-in movement to add opening stock.', 'success')
                return redirect(url_for('products'))
            except ValueError as error:
                flash(str(error), 'error')
            except sqlite3.IntegrityError:
                db().rollback()
                flash('That SKU already exists, including in archived products.', 'error')
        return render_template('product_form.html', product=None)

    @app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def edit_product(product_id):
        product = db().execute('SELECT * FROM products WHERE id=? AND active=1', (product_id,)).fetchone()
        if not product:
            abort(404)
        if request.method == 'POST':
            try:
                values = product_values()
                db().execute('UPDATE products SET sku=?,name=?,category=?,price_cents=?,threshold=? WHERE id=?', values + (product_id,))
                db().commit()
                flash('Product updated.', 'success')
                return redirect(url_for('products'))
            except ValueError as error:
                flash(str(error), 'error')
            except sqlite3.IntegrityError:
                db().rollback()
                flash('That SKU already exists.', 'error')
        return render_template('product_form.html', product=product)

    @app.post('/products/<int:product_id>/archive')
    @admin_required
    def archive_product(product_id):
        result = db().execute('UPDATE products SET active=0 WHERE id=? AND quantity=0 AND active=1', (product_id,))
        db().commit()
        flash('Product archived; movement history is preserved.' if result.rowcount else 'Only an active product with zero stock can be archived.', 'success' if result.rowcount else 'error')
        return redirect(url_for('products'))

    @app.route('/stock', methods=['GET', 'POST'])
    @login_required
    def stock():
        if request.method == 'POST':
            try:
                product_id = int(request.form.get('product_id', ''))
                amount = int(request.form.get('amount', ''))
                kind = request.form.get('kind')
                note = request.form.get('note', '').strip()
                if amount <= 0 or amount > 1000000000 or kind not in ('in', 'out') or len(note) > 500:
                    raise ValueError('Enter a positive whole quantity and a note under 500 characters.')
                connection = db()
                connection.execute('BEGIN IMMEDIATE')
                delta = amount if kind == 'in' else -amount
                result = connection.execute('UPDATE products SET quantity=quantity+? WHERE id=? AND active=1 AND quantity+? BETWEEN 0 AND 1000000000', (delta, product_id, delta))
                if result.rowcount != 1:
                    raise ValueError('Stock change rejected: insufficient stock, quantity limit, or unavailable product.')
                balance = connection.execute('SELECT quantity FROM products WHERE id=?', (product_id,)).fetchone()['quantity']
                connection.execute('INSERT INTO movements(product_id,user_id,kind,amount,balance,note) VALUES(?,?,?,?,?,?)', (product_id, g.user['id'], kind, amount, balance, note))
                connection.commit()
                flash('Stock movement recorded.', 'success')
                return redirect(url_for('movements'))
            except ValueError as error:
                db().rollback()
                flash(str(error) or 'Select a product and enter a whole quantity.', 'error')
        rows = db().execute('SELECT * FROM products WHERE active=1 ORDER BY name').fetchall()
        return render_template('stock.html', products=rows, selected=request.args.get('product', ''))

    @app.get('/movements')
    @login_required
    def movements():
        rows = db().execute('SELECT m.*, p.name,p.sku,u.username FROM movements m JOIN products p ON p.id=m.product_id JOIN users u ON u.id=m.user_id ORDER BY m.id DESC').fetchall()
        return render_template('movements.html', movements=rows)

    @app.get('/export/products.csv')
    @login_required
    def export_products():
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(['SKU', 'Product', 'Category', 'Unit price', 'Quantity', 'Reorder level'])
        def safe(value):
            return "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value
        for row in db().execute('SELECT * FROM products WHERE active=1 ORDER BY name'):
            writer.writerow([safe(row['sku']), safe(row['name']), safe(row['category']), '{:.2f}'.format(row['price_cents']/100), row['quantity'], row['threshold']])
        return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=inventory.csv'})

    @app.route('/users', methods=['GET', 'POST'])
    @admin_required
    def users():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role')
            if not 3 <= len(username) <= 40 or len(password) < 8 or role not in ('admin', 'staff'):
                flash('Use a username of 3–40 characters, a password of at least 8 characters, and a valid role.', 'error')
            else:
                try:
                    db().execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', (username, generate_password_hash(password), role))
                    db().commit()
                    flash('User created.', 'success')
                    return redirect(url_for('users'))
                except sqlite3.IntegrityError:
                    db().rollback()
                    flash('That username already exists.', 'error')
        return render_template('users.html', users=db().execute('SELECT id,username,role FROM users ORDER BY username').fetchall())

    @app.cli.command('create-admin')
    @click.option('--username', prompt=True)
    @click.password_option()
    def create_admin(username, password):
        if not 3 <= len(username.strip()) <= 40 or len(password) < 8:
            raise click.ClickException('Username must be 3–40 characters and password at least 8 characters.')
        try:
            db().execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)', (username.strip(), generate_password_hash(password), 'admin'))
            db().commit()
        except sqlite3.IntegrityError:
            raise click.ClickException('Username already exists.')
        click.echo('Administrator created.')

    @app.cli.command('reset-admin-password')
    @click.option('--username', prompt=True)
    def reset_admin_password(username):
        username = username.strip()
        if not 3 <= len(username) <= 40:
            raise click.ClickException('Username must be 3–40 characters.')
        user = db().execute(
            "SELECT id FROM users WHERE username=? AND role='admin'",
            (username,),
        ).fetchone()
        if not user:
            raise click.ClickException('No administrator account exists with that username.')
        password = click.prompt('New password', hide_input=True, confirmation_prompt=True)
        if len(password) < 8:
            raise click.ClickException('Password must be at least 8 characters.')
        db().execute(
            'UPDATE users SET password_hash=? WHERE id=?',
            (generate_password_hash(password), user['id']),
        )
        db().commit()
        click.echo('Administrator password updated.')

    @app.cli.command('seed-demo')
    def seed_demo():
        admin = db().execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1").fetchone()
        if not admin:
            raise click.ClickException('Run create-admin first.')
        if db().execute('SELECT COUNT(*) FROM products').fetchone()[0]:
            raise click.ClickException('Demo seeding requires an empty product database.')
        samples = [('EL-001','Wireless Mouse','Electronics',1899,34,10),('EL-002','USB-C Hub','Electronics',3499,6,8),('ST-001','A5 Notebook','Stationery',499,72,15),('ST-002','Gel Pen Set','Stationery',799,4,10),('OF-001','Desk Organizer','Office',1299,18,5),('EL-003','HDMI Cable','Electronics',999,0,5)]
        for sku, name, category, price, quantity, threshold in samples:
            result = db().execute('INSERT INTO products(sku,name,category,price_cents,quantity,threshold) VALUES(?,?,?,?,?,?)', (sku,name,category,price,quantity,threshold))
            if quantity:
                db().execute("INSERT INTO movements(product_id,user_id,kind,amount,balance,note) VALUES(?,?,'in',?,?,'Opening stock')", (result.lastrowid,admin['id'],quantity,quantity))
        db().commit()
        click.echo('Six demo products added.')

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error_page(error):
        return render_template('error.html', error=error), error.code

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
