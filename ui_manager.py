import logging
import tkinter as tk
from tkinter import messagebox

class UIManager:
    def __init__(self, root, backend_connector):
        self.root = root
        self.backend_connector = backend_connector
        self.logo_image = None  # Keep a reference to the image
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Production Handling Automation Suite")
        self.root.geometry("1024x768")  # Adjusting the window size

        frame_logo = tk.Frame(self.root)
        frame_logo.pack(pady=2)

        try:
            self.logo_image = tk.PhotoImage(file=r'./logo.png')  # Use a relative path
            logo_label = tk.Label(frame_logo, image=self.logo_image)
            logo_label.pack()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to load logo image: {str(e)}")
            logging.error(f"Unable to load logo image: {str(e)}")

        title_label = tk.Label(self.root, text="EGO EV 7.2 kW Single Phase Charger (Socket Version)", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        self.frame_main = tk.Frame(self.root)
        self.frame_main.pack(pady=20)

        self.loading_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.loading_label.pack(pady=5)

        self.readiness_result_label = tk.Label(self.frame_main, text="", font=("Helvetica", 12), fg="green", width=70, anchor='w')
        btn_check_unit = tk.Button(self.frame_main, text="Check Unit Readiness", command=self.check_unit_ready, width=30, height=2)
        btn_check_unit.grid(row=0, column=0, padx=10, pady=15)
        btn_check_unit.bind("<Enter>", self.on_enter)
        btn_check_unit.bind("<Leave>", self.on_leave)
        self.readiness_result_label.grid(row=0, column=1, padx=(20, 30), pady=20)

        self.create_buttons()

        # Set up the EVSE screen on the left side
        self.setup_evse_screen()

    def setup_evse_screen(self):
        # EVSE Status Frame on the left
        self.evse_frame = tk.Frame(self.root, width=160, height=160, bg="black")
        self.evse_frame.place(x=10, y=50)  # Place it on the left side of the window

        self.evse_status_labels = {
            "Status": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "Temperature": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "Available Power": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "AC Voltage": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "Current": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "Current Offered": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "Energy": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
            "EVSE PP State": tk.Label(self.evse_frame, text="", font=("Helvetica", 12), bg="black", fg="white"),
        }

        # Pack the labels vertically
        for label in self.evse_status_labels.values():
            label.pack(anchor="w")

        self.poll_evse_status()

    def poll_evse_status(self):
        evse_status = self.backend_connector.get_evse_status(username='Assembler', password='E2')
        if evse_status:
            self.update_evse_status(evse_status)
        self.root.after(5000, self.poll_evse_status)  # Poll every 5 seconds

    def update_evse_status(self, evse_status):
        status_color = {
            "preparing": "pink",
            "suspendedev": "gray",
            "charging": "blue",
            "available": "green"
        }
        
        # Update each label with the EVSE status information
        for key, label in self.evse_status_labels.items():
            label.config(text=f"{key}: {evse_status[key]}")

        # Set the Status color dynamically
        status = evse_status["Status"]
        self.evse_status_labels["Status"].config(fg=status_color.get(status, "white"))

    def check_unit_ready(self):
        self.loading_label.config(text="Loading... Please wait.")
        self.root.update()

        ip_address, power_drawn, hostname = self.backend_connector.connect_to_backend(
            test_urls=[
                'https://192.168.2.3', 'https://192.168.0.108',
                'https://192.168.2.4', 'https://192.168.2.5', 
                'https://192.168.2.6'
            ],
            username='Assembler',
            password='E2'
        )

        self.loading_label.config(text="")
        self.root.update()

        if not ip_address or not power_drawn:
            self.readiness_result_label.config(text="Could not retrieve IP or power information.", fg="red")
            return

        try:
            power_drawn = float(power_drawn.strip('V'))
        except ValueError:
            self.readiness_result_label.config(text="Invalid power drawn value retrieved.", fg="red")
            logging.error("Invalid power drawn value retrieved.")
            return

        if 220.0 <= power_drawn <= 240.0:
            self.readiness_result_label.config(text=f"IP Address: {ip_address}, Power Supply: {power_drawn:.2f}V, Hostname: {hostname}", fg="green")
            logging.info("Unit is ready for testing.")
        else:
            self.readiness_result_label.config(text="Power supply is not within the expected range.", fg="orange")
            logging.warning("Power supply is not within the expected range.")

    def upload_config(self):
        self.loading_label.config(text="Uploading configuration... Please wait.")
        self.root.update()

        config_file_path = r'./1.3.7_Config.zip'  # Adjust the path to your configuration file
        status = self.backend_connector.upload_config_file(config_file_path=config_file_path, username='Assembler', password='E2')
        
        self.loading_label.config(text="")
        self.root.update()

        self.pre_configure_result_label.config(text=status, fg="green" if "successfully" in status else "red")

    def allocate_ocpp_id(self):
        self.loading_label.config(text="Allocating OCPP ID... Please wait.")
        self.root.update()

        status = self.backend_connector.allocate_ocpp_id(username='Assembler', password='E2')
        self.loading_label.config(text="")
        self.root.update()

        self.ocpp_id_result_label.config(text=status, fg="green" if "successfully" in status else "red")

        if "successfully" in status:
            self.btn_generate_passwords.config(state=tk.NORMAL)

    def change_passwords(self):
        self.loading_label.config(text="Changing passwords... Please wait.")
        self.root.update()

        passwords = self.backend_connector.change_passwords(username='Assembler', password='E2')
        self.loading_label.config(text="")
        self.root.update()

        if "error" in passwords:
            self.generate_passwords_result_label.config(text=f"Error: {passwords['error']}", fg="red")
        else:
            password_text = f"Assembler: {passwords['Assembler']} | Installer: {passwords['Installer']} | EV: {passwords['EV']}"
            self.generate_passwords_result_label.config(text=password_text, fg="green")

    def on_enter(self, e):
        e.widget['background'] = 'lightblue'

    def on_leave(self, e):
        e.widget['background'] = 'SystemButtonFace'

    def create_buttons(self):
        self.pre_configure_result_label = tk.Label(self.frame_main, text="", font=("Helvetica", 12), fg="green", width=60, anchor='w')
        btn_pre_configure = tk.Button(self.frame_main, text="Pre-configure Settings", command=self.upload_config, width=30, height=2)
        btn_pre_configure.grid(row=2, column=0, padx=10, pady=5)
        btn_pre_configure.bind("<Enter>", self.on_enter)
        btn_pre_configure.bind("<Leave>", self.on_leave)
        self.pre_configure_result_label.grid(row=2, column=1, padx=10, pady=5)

        # Add "OCPP ID Allocation" button
        self.ocpp_id_result_label = tk.Label(self.frame_main, text="", font=("Helvetica", 12), fg="green", width=60, anchor='w')
        btn_ocpp_id_allocation = tk.Button(self.frame_main, text="OCPP ID Allocation", command=self.allocate_ocpp_id, width=30, height=2)
        btn_ocpp_id_allocation.grid(row=3, column=0, padx=10, pady=5)
        btn_ocpp_id_allocation.bind("<Enter>", self.on_enter)
        btn_ocpp_id_allocation.bind("<Leave>", self.on_leave)
        self.ocpp_id_result_label.grid(row=3, column=1, padx=10, pady=5)

        # Add "Generate Passwords" button, initially disabled
        self.btn_generate_passwords = tk.Button(self.frame_main, text="Generate Passwords", command=self.change_passwords, width=30, height=2, state=tk.DISABLED)
        self.btn_generate_passwords.grid(row=4, column=0, padx=10, pady=5)
        self.btn_generate_passwords.bind("<Enter>", self.on_enter)
        self.btn_generate_passwords.bind("<Leave>", self.on_leave)
        self.generate_passwords_result_label = tk.Label(self.frame_main, text="", font=("Helvetica", 12), fg="green", width=60, anchor='w')
        self.generate_passwords_result_label.grid(row=4, column=1, padx=10, pady=5)     

