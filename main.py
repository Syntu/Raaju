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

# Function to scrape data from the first source
def scrape_first_source():
    url = "https://nepsealpha.com/live-market"
    response = requests.get(url)
    if response.status_code == 200:
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
    else:
        raise Exception(f"Failed to retrieve data. HTTP Status code: {response.status_code}")

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
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    data = scrape_first_source()
    html_content = generate_html(data)
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
