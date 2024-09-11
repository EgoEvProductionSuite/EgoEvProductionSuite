# web_driver_manager.py

import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class WebDriverManager:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None

    def initialize_driver(self, headless=True):  # Pass headless as a parameter
        try:
            service = Service(self.driver_path)
            chrome_options = Options()

            if headless:
                chrome_options.add_argument("--headless")  # Enable headless mode based on parameter
                logging.info("Headless mode is enabled.")
            else:
                logging.info("Headless mode is disabled.")

            # Add necessary options to skip the first run experience and search engine choice
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument('--ignore-certificate-errors')  # Ignore SSL certificate errors
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("disable-search-engine-choice-screen")
            chrome_options.add_argument("disable-first-run-ui")

            # Log the final options being passed to Chrome
            logging.info(f"Chrome options being used: {chrome_options.arguments}")

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.info("WebDriver initialized successfully.")
            return self.driver
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {str(e)}")
            return None

    def quit_driver(self):
        if self.driver is not None:
            self.driver.quit()
            logging.info("WebDriver closed successfully.")
