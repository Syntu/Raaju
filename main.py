from flask import Flask
import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Load environment variables
FTP_HOST = os.getenv("FTP_HOST", "your-default-ftp-host")
FTP_USER = os.getenv("FTP_USER", "your-default-ftp-user")
FTP_PASS = os.getenv("FTP_PASS", "your-default-ftp-pass")

app = Flask(__name__)

# Function to fetch data from a given URL
def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

# Function to scrape live trading data
def scrape_live_trading():
    soup = fetch_data("https://www.sharesansar.com/live-trading")
    if not soup:
        return []
    rows = soup.find_all("tr")
    data = [
        {
            "Symbol": row.find_all("td")[1].text.strip(),
            "LTP": row.find_all("td")[2].text.strip().replace(",", ""),
            "Change%": row.find_all("td")[4].text.strip(),
            "Day High": row.find_all("td")[6].text.strip().replace(",", ""),
            "Day Low": row.find_all("td")[7].text.strip().replace(",", ""),
            "Previous Close": row.find_all("td")[9].text.strip().replace(",", ""),
            "Volume": row.find_all("td")[8].text.strip().replace(",", ""),
        }
        for row in rows if len(row.find_all("td")) > 1
    ]
    return data

# Function to scrape today's share price
def scrape_today_share_price():
    soup = fetch_data("https://www.sharesansar.com/today-share-price")
    if not soup:
        return []
    rows = soup.find_all("tr")
    data = [
        {
            "SN": row.find_all("td")[0].text.strip(),
            "Symbol": row.find_all("td")[1].text.strip(),
            "Turnover": row.find_all("td")[10].text.strip().replace(",", ""),
            "52 Week High": row.find_all("td")[19].text.strip().replace(",", ""),
            "52 Week Low": row.find_all("td")[20].text.strip().replace(",", ""),
        }
        for row in rows if len(row.find_all("td")) > 1
    ]
    return data

# Function to merge live trading data with today's share price
def merge_data(live_data, today_data):
    today_dict = {item["Symbol"]: item for item in today_data}
    merged = []
    for live in live_data:
        symbol = live["Symbol"]
        today = today_dict.get(symbol, {})
        merged.append({
            "SN": today.get("SN", "-"),
            "Symbol": symbol,
            "LTP": live["LTP"],
            "Change%": live["Change%"],
            "Day High": live["Day High"],
            "Day Low": live["Day Low"],
            "Previous Close": live["Previous Close"],
            "Volume": live["Volume"],
            "Turnover": today.get("Turnover", "N/A"),
            "52 Week High": today.get("52 Week High", "N/A"),
            "52 Week Low": today.get("52 Week Low", "N/A"),
        })
    return merged

# Function to calculate additional columns for the table
def calculate_additional_tables(data):
    for row in data:
        try:
            ltp = float(row["LTP"])
            high = float(row["52 Week High"]) if row["52 Week High"] != "N/A" else None
            low = float(row["52 Week Low"]) if row["52 Week Low"] != "N/A" else None
            row["Down From High"] = f"{((high - ltp) / high * 100):.2f}%" if high else "N/A"
            row["Up From Low"] = f"{((ltp - low) / low * 100):.2f}%" if low else "N/A"
        except ValueError:
            row["Down From High"] = "N/A"
            row["Up From Low"] = "N/A"
    return data

# Function to generate HTML table
def generate_html(data, update_time):
    rows = ""
    for i, row in enumerate(data, 1):
        rows += f"""
        <tr>
            <td>{i}</td>
            <td>{row['Symbol']}</td>
            <td>{row['LTP']}</td>
            <td>{row['Change%']}</td>
            <td>{row['Day High']}</td>
            <td>{row['Day Low']}</td>
            <td>{row['Previous Close']}</td>
            <td>{row['Volume']}</td>
            <td>{row['Turnover']}</td>
            <td>{row['52 Week High']}</td>
            <td>{row['52 Week Low']}</td>
            <td>{row['Down From High']}</td>
            <td>{row['Up From Low']}</td>
        </tr>
        """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <p>Updated on: {update_time}</p>
        <table>
            <thead>
                <tr>
                    <th>SN</th>
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
                    <th>Down From High</th>
                    <th>Up From Low</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

# Function to upload HTML to FTP
def upload_to_ftp(html_content):
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        ftp.storlines("STOR index.html", html_content.splitlines())

# Scheduled task to fetch data, process, and upload
def scheduled_task():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    final_data = calculate_additional_tables(merged_data)
    update_time = datetime.now(pytz.timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html_content = generate_html(final_data, update_time)
    upload_to_ftp(html_content)

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, "interval", minutes=15)
scheduler.start()

# Flask route for testing
@app.route("/")
def home():
    return "NEPSE Data Service is Running!"

# Main
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
