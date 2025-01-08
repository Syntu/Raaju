from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import ftplib
import os
import logging
import traceback
from flask import Flask, jsonify
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

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

# Function to create WebDriver for Selenium
def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode for server
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.binary_location = "/usr/bin/chromium"  # Set Chromium binary path

    # Use ChromeDriverManager to automatically download the correct driver version
    driver = webdriver.Chrome(service=Service(ChromeDriverManager(version="131.0.6778.204").install()), options=chrome_options)
    return driver

# Function to scrape NEPSE data using Selenium
def scrape_nepse_data():
    try:
        driver = create_webdriver()
        URL = "https://www.sharesansar.com/stock-heat-map/volume"
        driver.get(URL)

        # Wait for elements to load
        wait = WebDriverWait(driver, 10)
        nepse_index = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nepse-index-value"))).text
        as_of = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "date-as-of"))).text

        driver.quit()
        return {"nepse_index": nepse_index, "as_of": as_of}
    except Exception as e:
        logging.error(f"Error scraping NEPSE data: {e}")
        logging.error(traceback.format_exc())
        return None

# Function to generate HTML content
def generate_html(data):
    html_content = f"""
    <html>
    <head><title>NEPSE Data</title></head>
    <body>
        <h1>NEPSE Data</h1>
        <p><strong>NEPSE Index:</strong> {data['nepse_index']}</p>
        <p><strong>As of:</strong> {data['as_of']}</p>
    </body>
    </html>
    """
    return html_content

# Function to upload HTML to FTP server
def upload_to_ftp(html_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            ftp.cwd("/htdocs")  # FTP path, modify if necessary
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR index.html", f)
        logging.info("Successfully uploaded data to FTP server.")
    except Exception as e:
        logging.error(f"Error uploading to FTP: {e}")
        logging.error(traceback.format_exc())

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
    return jsonify({"status": "running", "message": "NEPSE scraper is running!"})

# Main function
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_data, "interval", minutes=REFRESH_INTERVAL)
    scheduler.start()

    # Initial data refresh
    refresh_data()

    # Start Flask app
    app.run(host="0.0.0.0", port=PORT)
