"""Create a non-destructive local administrator used only for capturing demo screens."""
import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect('instance/inventory.sqlite')
connection.execute(
    'INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)',
    ('demo-recorder', generate_password_hash('DemoPass123!'), 'admin'),
)
connection.commit()
connection.close()
print('Demo account ready: demo-recorder')
