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

# Function to fetch data from the Sharesansar page
def fetch_sharesansar_data():
    url = "https://www.sharesansar.com/stock-heat-map/volume"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    data = {}
    try:
        data["as_of"] = soup.find('span', string="As of :").find_next('span').text.strip()
    except AttributeError:
        data["as_of"] = "N/A"
    try:
        data["nepse_index"] = soup.find('span', string="NEPSE Index :").find_next('span').text.strip()
    except AttributeError:
        data["nepse_index"] = "N/A"
    
    return data

# Function to generate HTML
def generate_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sharesansar Data</title>
    </head>
    <body>
        <table>
            <tr>
                <td class="text-left text-bold">As of</td>
                <td id="as-of">{data['as_of']}</td>
            </tr>
            <tr>
                <td class="text-left text-bold">NEPSE Index</td>
                <td id="nepse-index">{data['nepse_index']}</td>
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
    data = fetch_sharesansar_data()
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
