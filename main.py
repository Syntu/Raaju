import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from ftplib import FTP
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

app = Flask(__name__)

# Global HTML content
html_content = ""

# Function to scrape live trading data
def scrape_live_trading_data():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    table_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 10:
            table_data.append([
                cells[0].text.strip(),  # SN
                cells[1].text.strip(),  # Symbol
                cells[2].text.strip(),  # LTP
                cells[4].text.strip(),  # Change%
                cells[6].text.strip(),  # Day High
                cells[7].text.strip(),  # Day Low
                cells[9].text.strip(),  # Previous Close
                cells[8].text.strip()   # Volume
            ])
    return table_data

# Function to scrape summary data
def scrape_summary_data():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table_data = soup.find_all("td")
    return {
        "Turnover": table_data[10].text.strip() if len(table_data) > 10 else "N/A",
        "52 Week High": table_data[19].text.strip() if len(table_data) > 19 else "N/A",
        "52 Week Low": table_data[20].text.strip() if len(table_data) > 20 else "N/A",
    }

# Function to calculate additional columns
def calculate_additional_data(table_data, summary_data):
    updated_data = []
    for row in table_data:
        try:
            ltp = float(row[2].replace(",", ""))
            high = float(summary_data["52 Week High"].replace(",", ""))
            low = float(summary_data["52 Week Low"].replace(",", ""))
            down_from_high = f"{((high - ltp) / high) * 100:.2f}%" if high else "N/A"
            up_from_low = f"{((ltp - low) / low) * 100:.2f}%" if low else "N/A"
        except ValueError:
            down_from_high = "N/A"
            up_from_low = "N/A"
        updated_data.append(row + [down_from_high, up_from_low])
    return updated_data

# Function to generate HTML table
def generate_html(table_data, summary_data):
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
                <th>SN</th>
                <th>Symbol</th>
                <th>LTP</th>
                <th>Change%</th>
                <th>Day High</th>
                <th>Day Low</th>
                <th>Previous Close</th>
                <th>Volume</th>
                <th>Down From High</th>
                <th>Up From Low</th>
            </tr>
    """
    for row in table_data:
        html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    html += f"""
        </table>
        <h2>Summary</h2>
        <p>Turnover: {summary_data['Turnover']}</p>
        <p>52 Week High: {summary_data['52 Week High']}</p>
        <p>52 Week Low: {summary_data['52 Week Low']}</p>
    </body>
    </html>
    """
    return html

# Function to refresh HTML content
def refresh_html():
    global html_content
    print("Scraping data...")
    table_data = scrape_live_trading_data()
    summary_data = scrape_summary_data()
    updated_data = calculate_additional_data(table_data, summary_data)
    print("Generating HTML...")
    html_content = generate_html(updated_data, summary_data)
    upload_to_ftp("index.html", html_content)
    print("HTML updated and uploaded!")

# Function to upload the file to FTP server
def upload_to_ftp(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)
    with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/")
        with open(filename, "rb") as file:
            ftp.storbinary(f"STOR {filename}", file)
    print(f"{filename} uploaded to FTP server.")

# Define Flask route
@app.route("/")
def home():
    return html_content or "<h1>Loading data...</h1>"

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_html, "interval", minutes=5)
scheduler.start()

# Refresh data initially
refresh_html()

# Start the server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default port 5000
    app.run(host="0.0.0.0", port=port)
