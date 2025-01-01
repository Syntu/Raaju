import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
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
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Debugging: print the status code and HTML content to check the structure
    print("Response Status Code:", response.status_code)
    print("HTML Content:\n", response.text[:1000])  # Print first 1000 characters to check the structure

    data = {}

    try:
        # Improved CSS selector to extract "As of"
        as_of = soup.find('span', text="As of :")
        data["as_of"] = as_of.find_next('span').text.strip() if as_of else "N/A"
    except AttributeError:
        data["as_of"] = "N/A"
    
    try:
        # Improved CSS selector to extract "NEPSE Index"
        nepse_index = soup.find('span', text="NEPSE Index :")
        data["nepse_index"] = nepse_index.find_next('span').text.strip() if nepse_index else "N/A"
    except AttributeError:
        data["nepse_index"] = "N/A"
    
    return data

# Function to generate HTML with CSS
def generate_html(data):
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sharesansar Data</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: #fff;
                margin-top: 20px;
            }}
            td {{
                padding: 10px;
                border: 1px solid #ddd;
            }}
            .text-left {{
                text-align: left;
                font-weight: bold;
            }}
            .text-bold {{
                font-weight: bold;
            }}
            h1 {{
                color: #333;
                text-align: center;
                font-size: 24px;
            }}
            #as-of, #nepse-index {{
                color: #4CAF50;
            }}
        </style>
    </head>
    <body>
        <h1>Sharesansar Stock Data</h1>
        <table>
            <tr>
                <td class="text-left">As of</td>
                <td id="as-of">{data['as_of']}</td>
            </tr>
            <tr>
                <td class="text-left">NEPSE Index</td>
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
