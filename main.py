import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
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
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            h1, h2 {{ text-align: center; margin: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; cursor: pointer; }}
            th {{ background-color: #8B4513; color: white; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #fffbcc; }}
            .highlight {{ background-color: #fffbcc !important; }}
            .header {{ position: absolute; top: 0; right: 10px; padding: 10px; }}
            .light-red {{ background-color: #FFCCCB; }}
            .light-green {{ background-color: #D4EDDA; }}
            .light-blue {{ background-color: #CCE5FF; }}
            @media (max-width: 768px) {{
                table {{ font-size: 12px; }}
                th, td {{ padding: 5px; }}
            }}
            @media (max-width: 480px) {{
                table {{ font-size: 10px; }}
                th, td {{ padding: 3px; }}
            }}
        </style>
        <script>
            function sortTable(n) {{
                var table = document.getElementById("dataTable");
                var rows = Array.from(table.rows).slice(1);
                var ascending = !table.rows[1].getAttribute("data-asc");
                rows.sort(function(a, b) {{
                    var x = a.cells[n].innerText;
                    var y = b.cells[n].innerText;
                    if (!isNaN(parseFloat(x)) && !isNaN(parseFloat(y))) {{
                        return ascending ? parseFloat(x) - parseFloat(y) : parseFloat(y) - parseFloat(x);
                    }} else {{
                        return ascending ? x.localeCompare(y) : y.localeCompare(x);
                    }}
                }});
                table.tBodies[0].append(...rows);
                Array.from(table.rows).forEach(row => row.setAttribute("data-asc", ascending));
            }}
            function highlightRow(row) {{
                Array.from(document.querySelectorAll(".highlight")).forEach(el => el.classList.remove("highlight"));
                row.classList.add("highlight");
            }}
        </script>
    </head>
    <body>
        <div class="header">
            Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a>
        </div>
        <h1>NEPSE Live Data</h1>
        <h2>Updated On: {updated_time}</h2>
        <table id="dataTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">SN</th>
                    <th onclick="sortTable(1)">Symbol</th>
                    <th onclick="sortTable(2)">LTP</th>
                    <th onclick="sortTable(3)">Change%</th>
                    <th onclick="sortTable(4)">Day High</th>
                    <th onclick="sortTable(5)">Day Low</th>
                    <th onclick="sortTable(6)">Previous Close</th>
                    <th onclick="sortTable(7)">Volume</th>
                    <th onclick="sortTable(8)">Turnover</th>
                    <th onclick="sortTable(9)">52 Week High</th>
                    <th onclick="sortTable(10)">52 Week Low</th>
                    <th onclick="sortTable(11)">Down From High (%)</th>
                    <th onclick="sortTable(12)">Up From Low (%)</th>
                </tr>
            </thead>
            <tbody>
    """
    for row in main_table:
        change_class = "light-red" if float(row["Change%"]) < 0 else (
            "light-green" if float(row["Change%"]) > 0 else "light-blue")
        html += f"""
            <tr onclick="highlightRow(this)">
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td class="{change_class}">{row["Change%"]}</td><td>{row["Day High"]}</td>
                <td>{row["Day Low"]}</td><td>{row["Previous Close"]}</td>
                <td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td>
                <td>{row["Down From High (%)"]}</td><td>{row["Up From Low (%)"]}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
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
    today_data = scrape_today_share_price()
    merged_data = merge_data(live_data, today_data)
    html_content = generate_html(merged_data)
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
