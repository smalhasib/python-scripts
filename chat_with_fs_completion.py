import requests
import json
import html2text
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel
from enum import Enum

# --- Configuration from fetch_and_send_tickets.py ---
BASE_URL = "https://support.wpmanageninja.com/wp-json/fluent-support/v2"
USERNAME = "alhasibsm@gmail.com"
PASSWORD = "gjUI NgUH GD1A cnJ4 5w29 YOyy"

# --- Schemas from app/schemas/chat.py ---
class Role(str, Enum):
    AI = "ai"
    HUMAN = "human"
    SUPPORT_AGENT = "support_agent"
    CUSTOMER = "customer"

class Message(BaseModel):
    role: Literal[Role.AI, Role.HUMAN]
    content: str

class TicketConversation(BaseModel):
    role: Literal[Role.SUPPORT_AGENT, Role.CUSTOMER]
    message: str

class FSChatInput(BaseModel):
    messages: list[Message] | None = None
    message: str | None = None
    conversation_id: str | None = None
    bot_id: UUID
    stream: bool = False
    ticket_conversation: list[TicketConversation]

# --- Functions from fetch_and_send_tickets.py (adapted) ---
def fetch_ticket_details(ticket_id):
    """Fetches details for a specific ticket ID."""
    try:
        response = requests.get(f"{BASE_URL}/tickets/{ticket_id}", auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching ticket details for ID {ticket_id}: {e}")
        return None

def format_conversation_to_ticket_conversation(ticket_data) -> List[TicketConversation]:
    """Formats ticket conversation into a list of TicketConversation objects."""
    conversation_list = []
    if not ticket_data or 'ticket' not in ticket_data:
        return conversation_list

    ticket = ticket_data['ticket']

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

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0 # Disable line wrapping

    for part in conversation_parts:
        role = Role.CUSTOMER if part['person_type'] == 'customer' else Role.SUPPORT_AGENT
        message_content = h.handle(part['content']).strip()
        if message_content:
            conversation_list.append(TicketConversation(role=role, message=message_content))

    return conversation_list


def chat_loop():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    ticket_id = None
    while ticket_id is None:
        try:
            ticket_id_input = input("Please enter the ticket ID (e.g., 12345): ")
            ticket_id = int(ticket_id_input)
        except ValueError:
            print("Invalid ticket ID. Please enter a number.")
            logging.error("Invalid ticket ID entered.")
    bot_id = UUID("872a1710-58c1-46a7-a22d-b46eb9b5de4b") # Replace with your actual bot ID

    logging.info(f"Fetching details for ticket ID: {ticket_id}")
    ticket_details = fetch_ticket_details(ticket_id)

    if not ticket_details:
        logging.error(f"Could not fetch details for ticket {ticket_id}. Exiting.")
        return

    ticket_conversation = format_conversation_to_ticket_conversation(ticket_details)
    if not ticket_conversation:
        logging.warning(f"No conversation found for ticket {ticket_id}. Chat will proceed without ticket context.")

    conversation_id = None # For stateful chat

    print(f"\n--- Chatting with FS Completion for Ticket {ticket_id} ---")
    print("Type 'exit' to end the chat.")

    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            break

        try:
            chat_input_data = FSChatInput(
                message=user_message,
                bot_id=bot_id,
                stream=True,
                ticket_conversation=ticket_conversation,
                conversation_id=conversation_id
            )

            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                'http://localhost:8000/chat/fs-completion',
                json=chat_input_data.model_dump(exclude_none=True),
                headers=headers,
                stream=True
            )
            response.raise_for_status()

            print("AI: ", end="")
            full_response_content = ""
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    try:
                        # Each chunk might contain multiple SSE data blocks
                        for line in chunk.decode('utf-8').splitlines():
                            if line.startswith('data: '):
                                json_data = json.loads(line[len('data: '):])
                                if 'response' in json_data:
                                    print(json_data['response'], end="")
                                    full_response_content += json_data['response']
                                if 'conversation_id' in json_data and conversation_id is None:
                                    conversation_id = json_data['conversation_id']
                                    logging.info(f"New conversation ID: {conversation_id}")
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON decode error: {e} in chunk: {chunk.decode('utf-8')}")
                        print(f"[Error decoding AI response: {e}]")
            print()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error during chat completion: {e}")
            print(f"Error: Could not get response from AI. {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            print(f"An unexpected error occurred: {e}")

    logging.info("Chat session ended.")

if __name__ == "__main__":
    from enum import Enum # Moved here to avoid circular import if Role is used elsewhere
    chat_loop()