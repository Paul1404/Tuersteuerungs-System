from gpiozero import OutputDevice, Button
from mfrc522 import SimpleMFRC522
import time
import sqlite3

# Define GPIO pins
RELAY_PIN = 17  # Pin where the relay is connected
RFID_PIN = 27  # Pin where the RFID reader is connected

relay = OutputDevice(RELAY_PIN)
rfid_reader = Button(RFID_PIN)


def read_rfid():
    reader = SimpleMFRC522()

    try:
        id, text = reader.read()
        return id
    finally:
        GPIO.cleanup()


def unlock_door():
    """Activate the relay to unlock the door for 3 seconds."""
    relay.on()
    time.sleep(3)
    relay.off()


def initialize_database():
    """Set up the SQLite database and create the tags table if it doesn't exist."""
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            tag_value TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()


def add_tag(tag_value):
    """Add a tag value to the database."""
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO tags (tag_value) VALUES (?)', (tag_value,))

    conn.commit()
    conn.close()


def remove_tag(tag_value):
    """Remove a tag value from the database."""
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tags WHERE tag_value = ?', (tag_value,))

    conn.commit()
    conn.close()


def is_authorized(tag_value):
    """Check if a given tag value is authorized (exists in the database)."""
    conn = sqlite3.connect('authorized_tags.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tags WHERE tag_value = ?', (tag_value,))
    result = cursor.fetchone()

    conn.close()

    return result is not None


def main():
    try:
        while True:
            print("Hold a tag near the reader")
            tag_id = read_rfid()  # This function will block until a tag is read
            if is_authorized(tag_id):  # Check the database
                unlock_door()
            time.sleep(0.1)  # Short pause to reduce CPU usage
    except KeyboardInterrupt:
        pass  # GPIOZero automatically handles cleanup



if __name__ == '__main__':
    main()
