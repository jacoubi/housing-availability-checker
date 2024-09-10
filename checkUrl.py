import os
import requests
from bs4 import BeautifulSoup
import logging
import json

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token and Chat ID (set these in environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# File to store the state
STATE_FILE = 'housing_state.json'

def read_urls_from_file(filename):
    urls = {}
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith('Fetched address for'):
                url, address = line.strip().split(': ', 1)
                url = url.replace('Fetched address for ', '')
                urls[url] = address
    return urls

URLS_TO_CHECK = read_urls_from_file('ile_de_france_addresses.txt')

def is_housing_available(html_content, url):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for the button
    button = soup.find('button', class_='svelte-eq6rxe fr-btn')
    if button:
        logger.info(f"Found button for {url}: title='{button.get('title')}', text='{button.text.strip()}'")
        if button.get('title') == "Ajouter à ma sélection" or "Ajouter" in button.text:
            return True
        elif button.get('title') == "Indisponible" or "Indisponible" in button.text:
            return False
    
    # Check for the span
    span = soup.find('span', class_='svelte-eq6rxe')
    if span:
        logger.info(f"Found span for {url}: text='{span.text.strip()}'")
        if "Ajouter" in span.text:
            return True
        elif "Indisponible" in span.text:
            return False
    
    # Check for availability in JSON data
    scripts = soup.find_all('script', type='application/json')
    for script in scripts:
        if 'available' in script.string:
            logger.info(f"Found JSON data for {url}: {script.string}")
            if '"available":true' in script.string:
                return True
            elif '"available":false' in script.string:
                return False
    
    logger.warning(f"Could not determine availability for {url}")
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"Failed to send Telegram message: {response.text}")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def check_availability():
    previous_state = load_state()
    current_state = {}
    changes = []

    for url, address in URLS_TO_CHECK.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            is_available = is_housing_available(response.text, url)
            
            current_state[url] = is_available
            
            if url not in previous_state:
                if is_available:
                    changes.append(f"New listing available: {address}\nURL: {url}")
            elif is_available != previous_state[url]:
                if is_available:
                    changes.append(f"Now available: {address}\nURL: {url}")
                else:
                    changes.append(f"No longer available: {address}\nURL: {url}")
            
            logger.info(f"Checked {url}: {'Available' if is_available else 'Not available'}")
        except requests.RequestException as e:
            logger.error(f"Error checking {url}: {str(e)}")
            current_state[url] = previous_state.get(url)

    save_state(current_state)

    if changes:
        message = "Housing Availability Updates:\n\n" + "\n\n".join(changes)
        send_telegram_message(message)
        logger.info("Sent update message")
    else:
        logger.info("No changes in availability")

def main():
    logger.info("Starting housing availability check")
    check_availability()
    logger.info("Finished housing availability check")

if __name__ == '__main__':
    main()
