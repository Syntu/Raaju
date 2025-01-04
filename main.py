import os
import logging
import ftplib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Flask app
app = Flask(__name__)

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fetch data using Selenium
def fetch_data():
    url = "https://sharehubnepal.com/nepse/indices"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    # Set the binary location of Google Chrome for Render environment
    options.binary_location = "/usr/bin/google-chrome"  # Adjust path as needed for your environment

    try:
        # Selenium driver setup
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        
        # Wait for the page to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        # Find table data
        table = soup.find('table', {'id': 'indices'})
        if not table:
            logging.error("Table not found on the webpage.")
            return []
        
        rows = table.find_all('tr')[1:]  # Skip header row
        indices_data = []
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 6:
                indices_data.append({
                    "Indices": columns[0].text.strip(),
                    "Value": columns[1].text.strip(),
                    "Ch": columns[2].text.strip(),
                    "Ch%": columns[3].text.strip(),
                    "HIGH": columns[4].text.strip(),
                    "LOW": columns[5].text.strip(),
                })
        return indices_data
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
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Indices</h1>
        <table>
            <tr>
                <th>Indices</th>
                <th>Value</th>
                <th>Ch</th>
                <th>Ch%</th>
                <th>HIGH</th>
                <th>LOW</th>
            </tr>
    """
    for row in data:
        html += f"""
        <tr>
            <td>{row['Indices']}</td>
            <td>{row['Value']}</td>
            <td>{row['Ch']}</td>
            <td>{row['Ch%']}</td>
            <td>{row['HIGH']}</td>
            <td>{row['LOW']}</td>
        </tr>
        """
    html += """
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
