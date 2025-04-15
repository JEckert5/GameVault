from flask import Flask, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

# Maybe move password to .env file idk
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "GameVault"
app.config["MYSQL_UNIX_SOCKET"] = "/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock"

mysql = MySQL(app)


@app.route("/")
def main():
    cur = mysql.connection.cursor()
    cur.execute("SHOW TABLES;")
    rv = cur.fetchall()
    print(rv)
    return render_template("index.html", tables=rv)
