import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

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

# Function to calculate additional tables
def calculate_additional_tables(merged_data):
    for row in merged_data:
        try:
            ltp = float(row["LTP"])
            high = float(row["52 Week High"]) if row["52 Week High"] != "N/A" else None
            low = float(row["52 Week Low"]) if row["52 Week Low"] != "N/A" else None

            row["Down From High (%)"] = f"{((high - ltp) / high * 100):.2f}" if high else "N/A"
            row["Up From Low (%)"] = f"{((ltp - low) / low * 100):.2f}" if low else "N/A"
        except ValueError:
            row["Down From High (%)"] = "N/A"
            row["Up From Low (%)"] = "N/A"
    return merged_data

# Function to generate HTML
def generate_html(main_table, update_date_time):
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NEPSE Live Data</title>
        <style>
            body {{font-family: Arial, sans-serif; margin: 20px;}}
            table {{width: 100%; border-collapse: collapse; margin-top: 20px;}}
            th, td {{border: 1px solid #ddd; padding: 8px; text-align: center;}}
            th {{background-color: #8B4513; color: white; position: sticky; top: 0;}}
            .light-red {{background-color: #FFCCCB;}}
            .light-green {{background-color: #D4EDDA;}}
            .light-blue {{background-color: #CCE5FF;}}
            h1 {{font-size: 42px; font-weight: bold; text-align: center; margin-bottom: 0;}}
            .header {{display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;}}
            .footer {{display: flex; justify-content: space-between; font-size: 14px; margin-top: 30px;}}
            .sortable:hover {{cursor: pointer;}}
            th.sortable:after {{content: " ↓"; font-size: 12px;}}
            th.sorted-asc:after {{content: " ↑";}}
            th.sorted-desc:after {{content: " ↓";}}
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div class="header">
            <p class="updated">Updated on: {update_date_time}</p>
            <p class="developer">Developed By: <a href="https://www.syntoo.com" target="_blank">Syntoo</a></p>
        </div>
        <table>
            <thead>
                <tr>
                    <th class="sortable">SN</th>
                    <th class="sortable">Symbol</th>
                    <th class="sortable">LTP</th>
                    <th class="sortable">Change%</th>
                    <th class="sortable">Day High</th>
                    <th class="sortable">Day Low</th>
                    <th class="sortable">Previous Close</th>
                    <th class="sortable">Volume</th>
                    <th class="sortable">Turnover</th>
                    <th class="sortable">52 Week High</th>
                    <th class="sortable">52 Week Low</th>
                    <th class="sortable">Down From High (%)</th>
                    <th class="sortable">Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in main_table:
        change_class = "light-red" if float(row["Change%"]) < 0 else (
            "light-green" if float(row["Change%"]) > 0 else "light-blue")
        html += f"""
            <tr>
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td class="{change_class}">{row["Change%"]}</td><td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td><td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td>
                <td>{row["Down From High (%)"]}</td><td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += "</tbody></table></body></html>"
    return html

# Upload to FTP
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Refresh Data
def refresh_data():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    calculated_data = calculate_additional_tables(merged_data)
    update_date_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html_content = generate_html(calculated_data, update_date_time)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
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
