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
            h1 {{
                text-align: center;
                font-size: 40px;
                font-weight: bold;
                margin-top: 20px;
            }}
            h2 {{
                text-align: center;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            .table-container {{
                margin: 0 auto;
                width: 95%;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 14px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #8B4513;
                color: white;
                position: sticky;
                top: 0;
                z-index: 1;
                cursor: pointer;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .light-red {{
                background-color: #FFCCCB;
            }}
            .light-green {{
                background-color: #D4EDDA;
            }}
            .light-blue {{
                background-color: #CCE5FF;
            }}
            .footer {{
                text-align: right;
                padding: 10px;
                font-size: 12px;
                color: gray;
            }}
            .footer a {{
                color: inherit;
                text-decoration: none;
            }}
            .updated-time {{
                font-size: 14px;
                margin-top: 10px;
            }}
            .left {{
                float: left;
            }}
            .right {{
                float: right;
            }}
            @media (max-width: 768px) {{
                table {{
                    font-size: 12px;
                }}
                th, td {{
                    padding: 5px;
                }}
            }}
            @media (max-width: 480px) {{
                table {{
                    font-size: 10px;
                }}
                th, td {{
                    padding: 3px;
                }}
            }}
        </style>
        <script>
            function sortTable(n) {{
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("nepseTable");
                switching = true;
                dir = "asc"; 
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (dir == "asc") {{
                            if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }} else if (dir === "desc") {{
                            if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }}
                    }}
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    }} else {{
                        if (switchcount === 0 && dir === "asc") {{
                            dir = "desc";
                            switching = true;
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <h1>NEPSE Live Data</h1>
        <h2>Welcome 🙏 to my Nepse Data website</h2>
        <div class="updated-time">
            <div class="left">Updated on: {updated_time}</div>
            <div class="right">Developed By: <a href="https://www.facebook.com/srajghimire">Syntoo</a></div>
        </div>

        <div class="table-container">
            <table id="nepseTable">
                <thead>
                    <tr>
                        <th>SN</th>
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
            <tr>
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

#main
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
