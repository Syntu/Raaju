import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from ftplib import FTP
from dotenv import load_dotenv

# Flask App
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# FTP Configuration from .env
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Global HTML content
html_content = ""

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

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    live_data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            live_data.append([cell.text.strip() for cell in cells])
    return live_data

# Function to generate HTML table
def generate_html(today_data, live_data):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                overflow-x: auto;
                display: block;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <tr>
                <th>Symbol</th>
                <th>LTP</th>
                <th>Change%</th>
                <th>Day High</th>
                <th>Day Low</th>
                <th>Previous Close</th>
                <th>Volume</th>
                <th>Turnover</th>
                <th>52 Week High</th>
                <th>52 Week Low</th>
                <th>Down From High (%)</th>
                <th>Up From Low (%)</th>
            </tr>
    """
    # Match and add data from today's share price and live trading
    for today, live in zip(today_data, live_data):
        symbol = live[1]  # Assuming symbol is in column 2
        ltp = live[2]  # LTP is in column 3
        change = live[4]  # Change% is in column 5
        day_high = live[6]  # Day High is in column 7
        day_low = live[7]  # Day Low is in column 8
        previous_close = live[9]  # Previous Close is in column 10
        volume = live[8]  # Volume is in column 9
        turnover = today[10]  # Turnover from today's share price
        week_high = today[19]  # 52 Week High from today's share price
        week_low = today[20]  # 52 Week Low from today's share price
        
        # Calculate Down From High and Up From Low
        down_from_high = ((float(week_high) - float(ltp)) / float(week_high)) * 100
        up_from_low = ((float(ltp) - float(week_low)) / float(week_low)) * 100

        html += f"""
            <tr>
                <td>{symbol}</td>
                <td>{ltp}</td>
                <td>{change}</td>
                <td>{day_high}</td>
                <td>{day_low}</td>
                <td>{previous_close}</td>
                <td>{volume}</td>
                <td>{turnover}</td>
                <td>{week_high}</td>
                <td>{week_low}</td>
                <td>{down_from_high:.2f}%</td>
                <td>{up_from_low:.2f}%</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    return html

# Function to refresh HTML content
def refresh_html():
    global html_content
    print("Scraping data...")
    today_data = scrape_today_share_price()
    live_data = scrape_live_trading()
    print("Generating HTML...")
    html_content = generate_html(today_data, live_data)
    print("HTML updated!")
    
    # FTP Upload
    upload_to_ftp(html_content)

# FTP Upload Function
def upload_to_ftp(content):
    try:
        print("Connecting to FTP...")
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd('/public_html')  # Ensure you set the correct directory in your FTP
        with open('index.html', 'w') as file:
            file.write(content)
        
        # Upload the file to FTP
        with open('index.html', 'rb') as file:
            ftp.storbinary('STOR index.html', file)
        
        print("File uploaded to FTP successfully!")
        ftp.quit()
    except Exception as e:
        print(f"FTP upload failed: {e}")

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
