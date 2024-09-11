# backend_connector.py

import random
import string
import logging
import os
import subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, ElementClickInterceptedException

class BackendConnector:

    def __init__(self, web_driver_manager):
        self.web_driver_manager = web_driver_manager
        self.ip_address = None
        self.hostname = None  # Make sure this is initialized

    def is_ip_reachable(self, ip_address):
        try:
            response = subprocess.run(["ping", "-n", "1", ip_address], stdout=subprocess.PIPE)
            return response.returncode == 0
        except Exception as e:
            logging.error(f"Failed to ping IP: {str(e)}")
            return False

    def connect_to_backend(self, test_urls, username, password):
        for test_url in test_urls:
            ip_address = test_url.split("//")[1]
            if not self.is_ip_reachable(ip_address):
                logging.error(f"IP {ip_address} is not reachable.")
                continue

            driver = self.web_driver_manager.initialize_driver(headless=True)  # Adjust headless mode as needed
            if driver is None:
                return None, None, None

            try:
                driver.get(test_url)

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
                driver.find_element(By.NAME, 'username').send_keys(username)
                driver.find_element(By.NAME, 'password').send_keys(password)
                driver.find_element(By.XPATH, "//button[@name='login']").click()

                WebDriverWait(driver, 10).until(EC.url_contains(test_url))

                driver.find_element(By.XPATH, "//a[contains(text(), 'Info')]").click()

                self.ip_address = driver.find_element(By.XPATH, "//td[text()='System IP Address']/following-sibling::td/span").text.strip()
                power_drawn = driver.find_element(By.XPATH, "//td[contains(text(),'AC Voltage')]/following-sibling::td/span").text.strip()

                # Store the hostname
                self.hostname = driver.find_element(By.XPATH, "//td[text()='Hostname']/following-sibling::td/span").text.strip()

                logging.info(f"Successfully retrieved information from {test_url}: IP={self.ip_address}, Power={power_drawn}, Hostname={self.hostname}")

                return self.ip_address, power_drawn, self.hostname

            except (TimeoutException, WebDriverException) as e:
                logging.error(f"Failed to connect to {test_url}: {str(e)}")
                continue
            finally:
                self.web_driver_manager.quit_driver()

        logging.info("All test URLs failed to connect.")
        return None, None, None

    def get_evse_status(self, username, password):
        if self.ip_address is None:
            logging.error("IP address is not set. Connect to the backend first.")
            return None

        url = f"https://{self.ip_address}/EVSE"
        driver = self.web_driver_manager.initialize_driver(headless=True)
        if driver is None:
            logging.error("Failed to initialize WebDriver.")
            return None

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
            driver.find_element(By.NAME, 'username').send_keys(username)
            driver.find_element(By.NAME, 'password').send_keys(password)
            driver.find_element(By.XPATH, "//button[@name='login']").click()

            # Navigate to the EVSE Status page
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//legend[text()='EVSEs']")))

            # Extract the EVSE status details
            status = driver.find_element(By.XPATH, "//td[text()='Status']/following-sibling::td/span").text.strip()
            temperature = driver.find_element(By.XPATH, "//td[text()='Temperature']/following-sibling::td/span").text.strip()
            available_power = driver.find_element(By.XPATH, "//td[text()='Available Power']/following-sibling::td/span").text.strip()
            ac_voltage = driver.find_element(By.XPATH, "//td[text()='AC Voltage']/following-sibling::td/span").text.strip()
            current = driver.find_element(By.XPATH, "//td[text()='Current']/following-sibling::td/span").text.strip()
            current_offered = driver.find_element(By.XPATH, "//td[text()='Current Offered']/following-sibling::td/span").text.strip()
            energy = driver.find_element(By.XPATH, "//td[text()='Energy']/following-sibling::td/span").text.strip()
            evse_pp_state = driver.find_element(By.XPATH, "//td[text()='EVSE PP State']/following-sibling::td/span").text.strip()

            evse_status = {
                "Status": status,
                "Temperature": temperature,
                "Available Power": available_power,
                "AC Voltage": ac_voltage,
                "Current": current,
                "Current Offered": current_offered,
                "Energy": energy,
                "EVSE PP State": evse_pp_state,
            }

            logging.info(f"EVSE Status retrieved: {evse_status}")
            return evse_status

        except Exception as e:
            logging.error(f"An error occurred while retrieving EVSE status: {str(e)}")
            return None
        finally:
            driver.quit()

    def upload_config_file(self, config_file_path, username, password):
        config_file_path = os.path.abspath(config_file_path)

        if not os.path.exists(config_file_path):
            logging.error(f"Configuration file does not exist: {config_file_path}")
            return "Configuration file not found."

        if self.ip_address is None:
            logging.error("IP address is not set. Connect to the backend first.")
            return "IP address is not set. Connect to the backend first."

        url = f"https://{self.ip_address}"
        driver = self.web_driver_manager.initialize_driver(headless=True)
        if driver is None:
            return "Failed to initialize WebDriver."

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
            driver.find_element(By.NAME, 'username').send_keys(username)
            driver.find_element(By.NAME, 'password').send_keys(password)
            driver.find_element(By.XPATH, "//button[@name='login']").click()

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href='/Assembler']")))
            assembler_link = driver.find_element(By.XPATH, "//a[@href='/Assembler']")
            assembler_link.click()

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//legend[contains(text(), "Configuration Import / Export")]')))
            file_input = driver.find_element(By.ID, 'configToUpload')
            driver.execute_script("arguments[0].scrollIntoView(true);", file_input)

            # Upload the configuration file
            try:
                file_input.send_keys(config_file_path)
                logging.info(f"Uploaded configuration file: {config_file_path}")

                import time
                # Wait for the button to be enabled and click it
                upload_button = driver.find_element(By.ID, 'uploadConfig')
                WebDriverWait(driver, 20).until(lambda d: upload_button.is_enabled())
                driver.execute_script("arguments[0].scrollIntoView(true);", upload_button)
                time.sleep(1)  # Ensure any animations or messages settle

                try:
                    upload_button.click()
                    logging.info("Clicked on the 'Import Config' button successfully.")
                except ElementClickInterceptedException as e:
                    logging.error(f"Element click intercepted: {str(e)}")
                    # Optionally retry clicking or use JavaScript to click
                    driver.execute_script("arguments[0].click();", upload_button)

            except Exception as e:
                logging.error(f"Failed to upload configuration file: {str(e)}")
                return f"An error occurred during configuration upload: {str(e)}"

            return "Configuration uploaded successfully."

        except Exception as e:
            logging.error(f"An error occurred during configuration upload: {str(e)}")
            return f"An error occurred: {str(e)}"

        finally:
            driver.quit()

    def allocate_ocpp_id(self, username, password):
        if self.ip_address is None:
            logging.error("IP address is not set. Connect to the backend first.")
            return "IP address is not set. Connect to the backend first."

        if self.hostname is None:
            logging.error("Hostname is not set. Ensure you have retrieved it during the readiness check.")
            return "Hostname is not set. Ensure you have retrieved it during the readiness check."

        # Extract the last 9 digits from the hostname
        ray_id_last_9 = self.hostname[-9:]
        logging.info(f"Extracted RAY ID (last 9 digits of Hostname): {ray_id_last_9}")

        url = f"https://{self.ip_address}/CSMS"
        driver = self.web_driver_manager.initialize_driver(headless=True)
        if driver is None:
            logging.error("Failed to initialize WebDriver.")
            return "Failed to initialize WebDriver."

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
            driver.find_element(By.NAME, 'username').send_keys(username)
            driver.find_element(By.NAME, 'password').send_keys(password)
            driver.find_element(By.XPATH, "//button[@name='login']").click()

            # Navigate to CSMS page
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href='/CSMS']")))
            csms_link = driver.find_element(By.XPATH, "//a[@href='/CSMS']")
            csms_link.click()
            logging.info(f"Navigated to the CSMS page for OCPP ID allocation.")

            # Set the OCPP ID (Charger Identity)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'Identity')))
            identity_input = driver.find_element(By.ID, 'Identity')
            identity_input.clear()
            identity_input.send_keys(ray_id_last_9)
            logging.info(f"Set Charger Identity (OCPP ID) to: {ray_id_last_9}")

            # Save the changes (using the correct xpath for the save button)
            save_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Save']")
            save_button.click()
            logging.info("Clicked on the 'Save' button to allocate OCPP ID.")

            return f"OCPP ID allocated successfully: {ray_id_last_9}"

        except Exception as e:
            logging.error(f"An error occurred during OCPP ID allocation: {str(e)}")
            return f"An error occurred: {str(e)}"

        finally:
            driver.quit()

    def generate_password(self):
        # Generate 4 random alphabets
        alphabets = ''.join(random.choices(string.ascii_uppercase, k=4))

        # Generate 1 random special character
        special_char = random.choice('#')

        # Generate 4 random numerical digits
        digits = ''.join(random.choices(string.digits, k=4))

        # Concatenate all components to form the password
        password = 'EGO' + special_char + alphabets + digits

        return password

    def change_password(self, driver, username, password):
        try:
            # Wait for the "Change Password" button to be present on the Security page
            change_password_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//input[@name='{username}-Change']"))
            )
            change_password_button.click()

            # Wait for the pop-up to appear
            popup = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'popup')))

            # Locate and input the new password
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'password1'))
            )
            password_input.clear()
            password_input.send_keys(password)

            # Locate and confirm the new password
            confirm_password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'password2'))
            )
            confirm_password_input.clear()
            confirm_password_input.send_keys(password)

            # Wait for the "Update" button inside the form
            update_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@name="Update" and @type="submit"]'))
            )
            update_button.click()

            logging.info(f"Password changed for {username} successfully.")
        except Exception as e:
            logging.error(f"An error occurred during password change for {username}: {str(e)}")
            raise

    def change_passwords(self, username, password):
        if self.ip_address is None:
            logging.error("IP address is not set. Connect to the backend first.")
            return {"error": "IP address is not set. Connect to the backend first."}

        url = f"https://{self.ip_address}/Security"
        driver = self.web_driver_manager.initialize_driver(headless=True)
        if driver is None:
            logging.error("Failed to initialize WebDriver.")
            return {"error": "Failed to initialize WebDriver."}

        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username')))
            driver.find_element(By.NAME, 'username').send_keys(username)
            driver.find_element(By.NAME, 'password').send_keys(password)
            driver.find_element(By.XPATH, "//button[@name='login']").click()

            # Navigate to Security page
            security_link = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href='/Security']")))
            security_link.click()

            # Define passwords
            assembler_password = "E2"
            installer_password = self.generate_password()
            ev_password = "EVOWNER"

            # Change passwords
            self.change_password(driver, "Assembler", assembler_password)
            self.change_password(driver, "Installer", installer_password)
            self.change_password(driver, "EV", ev_password)

            logging.info(f"Passwords updated: Assembler={assembler_password}, Installer={installer_password}, EV={ev_password}")

            return {
                "Assembler": assembler_password,
                "Installer": installer_password,
                "EV": ev_password
            }

        except Exception as e:
            logging.error(f"An error occurred during password updates: {str(e)}")
            return {"error": str(e)}
        finally:
            driver.quit()