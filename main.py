import os
import ftplib
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask

# Initialize Flask App
app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 15))  # in minutes

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to scrape NEPSE data
def scrape_nepse_data():
    try:
        url = "https://www.sharesansar.com/stock-heat-map/volume"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extracting Date
        date = soup.find("span", class_="text-org dDate")
        date_text = date.text.strip() if date else "Date not found"
        
        # Extracting NEPSE Index
        index = soup.find("li", id="infoIndex")
        nepse_index = (
            index.find("span", class_="text-org dIndex").text.strip() if index else "Index not found"
        )
        
        logging.info("Successfully scraped NEPSE data.")
        return {"date": date_text, "nepse_index": nepse_index}
    
    except Exception as e:
        logging.error(f"Error while scraping NEPSE data: {e}")
        return None

# Generate HTML content from the scraped data
def generate_html(data):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Data</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; text-align: center; }}
            h1 {{ color: #4CAF50; }}
            .content {{ margin: 20px auto; padding: 20px; border: 1px solid #ccc; background: #fff; max-width: 600px; }}
        </style>
    </head>
    <body>
        <div class="content">
            <h1>NEPSE Data</h1>
            <p><strong>Date:</strong> {data['date']}</p>
            <p><strong>NEPSE Index:</strong> {data['nepse_index']}</p>
        </div>
    </body>
    </html>
    """
    return html_content

# Upload HTML content to the FTP server
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")  # Change to your desired directory
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
        logging.info("Successfully uploaded data to FTP server.")
    except Exception as e:
        logging.error(f"Error while uploading to FTP: {e}")

# Refresh data function
def refresh_data():
    logging.info("Refreshing data...")
    data = scrape_nepse_data()
    if data:
        html_content = generate_html(data)
        upload_to_ftp(html_content)
    else:
        logging.error("Failed to scrape data. Skipping upload.")

# Scheduler to update data
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=REFRESH_INTERVAL)
scheduler.start()

# Initial data refresh
refresh_data()

# Flask app to keep the server running
@app.route("/")
def home():
    return "NEPSE data scraper is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
