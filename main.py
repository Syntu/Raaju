import os
import ftplib
import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask
import requests

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

# Function to scrape NEPSE data (with retry mechanism)
def scrape_nepse_data():
    url = "https://www.sharesansar.com/stock-heat-map/volume"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                date = soup.find("span", class_="text-org dDate")
                index = soup.find("li", id="infoIndex")
                
                if date and index:
                    date_text = date.text.strip()
                    nepse_index = index.find("span", class_="text-org dIndex").text.strip()
                    logging.info("Successfully scraped NEPSE data.")
                    return {"date": date_text, "nepse_index": nepse_index}
                else:
                    logging.warning("Could not find required data on the page.")
            else:
                logging.warning(f"HTTP Error: {response.status_code}")
        except Exception as e:
            logging.error(f"Error in scraping attempt {attempt + 1}: {e}")
        time.sleep(5)  # Wait 5 seconds before retrying
    logging.error("Failed to scrape data after 3 attempts.")
    return None

# Selenium fallback method for scraping
def scrape_with_selenium():
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(), options=options)
        driver.get("https://www.sharesansar.com/stock-heat-map/volume")
        time.sleep(5)  # Wait for the page to load

        date_element = driver.find_element(By.CLASS_NAME, "dDate")
        index_element = driver.find_element(By.CLASS_NAME, "dIndex")

        data = {
            "date": date_element.text.strip(),
            "nepse_index": index_element.text.strip()
        }
        driver.quit()
        logging.info("Successfully scraped data with Selenium.")
        return data
    except Exception as e:
        logging.error(f"Selenium scraping failed: {e}")
        return None

# Generate HTML content
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
    if not data:
        logging.warning("Retrying with Selenium...")
        data = scrape_with_selenium()
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
