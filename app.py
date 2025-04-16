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

@app.route('/games')
def games():
        cur = mysql.connection.cursor()
        
        cur.execute('''
            SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints,
                   d.name as developer_name
            FROM game g
            JOIN developer d ON g.developerID = d.developerID
            ORDER BY g.genre, g.title
        ''')
        games = cur.fetchall()
        # Organize by genre
        games_by_genre = {}
        for game in games:
            genre = game['genre']
            if genre not in games_by_genre:
                games_by_genre[genre] = []
            games_by_genre[genre].append(game)
            
        return render_template('games.html', games_by_genre=games_by_genre)

app.run(host='localhost', port=5000)
