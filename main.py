import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
import random
import logging

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Predefined indices to always include
PREDEFINED_INDICES = [
    {"indices": "NEPSE Index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Sensitive index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Sensitive Float index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Float Index", "value": "-", "change_point": "-", "change_percent": "-"},
]

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to fetch data from ShareHub Nepal
def fetch_data():
    url = "https://sharehubnepal.com/nepse/indices"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        # Send request to the website
        response = requests.get(url, headers=headers, timeout=10)
        logging.info("Response Status Code: %s", response.status_code)

        if response.status_code != 200:
            logging.error("Failed to fetch data. HTTP Status Code: %s", response.status_code)
            return []

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")
        logging.info("Parsing HTML content...")
        
        # Debug: Print part of the HTML
        logging.debug("HTML Preview: %s", response.content[:500])
        
        # Find the table
        table = soup.find("table")
        if not table:
            logging.error("Table not found on the webpage.")
            return []

        rows = table.find_all("tr")[1:]  # Skip header row
        logging.info("Found %d rows in the table.", len(rows))

        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:  # Ensure there are at least 4 columns
                indices = cols[0].text.strip()
                value = cols[1].text.strip()
                change_point = cols[2].text.strip()
                change_percent = cols[3].text.strip()
                data.append({
                    "indices": indices,
                    "value": value,
                    "change_point": change_point,
                    "change_percent": change_percent
                })

        logging.info("Fetched Data: %s", data)
        return data

    except Exception as e:
        logging.error("Error fetching or parsing data: %s", str(e))
        return []

# Function to generate HTML table
def generate_html(data):
    html = """
    <html>
        <head>
            <title>NEPSE Indices</title>
            <style>
                table {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: Arial, sans-serif;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f4f4f4;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
            </style>
        </head>
        <body>
            <h2>NEPSE Indices</h2>
            <table>
                <thead>
                    <tr>
                        <th>Indices</th>
                        <th>Value</th>
                        <th>Change Point</th>
                        <th>Change Percent</th>
                    </tr>
                </thead>
                <tbody>
    """
    for row in data:
        html += f"""
        <tr>
            <td>{row['indices']}</td>
            <td>{row['value']}</td>
            <td>{row['change_point']}</td>
            <td>{row['change_percent']}</td>
        </tr>
        """
    html += """
                </tbody>
            </table>
        </body>
    </html>
    """
    return html

# Upload HTML file to FTP
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)

        logging.info("Successfully uploaded HTML file to FTP.")
    except Exception as e:
        logging.error("Error uploading to FTP: %s", str(e))

# Refresh data and upload to FTP
def refresh_data():
    data = fetch_data()
    if data:
        html_content = generate_html(data)
        logging.info("Generated HTML content.")
        upload_to_ftp(html_content)
    else:
        logging.error("No data fetched to upload.")

# Scheduler to refresh data periodically
scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
scheduler.add_job(refresh_data, "cron", hour=4, minute=0)
scheduler.start()

# Initial data refresh
refresh_data()

# Keep running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
