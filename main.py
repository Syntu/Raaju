import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string
import json

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Fetch NEPSE data function
def fetch_nepse_indices():
    url = "https://sharehubnepal.com/nepse/indices"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    # Send request to the website
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status Code: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table
    table = soup.find('table', {'class': 'min-w-max w-full caption-bottom border-collapse'})
    if not table:
        print("Table not found. Verify the table class.")
        return []

    # Extract data from the table
    indices_data = []
    rows = table.find('tbody').find_all('tr')  # Locate all rows inside <tbody>
    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 6:  # Ensure there are enough columns
            indices = columns[0].text.strip()
            value = columns[1].text.strip()
            ch = columns[2].text.strip()
            ch_percent = columns[3].text.strip()
            high = columns[4].text.strip()
            low = columns[5].text.strip()

            indices_data.append({
                "Indices": indices,
                "Value": value,
                "Ch": ch,
                "Ch%": ch_percent,
                "HIGH": high if high != "N/A" else None,
                "LOW": low if low != "N/A" else None
            })

    return indices_data

# Function to generate HTML
def generate_html(main_table):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Indices Data</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 8px 12px;
                text-align: center;
                border: 1px solid #ddd;
            }}
            th {{
                background-color: #f4f4f4;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 0.9em;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <h1>NEPSE Indices</h1>
        <table>
            <thead>
                <tr>
                    <th>Indices</th>
                    <th>Value</th>
                    <th>Change</th>
                    <th>Change (%)</th>
                    <th>High</th>
                    <th>Low</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add the data rows
    for data in main_table:
        html += f"""
        <tr>
            <td>{data['Indices']}</td>
            <td>{data['Value']}</td>
            <td>{data['Ch']}</td>
            <td>{data['Ch%']}</td>
            <td>{data['HIGH'] if data['HIGH'] else "N/A"}</td>
            <td>{data['LOW'] if data['LOW'] else "N/A"}</td>
        </tr>
        """
    
    # Close table and add footer
    html += f"""
            </tbody>
        </table>
        <div class="footer">Data last updated: {updated_time}</div>
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
    data = fetch_nepse_indices()
    if data:
        html_content = generate_html(data)
        upload_to_ftp(html_content)

# Scheduler to run the refresh every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=5)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Flask App to serve the page
@app.route('/')
def index():
    data = fetch_nepse_indices()
    if data:
        html_content = generate_html(data)
        return render_template_string(html_content)
    else:
        return "Failed to fetch data."

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
