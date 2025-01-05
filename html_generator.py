from datetime import datetime
from pytz import timezone

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
            h1 {{ text-align: center; font-size: 40px; font-weight: bold; margin-top: 20px; }}
            h2 {{ text-align: center; font-size: 14px; margin-bottom: 20px; }}
            .table-container {{ margin: 0 auto; width: 95%; overflow-x: auto; overflow-y: auto; height: 600px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #8B4513; color: white; }}
            .footer {{ text-align: right; padding: 10px; font-size: 12px; color: gray; }}
            .updated-time {{ font-size: 14px; margin-top: 10px; }}
            .search-container {{ text-align: center; margin-bottom: 10px; }}
            .search-container input {{ width: 200px; padding: 5px; font-size: 14px; }}
        </style>
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
                        <th>Down From High (%)</th>
                        <th>Up From Low (%)</th>
                    </tr>
                </thead>
                <tbody>
    """
    for row in main_table:
        html += f"""
            <tr>
                <td>{row["SN"]}</td><td>{row["Symbol"]}</td><td>{row["LTP"]}</td>
                <td>{row["Change%"]}</td><td>{row["Day High"]}</td><td>{row["Day Low"]}</td>
                <td>{row["Previous Close"]}</td><td>{row["Volume"]}</td><td>{row["Turnover"]}</td>
                <td>{row["52 Week High"]}</td><td>{row["52 Week Low"]}</td><td>{row["Down From High (%)"]}</td>
                <td>{row["Up From Low (%)"]}</td>
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