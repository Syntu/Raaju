import os
import ftplib
import pytz
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Set timezone
NEPAL_TIMEZONE = pytz.timezone("Asia/Kathmandu")

# Global variable for last updated data
LAST_UPDATED_DATA = None
LAST_UPDATED_TIME = None

# Function to scrape live trading data
def scrape_live_trading():
    url = "https://www.sharesansar.com/live-trading"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "Symbol": cells[1].text.strip(),
                "LTP": cells[2].text.strip().replace(",", ""),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip().replace(",", ""),
                "Day Low": cells[7].text.strip().replace(",", ""),
                "Previous Close": cells[9].text.strip().replace(",", ""),
                "Volume": cells[8].text.strip().replace(",", "")
            })
    return data

# Function to scrape today's share price summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "SN": cells[0].text.strip(),
                "Symbol": cells[1].text.strip(),
                "Turnover": cells[10].text.strip().replace(",", ""),
                "52 Week High": cells[19].text.strip().replace(",", ""),
                "52 Week Low": cells[20].text.strip().replace(",", "")
            })
    return data

# Function to merge live and today's data
def merge_data(live_data, today_data):
    merged = []
    today_dict = {item["Symbol"]: item for item in today_data}
    for live in live_data:
        symbol = live["Symbol"]
        if symbol in today_dict:
            today = today_dict[symbol]
            merged.append({
                "SN": today["SN"],
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Turnover": today["Turnover"],
                "52 Week High": today["52 Week High"],
                "52 Week Low": today["52 Week Low"]
            })
        else:
            # If no match found, use live data with defaults
            merged.append({
                "SN": "-",
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Turnover": "N/A",
                "52 Week High": "N/A",
                "52 Week Low": "N/A"
            })
    return merged

# Function to generate HTML
def generate_html(main_table, last_updated_time):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {width: 100%; border-collapse: collapse; margin-top: 20px;}
            th, td {border: 1px solid #ddd; padding: 8px; text-align: center;}
            th {background-color: #8B4513; color: white; position: sticky; top: 0;}
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <table>
            <tr>
                <th>SN</th><th>Symbol</th><th>LTP</th><th>Change%</th><th>Day High</th>
                <th>Day Low</th><th>Previous Close</th><th>Volume</th>
                <th>Turnover</th><th>52 Week High</th><th>52 Week Low</th>
            </tr>
    """
    for row in main_table:
        html += f"""
            <tr>
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td>{row["Change%"]}</td><td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td><td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td>
            </tr>
        """
    html += f"""
        </table>
        <p style="text-align: center; margin-top: 20px;">
            Updated on: {last_updated_time.strftime('%Y-%m-%d %H:%M:%S %p')}
        </p>
    </body>
    </html>
    """
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Check if within market hours
def is_market_open():
    now = datetime.now(NEPAL_TIMEZONE)
    market_open_time = time(10, 45)
    market_close_time = time(15, 10)
    return now.weekday() in range(5) and market_open_time <= now.time() <= market_close_time

# Refresh Data
def refresh_data():
    global LAST_UPDATED_DATA, LAST_UPDATED_TIME
    if is_market_open():
        print("Fetching data...")
        live_data = scrape_live_trading()
        today_data = scrape_today_share_price()
        LAST_UPDATED_DATA = merge_data(live_data, today_data)
        LAST_UPDATED_TIME = datetime.now(NEPAL_TIMEZONE)
        print("Data refreshed.")
    else:
        print("Market closed. Using last available data.")

    if LAST_UPDATED_DATA:
        html_content = generate_html(LAST_UPDATED_DATA, LAST_UPDATED_TIME)
        upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler(timezone=NEPAL_TIMEZONE)
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
try:
    while True:
        pass
except KeyboardInterrupt:
    scheduler.shutdown()
