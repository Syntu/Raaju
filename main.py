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

# Function to calculate additional columns
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
            th {{background-color: #8B4513; color: white; position: sticky; top: 0; cursor: pointer;}}
            th:hover {{background-color: #A0522D;}}
            h1 {{font-size: 46px; font-weight: bold; text-align: center; margin-bottom: 0;}}
            .header {{display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;}}
            .footer {{text-align: center; margin-top: 20px; font-size: 16px;}}
            .sortable {{cursor: pointer;}}
            .sorted-asc::after {{content: " ▲";}}
            .sorted-desc::after {{content: " ▼";}}
        </style>
        <script>
            // Sorting Functionality
            function sortTable(columnIndex, type) {{
                const table = document.getElementById("data-table");
                const rows = Array.from(table.rows).slice(1);
                let isAscending = table.dataset.sortOrder === "asc";

                rows.sort((rowA, rowB) => {{
                    let cellA = rowA.cells[columnIndex].innerText;
                    let cellB = rowB.cells[columnIndex].innerText;

                    if (type === "number") {{
                        cellA = parseFloat(cellA) || 0;
                        cellB = parseFloat(cellB) || 0;
                    }}

                    return isAscending
                        ? cellA > cellB ? 1 : -1
                        : cellA < cellB ? 1 : -1;
                }});

                isAscending = !isAscending;
                table.dataset.sortOrder = isAscending ? "asc" : "desc";

                rows.forEach(row => table.appendChild(row));
            }}
        </script>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div class="header">
            <p>Updated on: {update_date_time}</p>
            <p>Developed By: <a href="https://www.syntoo.com" target="_blank">Syntoo</a></p>
        </div>
        <table id="data-table" data-sort-order="asc">
            <thead>
                <tr>
                    <th onclick="sortTable(0, 'number')">SN</th>
                    <th onclick="sortTable(1, 'string')">Symbol</th>
                    <th onclick="sortTable(2, 'number')">LTP</th>
                    <th onclick="sortTable(3, 'number')">Change%</th>
                    <th onclick="sortTable(4, 'number')">Day High</th>
                    <th onclick="sortTable(5, 'number')">Day Low</th>
                    <th onclick="sortTable(6, 'number')">Previous Close</th>
                    <th onclick="sortTable(7, 'number')">Volume</th>
                    <th onclick="sortTable(8, 'number')">Turnover</th>
                    <th onclick="sortTable(9, 'number')">52 Week High</th>
                    <th onclick="sortTable(10, 'number')">52 Week Low</th>
                    <th onclick="sortTable(11, 'number')">Down From High (%)</th>
                    <th onclick="sortTable(12, 'number')">Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in main_table:
        html += f"""
            <tr>
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td>{row["Change%"]}</td><td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td><td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td>
                <td>{row["Down From High (%)"]}</td><td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
        <div class="footer">
            <p>Welcome 🙏 to NEPSE Data Website.</p>
        </div>
    </body>
    </html>
    """
    return html

# FTP Upload Function
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        with open("index.html", "rb") as file:
            ftp.storbinary("STOR index.html", file)

# Scheduler to scrape and update data at regular intervals
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
scheduler.add_job(scheduled_task, 'interval', minutes=15)
scheduler.start()

# To keep the script running continuously
try:
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
