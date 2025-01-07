from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import ftplib
import os
import logging
import time
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 15))  # in minutes

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask app initialization
app = Flask(__name__)

# Function to scrape NEPSE data using Selenium
def scrape_nepse_data():
    try:
        # Set up Chrome options for headless browsing
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # ChromeDriver path
        service = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)

        # Access NEPSE Live Market page
        url = "https://nepsealpha.com/live-market"
        driver.get(url)

        # Allow time for the page to load
        time.sleep(5)

        # Scrape required data
        data = {
            'Date': driver.find_element(By.ID, "marketDate").text,
            'Current': driver.find_element(By.ID, "marketCurrent").text,
            'Daily Gain': driver.find_element(By.ID, "dailyGain").text,
            'Turnover': driver.find_element(By.ID, "marketTurnover").text,
            'Previous Close': driver.find_element(By.ID, "previousClose").text,
            'Positive Stock': driver.find_element(By.ID, "positiveStock").text,
            'Neutral Stock': driver.find_element(By.ID, "neutralStock").text,
            'Negative Stock': driver.find_element(By.ID, "negativeStock").text,
        }

        driver.quit()
        logging.info(f"Scraped Data: {data}")
        return data
    except Exception as e:
        logging.error(f"Error in scraping NEPSE data: {e}")
        return None

# Function to generate HTML content
def generate_html(data):
    html_content = f"""
    <html>
    <head><title>NEPSE Data</title></head>
    <body>
        <h1>NEPSE Live Data</h1>
        <ul>
            <li>Date: {data.get('Date', 'N/A')}</li>
            <li>Current: {data.get('Current', 'N/A')}</li>
            <li>Daily Gain: {data.get('Daily Gain', 'N/A')}</li>
            <li>Turnover: {data.get('Turnover', 'N/A')}</li>
            <li>Previous Close: {data.get('Previous Close', 'N/A')}</li>
            <li>Positive Stock: {data.get('Positive Stock', 'N/A')}</li>
            <li>Neutral Stock: {data.get('Neutral Stock', 'N/A')}</li>
            <li>Negative Stock: {data.get('Negative Stock', 'N/A')}</li>
        </ul>
    </body>
    </html>
    """
    return html_content

# Function to upload HTML to FTP server
def upload_to_ftp(html_content):
    try:
        # Save HTML content to file
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Connect to FTP server and upload file
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")  # Change to your desired directory
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
        logging.info("Successfully uploaded data to FTP server.")
    except Exception as e:
        logging.error(f"Error uploading to FTP: {e}")

# Function to refresh data
def refresh_data():
    logging.info("Refreshing data...")
    data = scrape_nepse_data()
    if data:
        html_content = generate_html(data)
        upload_to_ftp(html_content)
    else:
        logging.error("Failed to scrape NEPSE data. Skipping upload.")

# Flask route
@app.route("/")
def home():
    return "NEPSE scraper is running!"

# Main function
if __name__ == "__main__":
    from apscheduler.schedulers.background import BackgroundScheduler

    # Scheduler to refresh data
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data, "interval", minutes=REFRESH_INTERVAL)
    scheduler.start()

    # Initial data refresh
    refresh_data()

    # Start Flask app
    app.run(host="0.0.0.0", port=PORT)
