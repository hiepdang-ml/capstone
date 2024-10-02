import CoreWLAN
import datetime as dt
import time
import json
import os
import signal
import sys
import logging


# Configure logging
logging.basicConfig(
    filename=f'rssi_{dt.datetime.now().strftime("%Y%m%d%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def init(file_path):
    """Initialize the JSON file by creating an opening bracket for the array."""
    with open(file_path, 'w') as file:
        file.write('[')  # Start the JSON array
    logging.info(f"Initialized JSON file: {file_path}")


def append_record(file_path, record):
    """Append a single record to the JSON file without loading the entire file."""
    # Check if file size is greater than 1 byte to determine if it's the first record
    with open(file_path, 'a+') as file:
        file.seek(0, os.SEEK_END)
        # Add a comma before appending new record (if it's not the first record)
        if file.tell() > 1:
            file.write(',')
        
        json.dump(record, file, indent=2)
        file.write('\n')
    logging.info(f"Appended new record to JSON file: {file_path}")


def finalize(file_path):
    """Add the closing bracket to finalize the JSON array."""
    with open(file_path, 'a') as file:
        file.write(']')  # End the JSON array
    logging.info(f"Finalized and closed JSON file: {file_path}")


def handle_signal(signal_number, frame):
    """Handle termination signals to finalize the file before exiting."""
    logging.info(f"Received signal {signal_number}. Finalizing and closing the JSON file...")
    finalize('rssi.json')
    sys.exit(0)


def run(frequency: float = 2, file_path='rssi.json'):
    """Run the process to record RSSI every 'frequency' seconds."""
    wifi_interface = CoreWLAN.CWWiFiClient.sharedWiFiClient().interface()

    logging.info("Starting RSSI recording...")

    while True:
        now = dt.datetime.now()

        # Check if the current second is aligned with the frequency (e.g., 5, 10, 15 seconds, etc.)
        if now.second % frequency == 0:
            time_string: str = now.strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"Start recording at: {time_string}")
            record = {}

            try:
                networks, _ = wifi_interface.scanForNetworksWithName_error_(None, None)
                record[time_string] = []
                for i, network in enumerate(networks, start=1):
                    record[time_string].append({
                        'id': i, 'ssid': network.ssid(), 'bssid': network.bssid(), 'rssi': network.rssiValue()
                    })

                # Append the new record directly to the file
                append_record(file_path, record)

            except Exception as e:
                logging.error(f"Error during Wi-Fi scan: {e}")

            # Sleep for a while to avoid multiple triggers within the same second
            time.sleep(1)
        else:
            # Sleep for a short time before checking again
            time.sleep(0.1)


if __name__ == '__main__':
    json_file = 'rssi.json'
    
    # Initialize the file
    init(json_file)

    # Register signal handlers to catch termination signals
    signal.signal(signal.SIGTERM, handle_signal)  # Handle process kill
    signal.signal(signal.SIGINT, handle_signal)   # Handle interrupt (Ctrl+C)

    try:
        run(frequency=1, file_path=json_file)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        finalize(json_file)


