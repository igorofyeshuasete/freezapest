import logging
import psutil
import threading
import time
from pathlib import Path

class ApplicationMonitor:
    def __init__(self):
        self.setup_logging()
        self.process = psutil.Process()
        self.start_time = time.time()

    def setup_logging(self):
        log_file = Path("debug/app_monitor.log")
        log_file.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def monitor_resources(self):
        while True:
            try:
                # Monitor CPU and Memory
                cpu_percent = self.process.cpu_percent()
                memory_info = self.process.memory_info()
                
                logging.info(f"""
                    Performance Metrics:
                    CPU Usage: {cpu_percent}%
                    Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB
                    Virtual Memory: {memory_info.vms / 1024 / 1024:.2f} MB
                    Uptime: {time.time() - self.start_time:.2f} seconds
                """)
                
                # Check virtual environment
                import sys
                venv_path = sys.prefix
                logging.info(f"Virtual Environment: {venv_path}")
                
            except Exception as e:
                logging.error(f"Monitoring error: {str(e)}")
            
            time.sleep(60)  # Update every minute

    def start_monitoring(self):
        monitor_thread = threading.Thread(
            target=self.monitor_resources, 
            daemon=True
        )
        monitor_thread.start()