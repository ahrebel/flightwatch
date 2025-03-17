import tkinter as tk
from tkinter import messagebox
import csv
import os
import threading
import time
import schedule
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import logging

# Setup logging
logging.basicConfig(filename="flightwatch.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Email Configuration
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_email_password"

CSV_FILE = "flights.csv"

# Ensure CSV exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["origin", "destination", "date", "max_price", "email", "airline", "connections", "check_interval"])

# Function to add flights
def add_flight():
    origin = origin_entry.get().strip().upper()
    destination = destination_entry.get().strip().upper()
    date = date_entry.get().strip()
    max_price = max_price_entry.get().strip()
    email = email_entry.get().strip()
    airline = airline_entry.get().strip().title()
    connections = connections_var.get()
    check_interval = interval_var.get()

    if not all([origin, destination, date, max_price, email, check_interval]):
        messagebox.showerror("Error", "All fields except Airline are required!")
        return

    # Prevent duplicate entries
    with open(CSV_FILE, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[:5] == [origin, destination, date, max_price, email]:
                messagebox.showwarning("Duplicate Entry", "This flight is already being tracked!")
                return

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([origin, destination, date, max_price, email, airline, connections, check_interval])

    logging.info(f"Added flight: {origin} → {destination} on {date}, Max Price: ${max_price}")
    messagebox.showinfo("Success", "Flight added successfully!")
    clear_fields()

def clear_fields():
    origin_entry.delete(0, tk.END)
    destination_entry.delete(0, tk.END)
    date_entry.delete(0, tk.END)
    max_price_entry.delete(0, tk.END)
    email_entry.delete(0, tk.END)
    airline_entry.delete(0, tk.END)
    connections_var.set("Yes")
    interval_var.set("60")

# Function to send email alerts
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Email failed: {e}")

# Function to test email settings
def test_email():
    to_email = email_entry.get().strip()
    if not to_email:
        messagebox.showerror("Error", "Enter an email address first!")
        return
    send_email(to_email, "FlightWatch Test Email", "This is a test email from FlightWatch.")
    messagebox.showinfo("Test Email", "Test email sent successfully!")

# Function to scrape flight price
def get_flight_price(origin, destination, date, airline="", connections="Yes"):
    url = f"https://www.google.com/search?q=flights+from+{origin}+to+{destination}+on+{date}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logging.warning(f"Failed to fetch data for {origin} → {destination}")
        return "Not Found"

    soup = BeautifulSoup(response.text, "html.parser")
    price_element = soup.find("div", class_="YMlKec")
    
    if price_element:
        price = price_element.text.replace("$", "")
        return price if price.isdigit() else "Not Found"

    return "Not Found"

# Function to check prices and send alerts
def check_flight_prices():
    logging.info("Checking flight prices...")
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            price = get_flight_price(row["origin"], row["destination"], row["date"], row["airline"], row["connections"])
            if price != "Not Found":
                price_value = int(price)
                if price_value < int(row["max_price"]):
                    send_email(row["email"], f"Flight Price Alert: {row['origin']} to {row['destination']}", f"The price dropped to ${price}!\nBook now at Google Flights.")

# Function to start tracking with custom intervals
def start_tracking():
    schedule.clear()
    
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            interval = int(row["check_interval"])
            schedule.every(interval).minutes.do(check_flight_prices)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    messagebox.showinfo("Tracking Started", "Flight price tracking has started!")

# GUI Setup
root = tk.Tk()
root.title("FlightWatch")
root.geometry("400x500")

tk.Label(root, text="Origin (e.g., ATL)").pack()
origin_entry = tk.Entry(root)
origin_entry.pack()

tk.Label(root, text="Destination (e.g., LAX)").pack()
destination_entry = tk.Entry(root)
destination_entry.pack()

tk.Label(root, text="Date (YYYY-MM-DD)").pack()
date_entry = tk.Entry(root)
date_entry.pack()

tk.Label(root, text="Max Price ($)").pack()
max_price_entry = tk.Entry(root)
max_price_entry.pack()

tk.Label(root, text="Email for Alerts").pack()
email_entry = tk.Entry(root)
email_entry.pack()

tk.Label(root, text="Preferred Airline (Optional)").pack()
airline_entry = tk.Entry(root)
airline_entry.pack()

tk.Label(root, text="Allow Connections?").pack()
connections_var = tk.StringVar(value="Yes")
tk.OptionMenu(root, connections_var, "Yes", "No").pack()

tk.Label(root, text="Check Interval (minutes)").pack()
interval_var = tk.StringVar(value="60")
tk.OptionMenu(root, interval_var, "15", "30", "60", "120", "360").pack()

tk.Button(root, text="Add Flight", command=add_flight).pack(pady=5)
tk.Button(root, text="Start Tracking", command=start_tracking).pack(pady=5)
tk.Button(root, text="Test Email", command=test_email).pack(pady=5)

root.mainloop()
