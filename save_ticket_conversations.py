import requests
import json
import logging
import os
from datetime import datetime
import html2text

BASE_URL = "https://support.wpmanageninja.com/wp-json/fluent-support/v2"
USERNAME = "alhasibsm@gmail.com"
PASSWORD = "gjUI NgUH GD1A cnJ4 5w29 YOyy"

def fetch_ticket_details(ticket_id):
    """Fetches details for a specific ticket ID."""
    try:
        response = requests.get(f"{BASE_URL}/tickets/{ticket_id}", auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ticket details for ID {ticket_id}: {e}")
        return None

def format_conversation_to_json(ticket_data):
    """Formats ticket conversation into a JSON array of role and content."""
    if not ticket_data or 'ticket' not in ticket_data:
        return []

    ticket = ticket_data['ticket']
    conversation_json = []

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0 # Disable line wrapping

    # Add initial message
    if ticket.get('content'):
        conversation_json.append({
            'role': 'customer',
            'message': h.handle(ticket['content'])
        })

    # Add responses
    if 'responses' in ticket and ticket['responses']:
        for response in ticket['responses']:
            role = 'agent' if response.get('person', {}).get('person_type') == 'agent' else 'customer'
            conversation_json.append({
                'role': role,
                'message': h.handle(response.get('content', ''))
            })
    
    # Sort conversation parts by timestamp (assuming 'created_at' is available in responses)
    # For simplicity, this example assumes responses are already ordered or order doesn't strictly matter for JSON output.
    # If strict chronological order is needed, more complex sorting based on 'created_at' for both initial ticket and responses would be required.
    
    return conversation_json

import sys

def main():
    # Configure logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f".logs/save_ticket_conversations_log_{timestamp}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    output_dir = ".outputs"
    os.makedirs(output_dir, exist_ok=True)

    if len(sys.argv) > 1:
        ticket_id = sys.argv[1]
        try:
            ticket_id = int(ticket_id)
        except ValueError:
            logging.error(f"Invalid ticket ID provided: {sys.argv[1]}. Please provide an integer.")
            sys.exit(1)

        logging.info(f"Fetching details for single ticket ID: {ticket_id}")
        ticket_details = fetch_ticket_details(ticket_id)
        if ticket_details:
            conversation_json = format_conversation_to_json(ticket_details)
            output_filename = os.path.join(output_dir, f"ticket_conversation_{ticket_id}.json")
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(conversation_json, f, indent=4)
            logging.info(f"Saved conversation for ticket {ticket_id} to {output_filename}")
        else:
            logging.warning(f"Failed to fetch details for ticket {ticket_id}.")


    logging.info("\nProcess complete. JSON documents saved.")

if __name__ == "__main__":
    main()