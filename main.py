import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template_string

app = Flask(__name__)

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
PORT = int(os.getenv("PORT", 5000))

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

def scrape_listed_security():
    url = "https://sharehubnepal.com/nepse/listed-securities"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    rows = soup.find_all("tr")
    data = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            data.append({
                "Symbol": cells[1].text.strip(),
                "LTP": cells[4].text.strip().replace(",", ""),
                "Change%": cells[3].text.strip(),
                "52 Week High": cells[13].text.strip().replace(",", ""),
                "52 Week Low": cells[14].text.strip().replace(",", ""),
                "Listed Share": cells[5].text.strip().replace(",", ""),
                "Public Share": cells[6].text.strip().replace(",", ""),
                "Market Cap": cells[7].text.strip().replace(",", ""),
                "Paid Up Cap": cells[8].text.strip().replace(",", ""),
                "Float Cap": cells[9].text.strip().replace(",", ""),
                "EPS": cells[10].text.strip().replace(",", ""),
                "Book Value": cells[11].text.strip().replace(",", "")
            })
    return data

# Function to merge live and listed security data
def merge_data(live_data, listed_security_data):
    merged = []
    listed_security_dict = {item["Symbol"]: item for item in listed_security_data}
    for live in live_data:
        symbol = live["Symbol"]
        if symbol in listed_security_dict:
            listed_security = listed_security_dict[symbol]
            high = listed_security["52 Week High"]
            low = listed_security["52 Week Low"]
            ltp = live["LTP"]
            down_from_high = (float(high) - float(ltp)) / float(high) * 100 if high != "N/A" and ltp != "N/A" else "N/A"
            up_from_low = (float(ltp) - float(low)) / float(low) * 100 if low != "N/A" and ltp != "N/A" else "N/A"
            merged.append({
                "Symbol": symbol,
                "LTP": live["LTP"],
                "Change%": live["Change%"],
                "Day High": live["Day High"],
                "Day Low": live["Day Low"],
                "Previous Close": live["Previous Close"],
                "Volume": live["Volume"],
                "Listed Share": listed_security["Listed Share"],
                "Public Share": listed_security["Public Share"],
                "Market Cap": listed_security["Market Cap"],
                "Paid Up Cap": listed_security["Paid Up Cap"],
                "Float Cap": listed_security["Float Cap"],
                "EPS": listed_security["EPS"],
                "Book Value": listed_security["Book Value"],
                "52 Week High": listed_security["52 Week High"],
                "52 Week Low": listed_security["52 Week Low"],
                "Down From High (%)": f"{down_from_high:.2f}" if isinstance(down_from_high, float) else "N/A",
                "Up From Low (%)": f"{up_from_low:.2f}" if isinstance(up_from_low, float) else "N/A"
            })
    return merged

# Function to generate HTML
def generate_html(main_table):
    updated_time = datetime.now(timezone("Asia/Kathmandu")).strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEPSE Live Data</title>
        <style>
            /* CSS Styles (unchanged) */
        </style>
        <script>
            /* JavaScript functions (unchanged) */
        </script>
    </head>
    <body>
        <h1>NEPSE Data Table</h1>
        <h2>Welcome to Syntoo's Nepse Stock Data</h2>
        <div class="updated-time">
            <div class="left">Updated on: {updated_time}</div>
            <div class="right">Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a></div>
        </div>

        <div class="search-container">
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search for symbols...">
        </div>

        <div class="table-container">
            <table id="nepseTable">
                <thead>
                    <tr>
                        <th>SN</th>
                        <th class="symbol" onclick="sortTable(1)">Symbol</th>
                        <th onclick="sortTable(2)">LTP</th>
                        <th onclick="sortTable(3)">Change%</th>
                        <th onclick="sortTable(4)">Day High</th>
                        <th onclick="sortTable(5)">Day Low</th>
                        <th onclick="sortTable(6)">Previous Close</th>
                        <th onclick="sortTable(7)">Volume</th>
                        <th onclick="sortTable(8)">Turnover</th>
                        <th onclick="sortTable(9)">52 Week High</th>
                        <th onclick="sortTable(10)">52 Week Low</th>
                        <th onclick="sortTable(11)">Listed Share</th>
                        <th onclick="sortTable(12)">Public Share</th>
                        <th onclick="sortTable(13)">Market Cap</th>
                        <th onclick="sortTable(14)">Paid Up Cap</th>
                        <th onclick="sortTable(15)">Float Cap</th>
                        <th onclick="sortTable(16)">EPS</th>
                        <th onclick="sortTable(17)">Book Value</th>
                        <th onclick="sortTable(18)">Down From High (%)</th>
                        <th onclick="sortTable(19)">Up From Low (%)</th>
                    </tr>
                </thead>
                <tbody>
    """
    for row in main_table:
        change_class = "light-red" if float(row["Change%"]) < 0 else (
            "light-green" if float(row["Change%"]) > 0 else "light-blue")
        html += f"""
            <tr onclick="highlightRow(this)">
                <td>{row["Symbol"]}</td><td class="symbol {change_class}">{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td class="{change_class}">{row["Change%"]}</td><td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td><td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td>
                <td>{row["Listed Share"]}</td><td>{row["Public Share"]}</td><td>{row["Market Cap"]}</td>
                <td>{row["Paid Up Cap"]}</td><td>{row["Float Cap"]}</td><td>{row["EPS"]}</td>
                <td>{row["Book Value"]}</td><td>{row["Down From High (%)"]}</td><td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += """
        </tbody>
        </table>
    </div>

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

# Refresh Data
def refresh_data():
    live_data = scrape_live_trading()
    listed_security_data = scrape_listed_security()
    merged_data = merge_data(live_data, listed_security_data)
    html_content = generate_html(merged_data)
    upload_to_ftp(html_content)

# Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=5)
scheduler.start()

# Initial Data Refresh
refresh_data()

# Keep Running
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
