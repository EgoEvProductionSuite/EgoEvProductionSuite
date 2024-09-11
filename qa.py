# qa.py

import logging
from web_driver_manager import WebDriverManager
from backend_connector import BackendConnector
from ui_manager import UIManager
import tkinter as tk

# Set up logging
logging.basicConfig(
    filename="app.log",  # Log to a file
    level=logging.INFO,   # Set the minimum log level
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    web_driver_manager = WebDriverManager(driver_path='./chromedriver.exe')  # Provide the correct path to chromedriver
    backend_connector = BackendConnector(web_driver_manager)

    # Test with headless mode explicitly set to False to see if it works
    driver = web_driver_manager.initialize_driver(headless=True)  # Set this to True or False depending on what you want to test
    if driver is None:
        logging.error("WebDriver failed to initialize. Exiting.")
        return

    root = tk.Tk()
    ui_manager = UIManager(root, backend_connector)

    root.mainloop()

if __name__ == "__main__":
    main()

