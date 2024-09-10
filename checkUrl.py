import os
import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token (set this in Heroku Config Vars)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Telegram Chat ID (set this in Heroku Config Vars)
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

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

def is_housing_available(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    button = soup.find('button', class_='svelte-eq6rxe fr-btn')
    
    if button:
        if button['title'] == "Ajouter à ma sélection":
            return True
        elif button['title'] == "Indisponible":
            return False
    
    span = soup.find('span', class_='svelte-eq6rxe')
    if span:
        return span.text.strip() == "Ajouter à ma sélection"
    
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload)

def check_availability():
    for url, address in URLS_TO_CHECK.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            is_available = is_housing_available(response.text)
            
            if is_available:
                message = f"Housing is now available at: {address}\nURL: {url}"
                send_telegram_message(message)
                logger.info(message)
            elif is_available is False:
                logger.info(f"Housing is not available at: {address}")
            else:
                logger.warning(f"Could not determine availability for: {address}")
        except requests.RequestException as e:
            logger.error(f"Error checking {url}: {str(e)}")

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Housing availability checker is running. You will be notified when housing becomes available.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    
    while True:
        check_availability()

if __name__ == '__main__':
    main()