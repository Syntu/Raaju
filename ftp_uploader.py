import ftplib

def upload_to_ftp(ftp_host, ftp_user, ftp_pass, html_content):
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    with ftplib.FTP(ftp_host, ftp_user, ftp_pass) as ftp:
        ftp.cwd("/htdocs")
        with open("index.html", "rb") as f:
            ftp.storbinary("STOR index.html", f)