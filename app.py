from flask import Flask, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

# Maybe move password to .env file idk
app.config["MYSQL_HOST"] = "dbdev.cs.kent.edu"
app.config["MYSQL_USER"] = "nbooth5"
app.config["MYSQL_PASSWORD"] = "bi9tqNM6"
app.config["MYSQL_DB"] = "nbooth5"

mysql = MySQL(app)


@app.route("/")
def main():
    cur = mysql.connection.cursor()
    cur.execute("SHOW TABLES;")
    rv = cur.fetchall()
    print(rv)
    return render_template("index.html")
