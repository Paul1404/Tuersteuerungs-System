import time
import sqlite3

# Define GPIO pins
RELAY_PIN = 17  # Pin where the relay is connected
RFID_PIN = 27  # Pin where the RFID reader is connected

USE_MOCK = True  # Set to False when running on actual Raspberry Pi with hardware


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
        # Simulate a tag scan by pressing Enter
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
    """Main loop that checks for RFID input and unlocks the door if authorized."""
    try:
        while True:
            if rfid_reader.is_pressed:  # If RFID tag is detected
                # TODO: Uncomment and implement the following lines when ready
                # tag_id = read_rfid()  # Function to read the RFID tag ID
                # if is_authorized(tag_id):  # Check the database
                unlock_door()
            time.sleep(0.1)  # Short pause to reduce CPU usage
    except KeyboardInterrupt:
        pass  # GPIOZero automatically handles cleanup if using real library



if __name__ == '__main__':
    main()
