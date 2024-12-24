import os
from ftplib import FTP
from apscheduler.schedulers.blocking import BlockingScheduler
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve FTP credentials from environment variables
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

if not FTP_HOST or not FTP_USER or not FTP_PASS:
    raise ValueError("Missing FTP credentials in environment variables")

# Function to scrape today's share price data
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    table_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            table_data.append([cell.text.strip() for cell in cells])
    return table_data

# Function to generate HTML table
def generate_html(table_data):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
                text-align: center;
            }
            td {
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <tr>
                <th>Symbol</th>
                <th>LTP</th>
                <th>Change</th>
                <th>High</th>
                <th>Low</th>
                <th>Volume</th>
            </tr>
    """
    for row in table_data:
        html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row[:6]) + "</tr>"
    html += """
        </table>
    </body>
    </html>
    """
    return html

# Function to upload file to FTP server
def upload_to_ftp(file_content):
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(file_content)
        
        with FTP(FTP_HOST) as ftp:
            ftp.login(FTP_USER, FTP_PASS)
            with open("index.html", "rb") as f:
                ftp.storbinary("STOR /htdocs/index.html", f)
        print("File uploaded successfully!")
    except Exception as e:
        print(f"Error uploading file: {e}")

# Function to refresh data and update index.html
def update_website():
    print("Scraping data...")
    table_data = scrape_today_share_price()
    print("Generating HTML...")
    html_content = generate_html(table_data)
    print("Uploading to FTP...")
    upload_to_ftp(html_content)

# Initialize scheduler
scheduler = BlockingScheduler()
scheduler.add_job(update_website, "interval", minutes=5)

# Start the script
if __name__ == "__main__":
    print("Starting script...")
    update_website()  # Run once at the start
    scheduler.start()