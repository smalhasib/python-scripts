import requests
import json
import html2text
import logging
import os
from datetime import datetime

BASE_URL = "https://support.wpmanageninja.com/wp-json/fluent-support/v2"
USERNAME = "alhasibsm@gmail.com"
PASSWORD = "gjUI NgUH GD1A cnJ4 5w29 YOyy"

def fetch_ticket_ids(page=1, per_page=5, tag_id=37, product_id=1):
    """Fetches ticket IDs from the paginated API."""
    params = {
        "page": page,
        "per_page": per_page,
        "filter_type": "simple",
        "filters[ticket_tags][]": tag_id,
        "filters[product_id]": product_id
    }
    try:
        response = requests.get(f"{BASE_URL}/tickets", params=params, auth=(USERNAME, PASSWORD))
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ticket IDs: {e}")
        return None

def fetch_ticket_details(ticket_id):
    """Fetches details for a specific ticket ID."""
    try:
        response = requests.get(f"{BASE_URL}/tickets/{ticket_id}", auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ticket details for ID {ticket_id}: {e}")
        return None

def format_conversation_to_markdown(ticket_data):
    """Formats ticket conversation into a Markdown document."""
    if not ticket_data or 'ticket' not in ticket_data:
        return ""

    ticket = ticket_data['ticket']
    markdown_doc = f"# Ticket: {ticket.get('title', 'N/A')} (ID: {ticket.get('id', 'N/A')})\n\n"
    markdown_doc += f"**Created At:** {ticket.get('created_at', 'N/A')}\n"
    markdown_doc += f"**Status:** {ticket.get('status', 'N/A')}\n"
    markdown_doc += f"**Customer:** {ticket['customer'].get('full_name', 'N/A')} ({ticket['customer'].get('email', 'N/A')})\n"
    markdown_doc += f"**Agent:** {ticket['agent'].get('full_name', 'N/A')} ({ticket['agent'].get('email', 'N/A')})\n\n"

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0 # Disable line wrapping

    # Collect all conversation parts (initial message and responses)
    conversation_parts = []

    # Add initial message to conversation parts for sorting
    if ticket.get('content'):
        conversation_parts.append({
            'created_at': ticket.get('created_at'),
            'content': ticket['content'],
            'person_type': 'customer',
            'full_name': ticket['customer'].get('full_name', 'N/A'),
            'email': ticket['customer'].get('email', 'N/A')
        })

    # Add responses to conversation parts
    if 'responses' in ticket and ticket['responses']:
        for response in ticket['responses']:
            conversation_parts.append({
                'created_at': response.get('created_at'),
                'content': response.get('content'),
                'person_type': response.get('person', {}).get('person_type', 'N/A'),
                'full_name': response.get('person', {}).get('full_name', 'Unknown'),
                'email': response.get('person', {}).get('email', 'N/A')
            })

    # Sort conversation parts by timestamp
    conversation_parts.sort(key=lambda x: x.get('created_at', ''))

    markdown_doc += "## Conversation History\n\n"
    for part in conversation_parts:
        if part['person_type'] == 'customer':
            markdown_doc += f"### From: Customer\n"
        else:
            markdown_doc += f"### From: Agent\n"
        markdown_doc += h.handle(part['content']) + "\n\n"

    return markdown_doc

def send_to_localhost(markdown_content, title, source_url):
    payload = {
        'collection_name': '872a1710-58c1-46a7-a22d-b46eb9b5de4b',
        'content': markdown_content,
        'metadata': {
            'title': title,
            'source': source_url,
            'visibility': 'private'
        },
    }
    api_endpoint = 'http://localhost:8000/document/'
    try:
        response = requests.post(api_endpoint, json=payload)
        response.raise_for_status()
        logging.info(f"Successfully posted data for {title}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error posting data for {title}: {e}")

def main():
        # Configure logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f".logs/fetch_and_send_tickets_log_{timestamp}.log"
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


    all_ticket_ids = []
    page = 1
    per_page = 50
    last_page = 1 # Initialize to 1 to enter the loop

    while page <= last_page:
        logging.info(f"Fetching ticket IDs from page {page}...")
        data = fetch_ticket_ids(page=page, per_page=per_page) # Fetch 5 per page to get more IDs faster
        if data and 'tickets' in data:
            tickets_data = data['tickets']
            last_page = tickets_data.get('last_page', 1)
            for ticket_info in tickets_data.get('data', []):
                all_ticket_ids.append(ticket_info['id'])
            page += 1
        else:
            logging.warning("Could not fetch ticket IDs or no tickets found.")
            break

    logging.info(f"Found {len(all_ticket_ids)} ticket IDs: {all_ticket_ids}")

    for i, ticket_id in enumerate(all_ticket_ids):
        logging.info(f"Fetching details for ticket ID: {ticket_id}")
        ticket_details = fetch_ticket_details(ticket_id)
        if ticket_details:
            markdown_content = format_conversation_to_markdown(ticket_details)
            # Removed file saving logic as requested
            # output_filename = os.path.join(output_dir, f"ticket_{ticket_id}.md")
            # with open(output_filename, "w", encoding="utf-8") as f:
            #     f.write(markdown_content)
            # logging.info(f"Saved conversation for ticket {ticket_id} to {output_filename}")

            # Send to localhost:8000
            ticket_title = ticket_details['ticket'].get('title', f'Ticket {ticket_id}')
            ticket_url = f"{BASE_URL}/tickets/{ticket_id}" # Construct a URL for the ticket
            send_to_localhost(markdown_content, ticket_title, ticket_url)

        else:
            logging.warning(f"Failed to fetch details for ticket {ticket_id}.")

    logging.info("\nProcess complete. Markdown documents sent to localhost:8000.")

if __name__ == "__main__":
    main()