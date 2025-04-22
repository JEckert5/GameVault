from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import re
import MySQLdb.cursors
import json
from random import sample
from ast import literal_eval


app = Flask(__name__)

app.secret_key = "NEED TO CHANGE TO SOMETHING ACTUALLY SECURE"

# Maybe move password to .env file idk
app.config["MYSQL_HOST"] = "dbdev.cs.kent.edu"
app.config["MYSQL_USER"] = "nbooth5"
app.config["MYSQL_PASSWORD"] = "bi9tqNM6"
app.config["MYSQL_DB"] = "nbooth5"
# app.config["MYSQL_UNIX_SOCKET"] = "/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock"

mysql = MySQL(app)


@app.route("/")
def main():
    cur = mysql.connection.cursor()

    cur.execute(
        """
            SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints,
                   d.name, d.developerID
            FROM game g
            JOIN developer d ON g.developerID = d.developerID;
        """
    )

    featuredGames = sample(cur.fetchall(), 4)

    cur.execute(
        """
            SELECT developerID, name, about FROM developer;
        """
    )

    featuredDevelopers = sample(cur.fetchall(), 4)

    cur.close()

    return render_template("index.html", games=featuredGames, devs=featuredDevelopers)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "loggedin" in session:
        return redirect(url_for("index"))

    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
        user = cursor.fetchone()

        # Check if user exists and password is correct
        if user:
            if check_password_hash(user["password"], password):
                session["loggedin"] = True
                session["userID"] = user["userID"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                session["status"] = user["status"]

                # Update user status to ONLINE
                cursor.execute(
                    'UPDATE user SET status = "ONLINE" WHERE userID = %s',
                    (user["userID"],),
                )
                mysql.connection.commit()

                flash("Login successful!", "success")
                return redirect(url_for("main"))
            else:
                msg = "Incorrect password!"
        else:
            msg = "Username not found!"

    return render_template("login.html", msg=msg)


# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if "loggedin" in session:
        return redirect(url_for("index"))

    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
        and "email" in request.form
    ):
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if account exists
        cursor.execute(
            "SELECT * FROM user WHERE username = %s OR email = %s", (username, email)
        )
        account = cursor.fetchone()

        if account:
            msg = "Account already exists!"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            msg = "Invalid email address!"
        elif not re.match(r"^[A-Za-z0-9_]+$", username):
            msg = "Username must contain only letters, numbers and underscores!"
        else:
            # Hash the password
            hashed_password = generate_password_hash(password)

            # Create new user
            user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO user (userID, username, email, password, status, bio)
                VALUES (%s, %s, %s, %s, 'ONLINE', '')
            """,
                (user_id, username, email, hashed_password),
            )
            mysql.connection.commit()

            # Create empty profile
            """ cursor.execute('INSERT INTO user (userID) VALUES (%s)', (user_id,))
            mysql.connection.commit() """

            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("register.html", msg=msg)


# Logout Route
@app.route("/logout")
def logout():
    if "loggedin" in session:
        # Update status to OFFLINE
        cursor = mysql.connection.cursor()
        cursor.execute(
            'UPDATE user SET status = "OFFLINE" WHERE userID = %s', (session["userID"],)
        )
        mysql.connection.commit()

        # Clear session
        session.pop("loggedin", None)
        session.pop("userID", None)
        session.pop("username", None)
        session.pop("email", None)
        session.pop("status", None)

        flash("You have been logged out.", "info")
    return redirect(url_for("main"))


@app.route("/games")
def games():
    cur = mysql.connection.cursor()

    cur.execute(
        """
            SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints,
                  d.name as developer_name, d.developerID
            FROM game g
            JOIN developer d ON g.developerID = d.developerID
            ORDER BY g.genre, g.title
        """
    )

    games = cur.fetchall()
    # Organize by genre
    games_by_genre = {}
    for game in games:
        genre = game[2]
        if genre not in games_by_genre:
            games_by_genre[genre] = []
        games_by_genre[genre].append(game)

    cur.close()

    return render_template("games.html", games_by_genre=games_by_genre)


@app.route("/games/<int:id>", methods=["GET", "POST"])
def game(id: int):
    if request.method == "GET":
        cur = mysql.connection.cursor()
        cur.execute(
            f"""
                SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints, g.developerID, d.name, d.about
                FROM game g 
                JOIN developer d ON g.gameID = {id} AND g.developerID = d.developerID;
            """
        )

        game = cur.fetchall()

        cur.execute(
            f"""
                SELECT u.username, title, content, rating FROM review r JOIN user u ON r.gameID = {id} AND u.userID = r.userID;
            """
        )

        reviews = cur.fetchall()

        cur.close()

        return render_template("games.html", game=game[0], reviews=reviews)
    else:
        review = request.form.get("review-content")
        title = request.form.get("title-input")
        rating = request.form.get("rating")

        print(review, title)

        cur = mysql.connection.cursor()

        try:
            cur.execute(
                f"""
                    INSERT INTO review (gameID, userID, content, title, rating) VALUES
                    (
                        {id}, {session["userID"]}, "{review}", "{title}", "{rating}"
                    );
                """
            )
        except:
            pass

        mysql.connection.commit()

        cur.close()

        return redirect(f"/games/{id}")


@app.route("/developers")
def developers():
    cur = mysql.connection.cursor()
    cur.execute(
        """
            SELECT developerID, name, about FROM developer;
        """
    )
    data = cur.fetchall()

    cur.close()

    return render_template("developers.html", data=data)


@app.route("/developer_about/<int:id>")
def developer_about(id: int):
    cur = mysql.connection.cursor()

    cur.execute(
        f"""
            SELECT d.name, d.about FROM developer d WHERE d.developerID = {id};
        """
    )

    dev = cur.fetchall()

    cur.execute(f"SELECT * FROM game WHERE developerID = {id};")

    games = cur.fetchall()

    cur.close()

    return render_template("developer_about.html", dev=dev[0], games=games)


@app.route("/library")
def library():
    if "loggedin" in session:
        cur = mysql.connection.cursor()

        cur.execute(
            f"""
                SELECT  g.title, o.completed_checkpoints, g.total_checkpoints
                FROM owned_game o JOIN game g
                ON o.ownerID = {session["userID"]} AND o.gameID = g.gameID;
            """
        )

        data = cur.fetchall()

        cur.close()

        return render_template("library.html", games=data)

    else:
        return render_template("library.html", user=False)


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
