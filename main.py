import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
import random

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

# Function to fetch data from ShareHub Nepal
def fetch_data():
    url = "https://sharehubnepal.com/nepse/indices"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Send request to the website
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the table
    table = soup.find("table")
    if not table:
        print("Table not found on the webpage.")
        return []

    rows = table.find_all("tr")[1:]  # Skip header row

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

    # Scramble the data
    random.shuffle(data)

    # Ensure predefined indices are included and update their values if available
    for predefined in PREDEFINED_INDICES:
        for fetched in data:
            if fetched["indices"] == predefined["indices"]:
                predefined.update(fetched)
                break

    # Combine predefined and fetched data
    all_data = PREDEFINED_INDICES + [row for row in data if row["indices"] not in {p["indices"] for p in PREDEFINED_INDICES}]
    return all_data

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
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh data and upload to FTP
def refresh_data():
    data = fetch_data()
    html_content = generate_html(data)
    upload_to_ftp(html_content)

# Scheduler to refresh data periodically
scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
scheduler.add_job(refresh_data, "cron", hour=4, minute=0)
scheduler.start()

# Initial data refresh
refresh_data()

# Keep running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
