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

# Email Configuration
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_email_password"

CSV_FILE = "flights.csv"

# Ensure CSV exists
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["origin", "destination", "date", "max_price", "email", "airline", "connections"])

# Function to add flights
def add_flight():
    origin = origin_entry.get().strip().upper()
    destination = destination_entry.get().strip().upper()
    date = date_entry.get().strip()
    max_price = max_price_entry.get().strip()
    email = email_entry.get().strip()
    airline = airline_entry.get().strip().title()
    connections = connections_var.get()

    if not all([origin, destination, date, max_price, email]):
        messagebox.showerror("Error", "All fields except Airline are required!")
        return

    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([origin, destination, date, max_price, email, airline, connections])

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

# Function to send email alerts
def send_email(to_email, origin, destination, price):
    subject = f"Flight Price Alert: {origin} to {destination}"
    body = f"The price dropped to {price}!\nBook now at Google Flights."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        print(f"Email sent to {to_email} for {origin} → {destination}")
    except Exception as e:
        print(f"Email failed: {e}")

# Function to scrape flight price
def get_flight_price(origin, destination, date, airline="", connections="Yes"):
    url = f"https://www.google.com/search?q=flights+from+{origin}+to+{destination}+on+{date}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "Not Found"

    soup = BeautifulSoup(response.text, "html.parser")
    price_element = soup.find("div", class_="YMlKec")
    
    if price_element:
        price = price_element.text.replace("$", "")
        return price if price.isdigit() else "Not Found"

    return "Not Found"

# Function to check prices and send alerts
def check_flight_prices():
    print("Checking flight prices...")
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            price = get_flight_price(row["origin"], row["destination"], row["date"], row["airline"], row["connections"])
            if price != "Not Found":
                price_value = int(price)
                if price_value < int(row["max_price"]):
                    send_email(row["email"], row["origin"], row["destination"], price)

# Function to run price checker on a schedule
def start_tracking():
    schedule.every().day.at("08:00").do(check_flight_prices)

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
root.geometry("400x450")

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

tk.Button(root, text="Add Flight", command=add_flight).pack(pady=5)
tk.Button(root, text="Start Tracking", command=start_tracking).pack(pady=5)

root.mainloop()
