import os
import time
import logging
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", 15))  # Interval in minutes

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Flask App Initialization
app = Flask(__name__)

# Function to scrape NEPSE data using Selenium
def scrape_nepse_data():
    try:
        # Setup Chrome options for headless browsing
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.binary_location = os.getenv("GOOGLE_CHROME_BIN")  # Chrome binary location

        # ChromeDriver setup
        service = Service(os.getenv("CHROMEDRIVER_PATH"))
        driver = webdriver.Chrome(service=service, options=options)

        # Open NEPSE Alpha live market page
        url = "https://nepsealpha.com/live-market"
        driver.get(url)

        # Wait for the page to load
        time.sleep(5)

        # Extract required data
        data = {
            "Date": driver.find_element(By.XPATH, '//span[@id="marketDate"]').text,
            "Current": driver.find_element(By.XPATH, '//span[@id="marketCurrent"]').text,
            "Daily Gain": driver.find_element(By.XPATH, '//span[@id="dailyGain"]').text,
            "Turnover": driver.find_element(By.XPATH, '//span[@id="marketTurnover"]').text,
            "Previous Close": driver.find_element(By.XPATH, '//span[@id="previousClose"]').text,
            "Positive Stock": driver.find_element(By.XPATH, '//span[@id="positiveStock"]').text,
            "Neutral Stock": driver.find_element(By.XPATH, '//span[@id="neutralStock"]').text,
            "Negative Stock": driver.find_element(By.XPATH, '//span[@id="negativeStock"]').text,
        }

        driver.quit()
        logging.info("Successfully scraped NEPSE data.")
        return data
    except Exception as e:
        logging.error(f"Error in scraping NEPSE data: {e}")
        return None

# Generate HTML content from data
def generate_html(data):
    html_content = f"""
    <html>
    <head><title>NEPSE Live Data</title></head>
    <body>
        <h1>NEPSE Live Data</h1>
        {"".join(f"<p><strong>{key}:</strong> {value}</p>" for key, value in data.items())}
    </body>
    </html>
    """
    return html_content

# Upload HTML content to FTP server
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")
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
        logging.error("Failed to scrape NEPSE data. Skipping upload.")

# Scheduler to update data
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=REFRESH_INTERVAL)
scheduler.start()

# Initial data refresh
refresh_data()

# Flask route to keep the server running
@app.route("/")
def home():
    return "NEPSE data scraper is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
