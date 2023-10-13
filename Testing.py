import time
import sqlite3
import unittest
from unittest.mock import patch

# Define GPIO pins
RELAY_PIN = 17
RFID_PIN = 27
USE_MOCK = True
CURRENT_MODULE = __name__

# Mocked version of GPiOZero classes for testing
class MockOutputDevice:
    def __init__(self, pin):
        self.pin = pin

    def on(self):
        print(f"Mocked relay (pin {self.pin}) turned ON")

    def off(self):
        print(f"Mocked relay (pin {self.pin}) turned OFF")

class MockButton:
    def __init__(self, pin):
        self.pin = pin

    @property
    def is_pressed(self):
        input("Press Enter to simulate RFID scan...")
        return True

if USE_MOCK:
    relay = MockOutputDevice(RELAY_PIN)
    rfid_reader = MockButton(RFID_PIN)
else:
    from gpiozero import OutputDevice, Button
    relay = OutputDevice(RELAY_PIN)
    rfid_reader = Button(RFID_PIN)

def unlock_door():
    relay.on()
    time.sleep(3)
    relay.off()

def initialize_database():
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            tag_value TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def add_tag(tag_value, conn=None):
    if conn is None:
        conn = sqlite3.connect('authorized_tags.db')
        close_connection = True
    else:
        close_connection = False

    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO tags (tag_value) VALUES (?)', (tag_value,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Tag already exists; we can choose to pass, raise a custom exception, or log it.
        pass

    if close_connection:
        conn.close()



def remove_tag(tag_value):
    initialize_database()
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tags WHERE tag_value = ?', (tag_value,))
    conn.commit()
    conn.close()

def is_authorized(tag_value):
    initialize_database()
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tags WHERE tag_value = ?', (tag_value,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mock_read_rfid():
    return "1234567890ABCDEF"

def main():
    try:
        while True:
            if rfid_reader.is_pressed:
                tag_id = mock_read_rfid()
                if is_authorized(tag_id):
                    unlock_door()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

class RFIDTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY,
                tag_value TEXT NOT NULL UNIQUE
            )
        ''')
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_add_tag(self):
        add_tag("TEST_TAG", conn=self.conn)
        self.cursor.execute('SELECT * FROM tags WHERE tag_value = ?', ("TEST_TAG",))
        result = self.cursor.fetchone()
        self.assertIsNotNone(result)

    def test_remove_tag(self):
        add_tag("TEST_TAG")
        remove_tag("TEST_TAG")
        self.cursor.execute('SELECT * FROM tags WHERE tag_value = ?', ("TEST_TAG",))
        result = self.cursor.fetchone()
        self.assertIsNone(result)

    def test_is_authorized(self):
        add_tag("TEST_TAG")
        self.assertTrue(is_authorized("TEST_TAG"))
        self.assertFalse(is_authorized("NON_EXISTENT_TAG"))

    class CallCounter:
        def __init__(self, limit):
            self.count = 0
            self.limit = limit

        def __call__(self, *args, **kwargs):
            if self.count >= self.limit:
                raise KeyboardInterrupt
            self.count += 1
            return "1234567890ABCDEF"

    @patch('builtins.input', return_value="")
    @patch(f'{CURRENT_MODULE}.mock_read_rfid', return_value="1234567890ABCDEF")  # explicitly set return value here
    def test_main_loop(self, mock_input, mock_read_rfid_function):
        add_tag("1234567890ABCDEF")
        main()


if __name__ == '__main__':
    unittest.main()
