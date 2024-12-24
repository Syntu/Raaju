from flask import Flask
import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

app = Flask(__name__)  # Flask सर्भर सुरू गर्नुहोस्

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

# Function to scrape today's share price
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

# Function to merge live data and today's data
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
            row["Down From High"] = f"{((high - ltp) / high * 100):.2f}" if high else "N/A"
            row["Up From Low"] = f"{((ltp - low) / low * 100):.2f}" if low else "N/A"
        except ValueError:
            row["Down From High"] = "N/A"
            row["Up From Low"] = "N/A"
    return merged_data

# Function to generate HTML
def generate_html(data, update_time):
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NEPSE Live Data</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        h1 {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
        }
        h2 {
            text-align: center;
            font-size: 20px;
            margin: 0;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 20px;
        }
        .header div {
            font-size: 16px;
            font-weight: bold;
        }
        .header a {
            text-decoration: none;
            color: #000;
            font-weight: bold;
        }
        .header a:hover {
            color: #8B4513;
        }
        .table-container {
            width: 100%;
            overflow: auto;
            position: relative;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px auto;
            font-size: 14px;
            table-layout: fixed;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
            min-width: 100px;
        }
        th {
            background-color: #8B4513;
            color: white;
            position: sticky;
            top: 0;
            z-index: 2;
            cursor: pointer;
        }
        th.sortable:after {
            content: " ⇅";
            font-size: 12px;
            margin-left: 5px;
        }
        th:first-child {
            left: 0;
            z-index: 3;
        }
        td:first-child {
            position: sticky;
            left: 0;
            background-color: #fff;
        }
        tr:hover {
            background-color: #f1f1f1;
        }
        .footer {
            text-align: center;
            margin: 20px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <h1>NEPSE Live Data</h1>
    <div class="header">
        <div>Updated on: 2024-12-24 18:00:00</div>
        <a href="https://syntoo.com">Developed By: Syntoo</a>
    </div>
    <h2>Welcome 🙏 to NEPSE data Website.</h2>
    <div class="table-container">
        <table id="nepseTable">
            <thead>
                <tr>
                    <th>SN</th>
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
                    <th class="sortable">Down From High</th>
                    <th class="sortable">Up From Low</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>ABC</td>
                    <td>100</td>
                    <td>5%</td>
                    <td>105</td>
                    <td>95</td>
                    <td>98</td>
                    <td>2000</td>
                    <td>200,000</td>
                    <td>150</td>
                    <td>80</td>
                    <td>-33.33%</td>
                    <td>25%</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>DEF</td>
                    <td>200</td>
                    <td>-2%</td>
                    <td>210</td>
                    <td>190</td>
                    <td>202</td>
                    <td>3000</td>
                    <td>600,000</td>
                    <td>250</td>
                    <td>180</td>
                    <td>-20%</td>
                    <td>11.11%</td>
                </tr>
                <!-- Add more rows dynamically -->
            </tbody>
        </table>
    </div>
    <div class="footer">
        <p>Welcome 🙏 to NEPSE data Website.</p>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            const table = document.getElementById("nepseTable");
            const headers = table.querySelectorAll("th.sortable");

            headers.forEach((header, index) => {
                header.addEventListener("click", () => {
                    const rows = Array.from(table.querySelector("tbody").rows);
                    const ascending = header.classList.toggle("asc");
                    rows.sort((a, b) => {
                        const cellA = a.cells[index].innerText.trim();
                        const cellB = b.cells[index].innerText.trim();
                        const isNumeric = !isNaN(cellA) && !isNaN(cellB);
                        return isNumeric
                            ? (ascending ? cellA - cellB : cellB - cellA)
                            : (ascending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA));
                    });
                    rows.forEach(row => table.querySelector("tbody").appendChild(row));
                });
            });
        });
    </script>
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

# Scheduler task
def scheduled_task():
    live_data = scrape_live_trading()
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    final_data = calculate_additional_tables(merged_data)
    update_date_time = datetime.now(pytz.timezone('Asia/Kathmandu')).strftime("%Y-%m-%d %H:%M:%S")
    html_content = generate_html(final_data, update_date_time)
    upload_to_ftp(html_content)

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, "interval", minutes=15)
scheduler.start()

# Flask route
@app.route("/")
def home():
    return "NEPSE Data Service is Running!"

# Main
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
