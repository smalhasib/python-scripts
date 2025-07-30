import requests
import os
import re
import logging

def extract_article_from_url(url):
    try:
        api_url = f"http://localhost:4000/scrape?url={url}"
        response = requests.get(api_url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        title = data.get('title', 'No Title')
        content = data.get('content', '')

        # The content from the API is expected to be already in Markdown format
        # Post-process markdown to change image format from ![Alt Text](URL) to ! URL
        # This regex finds ![anything](URL) and replaces it with ! URL
        processed_content = re.sub(r'!\\[.*?\\]\\((.*?)\\)', r'! \1', content)

        return {'title': title, 'markdown': processed_content}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from API for URL {url}: {e}")
        return None
    except ValueError as e:
        print(f"Error decoding JSON response for URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Error extracting article from {url}: {e}")
        return None

def main():
    urls_file = ".outputs/extracted_fluentform_docs_urls.txt"
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f".logs/extraction_and_sending_log_{timestamp}.log"

    # Configure logging
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logging.error(f"Error: {urls_file} not found.")
        return

    # Process all URLs
    for i, url in enumerate(urls):
        logging.info(f"Processing URL {i+1}/{len(urls)}: {url}")
        article_data = extract_article_from_url(url)
        if article_data:
            # Prepare payload for API
            payload = {
                'collection_name': '714220f8-f9ee-4470-9382-bb44a40182b9', # This ID is from post_data.py
                'content': article_data['markdown'],
                'metadata': {
                    'title': article_data['title'],
                    'source': url,
                    'visibility': 'public'
                },
            }

            # Post data to the API endpoint
            api_endpoint = 'http://beta.fluentbot.ai:8100/document/'
            try:
                response = requests.post(api_endpoint, json=payload)
                response.raise_for_status()  # Raise an exception for bad status codes
                logging.info(f"Successfully posted data from {url}. Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error posting data from {url}: {e}")
        else:
            logging.warning(f"Failed to extract article from {url}")

if __name__ == "__main__":
    main()