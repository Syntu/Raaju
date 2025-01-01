import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Check if the required environment variables are set
if not all([FTP_HOST, FTP_USER, FTP_PASS]):
    logger.error("FTP credentials are not set in the environment variables.")
    exit(1)

# Function to scrape data from the first source
def scrape_first_source():
    url = "https://nepsealpha.com/live-market"
    
    # Adding User-Agent header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {
            "Date": soup.select_one("td:contains('Date') + td").text.strip(),
            "Current": soup.select_one("td:contains('Current') + td").text.strip(),
            "Daily Gain": soup.select_one("td:contains('Daily Gain') + td span").text.strip(),
            "Turnover": soup.select_one("td:contains('Turnover') + td").text.strip(),
            "Previous Close": soup.select_one("td:contains('Previous Close') + td").text.strip(),
            "Positive Stocks": soup.select_one("td:contains('Positive Stocks') + td span").text.strip(),
            "Neutral Stocks": soup.select_one("td:contains('Neutral Stocks') + td span").text.strip(),
            "Negative Stocks": soup.select_one("td:contains('Negative Stocks') + td span").text.strip(),
            "Total Turnover Rs": soup.select_one("th:contains('Total Turnover Rs:') + td").text.strip(),
            "Total Traded Shares": soup.select_one("th:contains('Total Traded Shares') + td").text.strip(),
            "Total Transactions": soup.select_one("th:contains('Total Transactions') + td").text.strip(),
            "Total Scrips Traded": soup.select_one("th:contains('Total Scrips Traded') + td").text.strip(),
            "Total Float Market Capitalization Rs": soup.select_one("th:contains('Total Float Market Capitalization Rs:') + td").text.strip(),
            "NEPSE Market Cap": soup.select_one("th:contains('NEPSE Market Cap') + td").text.strip(),
        }
        return data
    except Exception as e:
        logger.error(f"Failed to retrieve data: {e}")
        return None

# Function to generate HTML from the scraped data
def generate_html(data):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1 {{ text-align: center; font-size: 24px; margin: 20px 0; }}
            table {{ width: 80%; margin: 20px auto; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .footer {{ text-align: center; margin: 20px; font-size: 14px; color: gray; }}
        </style>
    </head>
    <body>
        <h1>NEPSE Live Market Data</h1>
        <table>
            <tr>
                <th>Field</th>
                <th>Value</th>
            </tr>
    """
    for key, value in data.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    
    html += f"""
        </table>
        <div class="footer">Updated on: {updated_time}</div>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
        logger.info("File uploaded successfully to FTP server.")
    except Exception as e:
        logger.error(f"Failed to upload file to FTP server: {e}")

# Refresh Data
def refresh_data():
    data = scrape_first_source()
    if data:
        html_content = generate_html(data)
        upload_to_ftp(html_content)
    else:
        logger.error("No data to upload.")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
