import json
import requests

def post_data_from_json(file_path, api_endpoint):
    """
    Parses data from a JSON file and posts it to a specified API endpoint.

    Args:
        file_path (str): The path to the JSON file.
        api_endpoint (str): The URL of the API endpoint.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file at {file_path}.")
        return

    for item in data:
        if 'title' in item and 'content' in item and 'website_url' in item:
            payload = {
                'collection_name': '872a1710-58c1-46a7-a22d-b46eb9b5de4b',
                'content': item['content'],
                'metadata': {
                'title': item['title'],
                'source': item['website_url']
                },
            }
            try:
                response = requests.post(api_endpoint, json=payload)
                response.raise_for_status()  # Raise an exception for bad status codes
                print(f"Successfully posted data from {item['website_url']}. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error posting data from {item['website_url']}: {e}")
        else:
            print(f"Skipping item due to missing 'content' or 'website_url': {item.get('id', 'N/A')}")

if __name__ == "__main__":
    JSON_FILE_PATH = '.outputs/fluentcrm_docs.json'
    API_ENDPOINT = 'http://localhost:8000/document/'
    post_data_from_json(JSON_FILE_PATH, API_ENDPOINT)
