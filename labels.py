import json
import os
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import datetime as dt

# Configure logging
logging.basicConfig(
    filename=f'count_{dt.datetime.now().strftime("%Y%m%d%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

last_timestamp = None
last_count = None
json_file = "count.json"

def append_data_to_json(entries: List[Dict[str, int]]) -> None:
    file_exists = os.path.exists(json_file)
    
    if file_exists:
        with open(json_file, 'r+') as file:
            data = json.load(file)
            data_dict = {k: v for d in data for k, v in d.items()}  # Convert to dictionary to handle duplicates
            for entry in entries:
                data_dict.update(entry)  # Overwrite any existing entries with the same timestamp
            data = [{k: v} for k, v in data_dict.items()]  # Convert back to list of dictionaries
            file.seek(0)
            json.dump(data, file, indent=2)
            file.truncate()  # Remove any leftover data
    else:
        with open(json_file, 'w') as file:
            json.dump(entries, file, indent=2)

    logging.info(f"Appended data to {json_file}")

def validate_input(user_input: str) -> bool:
    return user_input.isdigit() and int(user_input) >= 0

def get_nearest_valid_timestamp(current_time: datetime, frequency: int) -> datetime:
    seconds = current_time.second
    nearest_second = (seconds // frequency) * frequency
    if seconds % frequency >= frequency / 2:
        nearest_second += frequency

    nearest_second = min(59, nearest_second)
    adjusted_time = current_time.replace(second=nearest_second, microsecond=0)
    return adjusted_time

def fill_missing_timestamps(
    last_time: datetime, 
    current_time: datetime, 
    fill_value: int, 
    frequency: int
) -> List[Dict[str, int]]:
    entries = []
    time_step = timedelta(seconds=frequency)
    
    while last_time + time_step < current_time:
        last_time += time_step
        entries.append({last_time.strftime('%Y-%m-%d %H:%M:%S'): fill_value})

    return entries

def run(frequency: int):
    global last_timestamp, last_count
    while True:
        user_input = input("Enter number of people in the room: ")
        current_time = datetime.now()

        if validate_input(user_input):
            nearest_time = get_nearest_valid_timestamp(current_time, frequency)
            logging.info(f"User input: {user_input}, Time: {nearest_time}, Status: OK")
        else:
            logging.info(f"User input: {user_input}, Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}, Status: IGNORED")
            print("Invalid input, ignored.")
            continue

        user_input = int(user_input)
        new_entry = [{nearest_time.strftime('%Y-%m-%d %H:%M:%S'): user_input}]
        
        if last_timestamp is not None and nearest_time > last_timestamp:
            filled_entries = fill_missing_timestamps(last_timestamp, nearest_time, last_count, frequency)
            new_entry = filled_entries + new_entry

        append_data_to_json(new_entry)
        last_timestamp = nearest_time
        last_count = user_input

if __name__ == "__main__":
    logging.info("Program started.")
    try:
        run(frequency=1)
    except KeyboardInterrupt:
        logging.info("Program interrupted by the user.")
        print("\nProgram terminated.")