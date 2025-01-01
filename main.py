import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

# Function to scrape data from the first code
def scrape_main_data():
    url = "https://nepsealpha.com/live-market"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        data = {
            "Date": soup.select_one("td:contains('Date') + td").text.strip(),
            "Current": soup.select_one("td:contains('Current') + td").text.strip(),
            "Daily Gain": soup.select_one("td:contains('Daily Gain') + td span").text.strip(),
            "Turnover": soup.select_one("td:contains('Turnover') + td").text.strip(),
            "Previous Close": soup.select_one("td:contains('Previous Close') + td").text.strip(),
            "Positive Stocks": soup.select_one("td:contains('Positive Stocks') + td span").text.strip(),
            "Neutral Stocks": soup.select_one("td:contains('Neutral Stocks') + td span").text.strip(),
            "Negative Stocks": soup.select_one("td:contains('Negative Stocks') + td span").text.strip(),
            "Total Turnover Rs": soup.select_one("th:contains('Total Turnover Rs:') + td").text.strip(),
            "Total Traded Shares": soup.select_one("th:contains('Total Traded Shares') + td").text.strip(),
            "Total Transactions": soup.select_one("th:contains('Total Transactions') + td").text.strip(),
            "Total Scrips Traded": soup.select_one("th:contains('Total Scrips Traded') + td").text.strip(),
            "Total Float Market Capitalization Rs": soup.select_one("th:contains('Total Float Market Capitalization Rs:') + td").text.strip(),
            "NEPSE Market Cap": soup.select_one("th:contains('NEPSE Market Cap') + td").text.strip(),
        }
        return data
    else:
        return {}

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
            high = today["52 Week High"]
            low = today["52 Week Low"]
            ltp = live["LTP"]
            down_from_high = (float(high) - float(ltp)) / float(high) * 100 if high != "N/A" and ltp != "N/A" else "N/A"
            up_from_low = (float(ltp) - float(low)) / float(low) * 100 if low != "N/A" and ltp != "N/A" else "N/A"
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
                "52 Week Low": today["52 Week Low"],
                "Down From High (%)": f"{down_from_high:.2f}" if isinstance(down_from_high, float) else "N/A",
                "Up From Low (%)": f"{up_from_low:.2f}" if isinstance(up_from_low, float) else "N/A"
            })
    return merged

# Function to generate HTML
def generate_html(main_table, first_code_data):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    first_code_table = "<table border='1'><tr><th>Key</th><th>Value</th></tr>"
    for key, value in first_code_data.items():
        first_code_table += f"<tr><td>{key}</td><td>{value}</td></tr>"
    first_code_table += "</table>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>NEPSE Data</h1>
        <div>Updated on: {updated_time}</div>
        {first_code_table}
        <!-- Additional Search Box and Main Table -->
        <div>...Rest of the code...</div>
    </body>
    </html>
    """
    return html

# Refresh Data
def refresh_data():
    first_code_data = scrape_main_data()
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    html_content = generate_html(merged_data, first_code_data)
    upload_to_ftp(html_content)

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=15)
scheduler.start()

# Initial Data Refresh
refresh_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
