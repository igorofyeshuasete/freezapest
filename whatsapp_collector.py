import datetime
import time
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WhatsAppCollector:
    def __init__(self):
        self.target_date = datetime.datetime.now().strftime('%d/%m/%Y')
        
    def collect_messages(self):
        try:
            # Configurações do Chrome
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")  # Porta para debugging
            chrome_options.add_argument("--user-data-dir=C:\\Users\\igor de jesus\\AppData\\Local\\Google\\Chrome\\User Data")
            chrome_options.add_argument("--profile-directory=Default")  # Pasta do perfil
            chrome_options.add_argument("--disable-extensions")  # Desativa extensões
            chrome_options.add_argument("--disable-gpu")  # Desativa GPU (útil para ambientes virtuais)
            chrome_options.add_argument("--headless")  # Executa em modo headless (sem interface gráfica)
            
            # Caminho para o ChromeDriver (ajuste conforme sua instalação)
            service = Service(executable_path="C:\\caminho\\para\\chromedriver.exe")
            
            # Inicializa o driver
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://web.whatsapp.com/")
            print("Accessing WhatsApp Web...")
            
            # Restante do código (igual ao original)
            # Wait for chats to load
            wait = WebDriverWait(driver, 45)
            chats = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_8nE1Y")))
            print(f"Found {len(chats)} chats")

            messages = []
            # Process first 5 chats (código omitido para brevidade)
            # ... [seu código de coleta de mensagens aqui] ...

            # Save messages to file
            with open("collected_messages.txt", "w", encoding="utf-8") as f:
                f.write(f"Message Collection Report - {self.target_date}\n")
                f.write("=" * 50 + "\n\n")
                for msg in messages:
                    f.write(f"Contact: {msg['contact']}\n")
                    f.write(f"Time: {msg['timestamp']}\n")
                    f.write(f"Status: {'Unread' if msg['unread'] else 'Read'}\n")
                    f.write(f"Message:\n{msg['message']}\n")
                    f.write("-" * 50 + "\n\n")

            print(f"\nCollection completed. Messages saved to collected_messages.txt")
            driver.quit()

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            if 'driver' in locals():
                driver.quit()

def run_http_server():
    os.chdir(os.getcwd())
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Serving HTTP on http://localhost:8000 ...")
    httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_http_server)
    server_thread.daemon = True
    server_thread.start()

    collector = WhatsAppCollector()
    collector.collect_messages()

    print("Pressione Ctrl+C para encerrar o servidor.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Servidor encerrado.")