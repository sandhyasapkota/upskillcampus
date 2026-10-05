import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.temp.name) / 'test.sqlite')
        self.app = create_app({'TESTING': True, 'DATABASE': self.database, 'SECRET_KEY': 'test-key'})
        self.client = self.app.test_client()
        with self.connection() as db:
            db.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,'admin')", ('admin', generate_password_hash('testpass123')))
            db.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,'staff')", ('staff', generate_password_hash('testpass123')))
            db.execute("INSERT INTO products(sku,name,category,price_cents,threshold) VALUES('SKU-1','Test product','Office',1250,5)")

    def tearDown(self):
        self.temp.cleanup()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.database)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def post(self, path, data=None, follow_redirects=False):
        self.client.get('/login')
        with self.client.session_transaction() as session:
            token = session['csrf']
        return self.client.post(path, data=dict(data or {}, csrf_token=token), follow_redirects=follow_redirects)

    def login(self, username='admin'):
        return self.post('/login', {'username': username, 'password': 'testpass123'})

    def test_login_and_authentication(self):
        self.assertEqual(self.client.get('/products').status_code, 302)
        response = self.post('/login', {'username': 'admin', 'password': 'wrong'})
        self.assertIn(b'Incorrect username', response.data)
        self.assertEqual(self.login().status_code, 302)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.post('/logout')
        self.assertEqual(self.client.get('/').status_code, 302)

    def test_staff_permissions(self):
        self.login('staff')
        for path in ['/users', '/products/new', '/products/1/edit']:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.post('/products/1/archive').status_code, 403)
        for path in ['/', '/products', '/stock', '/movements', '/export/products.csv']:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_movements_and_rejected_overdraw(self):
        self.login('staff')
        self.assertEqual(self.post('/stock', {'product_id': 1, 'kind': 'in', 'amount': 10, 'note': 'Delivery'}).status_code, 302)
        self.assertEqual(self.post('/stock', {'product_id': 1, 'kind': 'out', 'amount': 7}).status_code, 302)
        response = self.post('/stock', {'product_id': 1, 'kind': 'out', 'amount': 4})
        self.assertIn(b'insufficient stock', response.data)
        for amount in ['-1', '0', '1.5', 'bad']:
            self.post('/stock', {'product_id': 1, 'kind': 'in', 'amount': amount})
        with self.connection() as db:
            self.assertEqual(db.execute('SELECT quantity FROM products').fetchone()[0], 3)
            self.assertEqual(db.execute('SELECT amount,balance FROM movements ORDER BY id').fetchall(), [(10,10),(7,3)])
        self.assertIn(b'Test product', self.client.get('/products?low=1').data)
        self.assertIn(b'Delivery', self.client.get('/movements').data)

    def test_product_validation_edit_archive_and_history(self):
        self.login()
        values = {'sku':'NEW-1','name':'New product','category':'Office','price':'12.34','threshold':'4'}
        self.assertEqual(self.post('/products/new', values).status_code, 302)
        self.assertIn(b'already exists', self.post('/products/new', values).data)
        self.assertEqual(self.post('/products/2/edit', dict(values, name='Updated')).status_code, 302)
        self.assertIn(b'Updated', self.client.get('/products?q=NEW-1').data)
        for price in ['NaN', '-1', '1.234', 'Infinity']:
            self.assertIn(b'valid price', self.post('/products/new', dict(values, sku='BAD', price=price)).data)
        self.post('/stock', {'product_id': 1, 'kind': 'in', 'amount': 2})
        self.assertIn(b'zero stock', self.post('/products/1/archive', follow_redirects=True).data)
        self.post('/stock', {'product_id': 1, 'kind': 'out', 'amount': 2})
        self.post('/products/1/archive')
        self.assertNotIn(b'Test product', self.client.get('/products').data)
        self.assertIn(b'Test product', self.client.get('/movements').data)
        self.assertIn(b'unavailable product', self.post('/stock', {'product_id': 1, 'kind': 'in', 'amount': 1}).data)

    def test_csrf_user_creation_csv_and_templates(self):
        self.login()
        self.assertEqual(self.client.post('/products/new', data={}).status_code, 400)
        self.assertEqual(self.post('/users', {'username':'newstaff','password':'longpassword','role':'staff'}).status_code, 302)
        self.assertIn(b'already exists', self.post('/users', {'username':'newstaff','password':'longpassword','role':'staff'}).data)
        self.assertIn(b'valid role', self.post('/users', {'username':'newstaff','password':'longpassword','role':'owner'}).data)
        self.post('/products/new', {'sku':'FORMULA','name':'=1+1','category':'Office','price':'1','threshold':'0'})
        csv = self.client.get('/export/products.csv')
        self.assertIn(b"'=1+1", csv.data)
        self.assertIn('attachment', csv.headers['Content-Disposition'])
        for path in ['/', '/products', '/products/new', '/products/1/edit', '/stock', '/movements', '/users']:
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get('/products/999/edit').status_code, 404)

    def test_cli(self):
        runner = self.app.test_cli_runner()
        result = runner.invoke(args=['create-admin', '--username', 'secondadmin', '--password', 'longpassword'])
        self.assertEqual(result.exit_code, 0, result.output)
        result = runner.invoke(
            args=['reset-admin-password', '--username', 'admin'],
            input='newpassword\nnewpassword\n',
        )
        self.assertEqual(result.exit_code, 0, result.output)
        with self.connection() as db:
            password_hash = db.execute(
                "SELECT password_hash FROM users WHERE username='admin'"
            ).fetchone()[0]
        from werkzeug.security import check_password_hash
        self.assertTrue(check_password_hash(password_hash, 'newpassword'))
        result = runner.invoke(
            args=['reset-admin-password', '--username', 'staff'],
            input='newpassword\nnewpassword\n',
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('No administrator account', result.output)
        self.assertNotEqual(runner.invoke(args=['seed-demo']).exit_code, 0)
        with self.connection() as db:
            db.execute('DELETE FROM products')
        result = runner.invoke(args=['seed-demo'])
        self.assertEqual(result.exit_code, 0, result.output)
        with self.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM products').fetchone()[0], 6)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM movements').fetchone()[0], 5)


if __name__ == '__main__':
    unittest.main()
