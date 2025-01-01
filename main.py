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

# Function to fetch data from NEPSEalpha
def fetch_nepsealpha_data():
    url = "https://nepsealpha.com/live-market"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    data = {}
    try:
        data["date"] = soup.find('td', string="Date").find_next('td').text.strip()
    except AttributeError:
        data["date"] = "Todays Date"
    try:
        data["current"] = soup.find('td', string="Current").find_next('td').text.strip()
    except AttributeError:
        data["current"] = "N/A"
    try:
        data["daily_gain"] = soup.find('td', string="Daily Gain").find_next('td').text.strip()
    except AttributeError:
        data["daily_gain"] = "N/A"
    try:
        data["turnover"] = soup.find('td', string="Turnover").find_next('td').text.strip()
    except AttributeError:
        data["turnover"] = "N/A"
    try:
        data["previous_close"] = soup.find('td', string="Previous Close").find_next('td').text.strip()
    except AttributeError:
        data["previous_close"] = "N/A"
    
    return data

# Function to generate HTML
def generate_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Data</title>
    </head>
    <body>
        <table>
            <tr>
                <td class="text-left text-bold">Date</td>
                <td id="date">{data['date']}</td>
            </tr>
            <tr>
                <td class="text-left text-bold">Current</td>
                <td id="current">{data['current']}</td>
            </tr>
            <tr>
                <td class="text-left text-bold line-1-3">Daily Gain</td>
                <td id="daily-gain">{data['daily_gain']}</td>
            </tr>
            <tr>
                <td class="text-left text-bold">Turnover</td>
                <td id="turnover">{data['turnover']}</td>
            </tr>
            <tr>
                <td class="text-left text-bold">Previous Close</td>
                <td id="previous-close">{data['previous_close']}</td>
            </tr>
        </table>
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
    data = fetch_nepsealpha_data()
    html_content = generate_html(data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
scheduler.add_job(refresh_data, "cron", hour=4, minute=0)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
