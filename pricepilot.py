import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
import schedule
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import logging
import os

# Configure logging
logging.basicConfig(filename="pricepilot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Email credentials
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"

# CSV storage
CSV_FILE = "flights.csv"

# Create CSV if not exists
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["Origin", "Destination", "Date", "MaxPrice", "Airline", "Connections", "Email", "Interval"]).to_csv(CSV_FILE, index=False)

# Function to add flight

def add_flight():
    details = {
        "Origin": origin.get().upper().strip(),
        "Destination": destination.get().upper().strip(),
        "Date": date.get().strip(),
        "MaxPrice": float(max_price.get().strip()),
        "Airline": airline.get().title().strip(),
        "Connections": connections.get(),
        "Email": email.get().strip(),
        "Interval": int(interval.get()),
    }

    if not all([details["Origin"], details["Destination"], details["Date"], details["MaxPrice"], details["Email"]]):
        messagebox.showerror("Error", "Please fill in all mandatory fields.")
        return

    df = pd.read_csv(CSV_FILE)
    if ((df['Origin'] == details['Origin']) & (df['Destination'] == details['Destination']) & (df['Date'] == details['Date'])).any():
        messagebox.showwarning("Duplicate", "This flight is already tracked.")
        return

    df = df.append(details, ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    logging.info(f"Added flight: {details}")
    messagebox.showinfo("Success", "Flight added successfully!")
    clear_entries()

# Clear entry fields
def clear_entries():
    origin.set("")
    destination.set("")
    date.set("")
    max_price.set("")
    airline.set("")
    email.set("")
    connections.set("Yes")
    interval.set("60")

# Send email alerts
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())

# Scrape flight price from Google Flights (simplified)
def fetch_price(origin, destination, date):
    url = f"https://www.google.com/search?q=flight+from+{origin}+to+{destination}+on+{date}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, "html.parser")
        price = soup.find("div", class_="YMlKec").text.replace("$", "").replace(",", "")
        return float(price)
    except Exception as e:
        logging.warning(f"Price not found: {e}")
        return None

# Check flights and send alerts
def check_prices():
    df = pd.read_csv(CSV_FILE)
    for idx, flight in df.iterrows():
        price = fetch_price(flight.Origin, flight.Destination, flight.Date)
        if price and price <= flight.MaxPrice:
            send_email(
                flight.Email,
                f"Price Alert: {flight.Origin}-{flight.Destination}",
                f"Flight is now ${price}! Book ASAP."
            )
            logging.info(f"Alert sent for {flight.Origin}-{flight.Destination}")

# Scheduler to run checks
def schedule_checks():
    schedule.clear()
    df = pd.read_csv(CSV_FILE)
    intervals = df.Interval.unique()
    for interval_min in intervals:
        schedule.every(interval_min).minutes.do(check_prices)

    while True:
        schedule.run_pending()
        time.sleep(30)

# Start tracking in separate thread
def start_tracking():
    thread = threading.Thread(target=schedule_checks, daemon=True)
    thread.start()
    messagebox.showinfo("Tracking", "Flight tracking started.")

# GUI Setup
app = tk.Tk()
app.title("PricePilot - Flight Tracker")
app.geometry("450x550")

style = ttk.Style(app)
style.theme_use('clam')

origin = tk.StringVar()
destination = tk.StringVar()
date = tk.StringVar()
max_price = tk.StringVar()
airline = tk.StringVar()
email = tk.StringVar()
connections = tk.StringVar(value="Yes")
interval = tk.StringVar(value="60")

fields = [
    ("Origin (e.g. ATL)", origin),
    ("Destination (e.g. JFK)", destination),
    ("Date (YYYY-MM-DD)", date),
    ("Max Price ($)", max_price),
    ("Preferred Airline", airline),
    ("Email for Alerts", email),
    ("Allow Connections?", connections, ["Yes", "No"]),
    ("Check Interval (min)", interval, ["15", "30", "60", "120"])
]

for label, var, *opts in fields:
    ttk.Label(app, text=label).pack(pady=5)
    if opts:
        ttk.Combobox(app, textvariable=var, values=opts[0]).pack()
    else:
        ttk.Entry(app, textvariable=var).pack()

ttk.Button(app, text="Add Flight", command=add_flight).pack(pady=10)
ttk.Button(app, text="Start Tracking", command=start_tracking).pack(pady=10)

app.mainloop()
