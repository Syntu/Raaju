import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to scrape NEPSE Alpha live market data
def scrape_nepse_alpha():
    url = "https://nepsealpha.com/live-market"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            date = soup.find('span', class_='date').text.strip()
            current_index = soup.find('span', class_='current-index').text.strip()
            daily_gain = soup.find('span', class_='daily-gain').text.strip()
            turnover = soup.find('span', class_='turnover').text.strip()
            previous_close = soup.find('span', class_='previous-close').text.strip()
            return {
                "date": date,
                "current_index": current_index,
                "daily_gain": daily_gain,
                "turnover": turnover,
                "previous_close": previous_close,
            }
        except AttributeError:
            print("Unable to find the required elements in the NEPSE Alpha page.")
            return None
    else:
        print(f"Failed to fetch NEPSE Alpha data. Status code: {response.status_code}")
        return None

# Function to generate HTML
def generate_html(nepse_alpha_data):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    nepse_alpha_section = ""
    
    if nepse_alpha_data:
        nepse_alpha_section = f"""
        <div class="nepse-alpha">
            <h3>NEPSE Alpha Data</h3>
            <p>Date: {nepse_alpha_data['date']}</p>
            <p>Current Index: {nepse_alpha_data['current_index']}</p>
            <p>Daily Gain: {nepse_alpha_data['daily_gain']}</p>
            <p>Turnover: {nepse_alpha_data['turnover']}</p>
            <p>Previous Close: {nepse_alpha_data['previous_close']}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1 {{
                text-align: center;
                font-size: 40px;
                font-weight: bold;
                margin-top: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 18px;
                margin-bottom: 20px;
            }}
            .nepse-alpha {{
                margin: 20px auto;
                width: 80%;
                padding: 15px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
                text-align: left;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <h1>NEPSE Data Table</h1>
        <h2>Welcome to NEPSE Stock Data</h2>
        {nepse_alpha_section}
        <div class="footer">
            <p>Updated on: {updated_time}</p>
        </div>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    nepse_alpha_data = scrape_nepse_alpha()
    html_content = generate_html(nepse_alpha_data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
