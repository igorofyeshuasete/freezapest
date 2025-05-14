import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import logging

class WhatsAppHandler:
    def __init__(self):
        self.setup_logging()
        self.messages_queue = []
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('whatsapp.log'),
                logging.StreamHandler()
            ]
        )

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("user-data-dir=C:\\Users\\igor de jesus\\AppData\\Local\\Google\\Chrome\\User Data")
        chrome_options.add_argument('--log-level=3')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://web.whatsapp.com/")
        logging.info("WhatsApp Web loaded")
        return driver

    def send_message(self, contact, message):
        try:
            driver = self.setup_driver()
            wait = WebDriverWait(driver, 10)
            
            # Wait for search box
            search_box = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[title='Search input textbox']")
            ))
            search_box.send_keys(contact)
            time.sleep(2)
            
            # Click on contact
            contact_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, f"//span[@title='{contact}']")
            ))
            contact_element.click()
            time.sleep(1)
            
            # Find message box and send message
            message_box = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[title='Type a message']")
            ))
            message_box.send_keys(message)
            
            # Click send button
            send_button = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
            send_button.click()
            
            logging.info(f"Message sent to {contact}")
            
            # Save message details
            self.messages_queue.append({
                'contact': contact,
                'message': message,
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'sent'
            })
            
            time.sleep(5)
            driver.quit(10)
            return True
            
        except Exception as e:
            logging.error(f"Error sending message: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            return False

    def save_message_history(self):
        """Save message history to JSON file"""
        try:
            with open('message_history.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'last_updated': datetime.datetime.now().isoformat(),
                    'messages': self.messages_queue
                }, f, ensure_ascii=False, indent=2)
            logging.info("Message history saved successfully")
        except Exception as e:
            logging.error(f"Error saving message history: {str(e)}")

def main():
    handler = WhatsAppHandler()
    
    # Example usage
    contacts = [
        {'name': 'Igor', 'message': 'Olá boa noite!'},
        {'name': '+55', 'message': 'Seja bem-vindo!'}
    ]
    
    for contact in contacts:
        success = handler.send_message(contact['name'], contact['message'])
        if success:
            print(f"Message sent to {contact['name']}")
        else:
            print(f"Failed to send message to {contact['name']}")
    
    handler.save_message_history()

if __name__ == "__main__":
    main()