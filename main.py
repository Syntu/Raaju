import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import ftplib

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Flask app
app = Flask(__name__)

# Predefined indices
PREDEFINED_INDICES = [
    {"indices": "NEPSE Index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Sensitive index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Sensitive Float index", "value": "-", "change_point": "-", "change_percent": "-"},
    {"indices": "Float Index", "value": "-", "change_point": "-", "change_percent": "-"},
]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch data using Selenium
def fetch_data():
    url = "https://sharehubnepal.com/nepse/indices"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    try:
        # Selenium driver setup
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        
        # Find the table
        table = soup.find("table")
        if not table:
            logging.error("Table not found on the webpage.")
            return []

        rows = table.find_all("tr")[1:]  # Skip header row
        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 4:
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

        logging.info("Data fetched successfully: %s", data)
        return data

    except Exception as e:
        logging.error("Error fetching data: %s", str(e))
        return []

# Generate HTML table
def generate_html(data):
    html = """
    <html>
        <head>
            <title>NEPSE Indices</title>
            <style>
                table { border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f4f4f4; }
                tr:nth-child(even) { background-color: #f9f9f9; }
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

# Upload to FTP
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

# Refresh data and upload
def refresh_data():
    data = fetch_data()
    if data:
        html_content = generate_html(data)
        logging.info("Generated HTML content.")
        upload_to_ftp(html_content)
    else:
        logging.error("No data fetched to upload.")

# Scheduler setup
scheduler = BackgroundScheduler(timezone="Asia/Kathmandu")
scheduler.add_job(refresh_data, "cron", hour=4, minute=0)
scheduler.start()

# Initial data refresh
refresh_data()

# Flask app run
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
