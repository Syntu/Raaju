import os
import ftplib
from apscheduler.schedulers.background import BackgroundScheduler
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
                "SN": cells[0].text.strip(),
                "Symbol": cells[1].text.strip(),
                "LTP": cells[2].text.strip(),
                "Change%": cells[4].text.strip(),
                "Day High": cells[6].text.strip(),
                "Day Low": cells[7].text.strip(),
                "Previous Close": cells[9].text.strip(),
                "Volume": cells[8].text.strip()
            })
    return data

# Function to scrape today's share price summary
def scrape_today_share_price():
    url = "https://www.sharesansar.com/today-share-price"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table_data = soup.find_all("td")
    return {
        "Turnover": table_data[10].text.strip(),
        "52 Week High": table_data[19].text.strip(),
        "52 Week Low": table_data[20].text.strip()
    }

# Function to calculate additional columns and merge data
def merge_data(live_data, summary_data):
    for row in live_data:
        ltp = float(row["LTP"].replace(",", "")) if row["LTP"] else 0
        high = float(summary_data["52 Week High"].replace(",", ""))
        low = float(summary_data["52 Week Low"].replace(",", ""))

        row["Turnover"] = summary_data["Turnover"]
        row["52 Week High"] = summary_data["52 Week High"]
        row["52 Week Low"] = summary_data["52 Week Low"]
        row["Down From High"] = f"{((high - ltp) / high * 100):.2f}%" if high else "N/A"
        row["Up From Low"] = f"{((ltp - low) / low * 100):.2f}%" if low else "N/A"
    return live_data

# Function to generate HTML table
def generate_html(merged_data):
    html = """
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
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 1;
                cursor: pointer;
            }
            td {
                text-align: center;
            }
            .table-container {
                max-height: 80vh;
                overflow-y: auto;
            }
            h1 {
                text-align: center;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <div class="table-container">
            <table id="stock-table">
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
                        <th onclick="sortTable(11)">Down From High</th>
                        <th onclick="sortTable(12)">Up From Low</th>
                    </tr>
                </thead>
                <tbody>
    """
    for row in merged_data:
        html += "<tr>" + "".join(f"<td>{row[col]}</td>" for col in row) + "</tr>"
    html += """
                </tbody>
            </table>
        </div>
        <script>
            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("stock-table");
                switching = true;
                dir = "asc"; // Set the sorting direction to ascending
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (dir == "asc") {
                            if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        } else if (dir == "desc") {
                            if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                shouldSwitch = true;
                                break;
                            }
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    return html

# Function to upload HTML to FTP server
def upload_to_ftp(html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
        ftp.cwd("/htdocs")  # Change to the correct directory if necessary
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)

# Function to refresh data
def refresh_data():
    print("Fetching data...")
    live_data = scrape_live_trading()
    summary_data = scrape_today_share_price()
    merged_data = merge_data(live_data, summary_data)
    print("Generating HTML...")
    html_content = generate_html(merged_data)
    print("Uploading to FTP...")
    upload_to_ftp(html_content)
    print("Data refreshed and uploaded successfully!")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", minutes=5)
scheduler.start()

# Refresh data initially
refresh_data()

# Keep the script running
try:
    print("Script running... Press Ctrl+C to stop.")
    while True:
        pass
except (KeyboardInterrupt, SystemExit):
    print("Stopping script...")
    scheduler.shutdown()
