import csv
import requests

CSV_FILE_PATH = '/Users/smalhasib/Work/python-scripts/.inputs/deletion-keys.csv'
BASE_URL = 'http://localhost:8000/document/'
COLLECTION_NAME = '872a1710-58c1-46a7-a22d-b46eb9b5de4b'

def delete_keys_from_csv(csv_file_path):
    """
    Reads keys from a CSV file and sends DELETE requests for each key.
    """
    try:
        with open(csv_file_path, mode='r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip header row
            if 'key' not in header:
                print(f"Error: CSV file '{csv_file_path}' does not contain a 'key' column.")
                return
            key_index = header.index('key')

            for row in reader:
                if row:
                    key = row[key_index].strip().strip('"') # Remove any leading/trailing whitespace or quotes
                    if key:
                        url = f"{BASE_URL}{key}?collection_name={COLLECTION_NAME}"
                        print(f"Attempting to delete key: {key} from URL: {url}")
                        try:
                            response = requests.delete(url)
                            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                            print(f"Successfully deleted key {key}. Status Code: {response.status_code}")
                        except requests.exceptions.HTTPError as http_err:
                            print(f"HTTP error occurred for key {key}: {http_err}")
                        except requests.exceptions.ConnectionError as conn_err:
                            print(f"Connection error occurred for key {key}: {conn_err}")
                        except requests.exceptions.Timeout as timeout_err:
                            print(f"Timeout error occurred for key {key}: {timeout_err}")
                        except requests.exceptions.RequestException as req_err:
                            print(f"An unexpected error occurred for key {key}: {req_err}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at '{csv_file_path}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    delete_keys_from_csv(CSV_FILE_PATH)