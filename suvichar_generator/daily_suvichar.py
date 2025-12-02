

import os
import sys
import csv
import requests
import smtplib
import datetime
from email.message import EmailMessage
from dotenv import load_dotenv


load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def fetch_quote():
    """Fetch random quote from ZenQuotes API"""
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=10)
        response.raise_for_status()
        data = response.json()[0]
        return data["q"].strip(), data["a"].strip()
    except requests.RequestException as e:
        print(f"Failed to fetch quote: {e}")
        return None, None


def save_quote(date_s, day, quote, author):
    """Save quote to log file"""
    new = not os.path.exists("suvichar_history.csv")
    with open("suvichar_history.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["Date", "Day", "Lang", "Quote", "Author"])
        writer.writerow([date_s, day, "English", quote, author])

def send_email(date_s, day, quote, author):
    """Send quote through email"""
    if not EMAIL_USER or not EMAIL_PASS:
        print("Email Credentials Missing!")
        return False

    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER
    msg["Subject"] = f"Daily Suvichar — {day}, {date_s}"
    msg.set_content(f'{date_s} ({day})\n\n"{quote}"\n\n— {author}\n')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def main():
    """Main function"""
    now = datetime.datetime.now()
    ds = now.strftime("%d/%m/%y")
    day = now.strftime("%A")

    quote, author = fetch_quote()
    if not quote:
        print("Could not fetch quote. Exiting.")
        sys.exit(1)

    print(f'\n{ds} ({day}) "{quote}" — {author}\n')

    save_quote(ds, day, quote, author)
    send_email(ds, day, quote, author)

if __name__ == "__main__":
    main()