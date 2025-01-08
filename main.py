import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
from flask import Flask
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to fetch data using Playwright
def fetch_nepsealpha_data():
    data = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = "https://nepsealpha.com/live-market"
        page.goto(url)
        page.wait_for_selector('tr[data-v-dfae8c1a=""]')

        rows = page.query_selector_all('tr[data-v-dfae8c1a=""]')
        for row in rows:
            columns = row.query_selector_all('td')
            if len(columns) == 2:
                key = columns[0].inner_text().strip()
                value = columns[1].inner_text().strip()
                data[key] = value

        browser.close()
    return data

# Function to generate HTML
def generate_html(data):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Data</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f4f4f4; }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <tr><th>Key</th><th>Value</th></tr>
    """
    for key, value in data.items():
        html_content += f"<tr><td>{key}</td><td>{value}</td></tr>"
    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content

# Upload HTML to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    try:
        data = fetch_nepsealpha_data()
        html_content = generate_html(data)
        upload_to_ftp(html_content)
        print(f"[{datetime.now()}] Data refreshed and uploaded successfully!")
    except Exception as e:
        print(f"[{datetime.now()}] Error refreshing data: {e}")

# Scheduler
scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
scheduler.add_job(refresh_data, "cron", hour=4, minute=0)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Flask Route
@app.route("/")
def home():
    return "NEPSE Data Scraper is running!"

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
