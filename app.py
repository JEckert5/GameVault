from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import re
import MySQLdb.cursors
from datetime import datetime
import json
from random import sample
from ast import literal_eval
from os.path import isfile


app = Flask(__name__)

app.secret_key = "NEED TO CHANGE TO SOMETHING ACTUALLY SECURE"

# Maybe move password to .env file idk
app.config["MYSQL_HOST"] = "dbdev.cs.kent.edu"
app.config["MYSQL_USER"] = "nbooth5"
app.config["MYSQL_PASSWORD"] = "bi9tqNM6"
app.config["MYSQL_DB"] = "nbooth5"

mysql = MySQL(app)


@app.route("/")
def main():
    cur = mysql.connection.cursor()

    cur.execute(
        """
            SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints, g.price,
                   d.name, d.developerID
            FROM game g
            JOIN developer d ON g.developerID = d.developerID;
        """
    )

    featuredGames = sample(cur.fetchall(), 4)

    alreadyOwned = {}
    if "loggedin" in session:
        for game in featuredGames:
            cur.execute(
                f"SELECT g.gameID FROM game AS g, owned_game AS o WHERE o.gameID = {game[0]} AND o.ownerID = {session["userID"]}"
            )
            result = cur.fetchall()
            if result:
                alreadyOwned[game[0]] = True
            else:
                alreadyOwned[game[0]] = False
    else:
        for game in featuredGames:
            alreadyOwned[game[0]] = False

    cur.execute(
        """
            SELECT developerID, name, about FROM developer;
        """
    )

    featuredDevelopers = sample(cur.fetchall(), 4)

    cur.close()

    return render_template(
        "index.html", games=featuredGames, devs=featuredDevelopers, owned=alreadyOwned
    )


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

        if user:
            if check_password_hash(user["password"], password):
                session["loggedin"] = True
                session["userID"] = user["userID"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                session["status"] = user["status"]
                session["developer"] = user["developer"]

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

        cursor = mysql.connection.cursor()
        cursor.execute(
            'UPDATE user SET status = "OFFLINE" WHERE userID = %s', (session["userID"],)
        )
        mysql.connection.commit()

        session.pop("loggedin", None)
        session.pop("userID", None)
        session.pop("username", None)
        session.pop("email", None)
        session.pop("status", None)
        session.pop("developer", None)

        flash("You have been logged out.", "info")
    return redirect(url_for("main"))


@app.route("/toggle_developer")
def toggle_developer():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("SELECT developer FROM user WHERE userID = %s", [session["userID"]])
    current_status = cur.fetchone()[0]

    new_status = 0 if current_status == 1 else 1
    cur.execute(
        "UPDATE user SET developer = %s WHERE userID = %s",
        [new_status, session["userID"]],
    )
    mysql.connection.commit()
    cur.close()

    session["developer"] = new_status

    flash(f"Developer mode {'enabled' if new_status else 'disabled'}.", "info")
    return redirect(request.referrer or url_for("main"))


@app.route("/games")
def games():
    cur = mysql.connection.cursor()

    cur.execute(
        """
            SELECT g.gameID, g.title, g.genre, g.description, g.total_checkpoints,
                g.price, d.name as developer_name, d.developerID
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

    alreadyOwned = {}
    if "loggedin" in session:
        for game in games:
            cur.execute(
                f"SELECT g.gameID FROM game AS g, owned_game AS o WHERE o.gameID = {game[0]} AND o.ownerID = {session["userID"]}"
            )
            result = cur.fetchall()
            if result:
                alreadyOwned[game[0]] = True
            else:
                alreadyOwned[game[0]] = False
    else:
        for game in games:
            alreadyOwned[game[0]] = False

    cur.close()

    return render_template(
        "games.html", games_by_genre=games_by_genre, owned=alreadyOwned
    )


@app.route("/games/<int:id>", methods=["GET", "POST"])
def game(id: int):
    if request.method == "GET":
        dupe = False
        if request.args.get("duplicate"):
            dupe = True

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
            f"SELECT u.username, title, content, rating FROM review r JOIN user u ON r.gameID = {id} AND u.userID = r.userID;"
        )

        reviews = cur.fetchall()

        alreadyOwned = False

        if "loggedin" in session:
            cur.execute(
                f"SELECT g.gameID FROM game AS g, owned_game AS o WHERE o.gameID = {id} and o.ownerID = {session["userID"]};"
            )
            result = cur.fetchall()
            if result:
                alreadyOwned = True
            else:
                alreadyOwned = False

        cur.close()

        return render_template(
            "games.html",
            game=game[0],
            reviews=reviews,
            duplicate=dupe,
            owned=alreadyOwned,
        )
    else:
        review = request.form.get("review-content")
        title = request.form.get("title-input")
        rating = request.form.get("rating")

        # print(review, title)

        cur = mysql.connection.cursor()

        try:
            cur.execute(
                f"""
                INSERT INTO review (gameID, userID, content, title, rating) VALUES
                (
                    {id}, 
                    {session["userID"]}, 
                    "{review}", 
                    "{title}", 
                    "{rating}"
                );
                """
            )

        except Exception as e:  # Probably a user double reviewing, not allowed
            print(e)

            return redirect(f"/games/{id}?duplicate=true")

        print(review)

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
                SELECT  g.gameID, g.title, o.completed_checkpoints, g.total_checkpoints
                FROM owned_game o JOIN game g
                ON o.ownerID = {session["userID"]} AND o.gameID = g.gameID;
            """
        )

        data = cur.fetchall()

        cur.close()

        return render_template("library.html", user=True, games=data)

    else:
        return render_template("library.html", user=False)


@app.route("/add-game", methods=["GET", "POST"])
def add_game():
    if "loggedin" in session:
        if request.method == "GET":
            cur = mysql.connection.cursor()

            cur.execute("SHOW COLUMNS FROM game LIKE 'genre';")
            data = cur.fetchall()[0][1]
            data = data.replace("enum", "")
            data = literal_eval(data)

            cur.execute(
                "SELECT developer FROM user WHERE userID=%s;", [session["userID"]]
            )
            dev = cur.fetchall()[0][0]

            cur.close()
            return render_template("add_game.html", genres=data, dev=dev)
        elif request.method == "POST":
            cur = mysql.connection.cursor()
            addTitle = request.form["name"]
            addDesc = request.form["desc"]
            addGenre = request.form["genre"]
            addCP = request.form["checkpoints"]
            addPrice = request.form["price"]

            cur.execute("SELECT MAX(gameID) FROM game")
            addGID = cur.fetchone()[0] + 1
            addDID = session["userID"]
            addDName = session["username"]

            cur.execute("SELECT * FROM developer WHERE developerID=%s", [addDID])
            match = cur.fetchone()

            if not match:
                cur.execute(
                    "INSERT INTO developer(developerID, name) VALUES (%s, %s)",
                    [addDID, addDName],
                )
                mysql.connection.commit()

            # add to game table and user's library
            cur.execute(
                """
                INSERT INTO game(gameID, title, genre, description, total_checkpoints, developerID, developer_name, price)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                [
                    addGID,
                    addTitle,
                    addGenre,
                    addDesc,
                    addCP,
                    addDID,
                    addDName,
                    addPrice,
                ],
            )
            mysql.connection.commit()

            cur.execute(
                "INSERT INTO owned_game(gameID, ownerID, completed_checkpoints) VALUES (%s, %s, 0)",
                [addGID, addDID],
            )
            mysql.connection.commit()
            message = "Successfully added!"

            # readying to reload the page
            cur.execute("SHOW COLUMNS FROM game LIKE 'genre';")
            data = cur.fetchall()[0][1]
            data = data.replace("enum", "")
            data = literal_eval(data)

            cur.execute(
                "SELECT developer FROM user WHERE userID=%s;", [session["userID"]]
            )
            dev = cur.fetchall()[0][0]

            cur.close()

            return render_template("add_game.html", genres=data, dev=dev, msg=message)
        else:
            print("REQUEST TYPE ERROR")
    else:
        return render_template("add_game.html", user=False)


@app.route("/add_to_cart/<int:game_id>")
def add_to_cart(game_id):
    cart = session.get("cart", [])

    addable = True
    for g in cart:
        if g == game_id:
            addable = False
            break

    if addable == True:
        cart.append(game_id)
        session["cart"] = cart
        flash("Game added to cart.", "success")

    return redirect(request.referrer or url_for("games"))


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    cur = mysql.connection.cursor()

    if cart:

        fmt = ",".join(["%s"] * len(cart))
        cur.execute(
            f"""
            SELECT gameID, title, price
            FROM game
            WHERE gameID IN ({fmt})
        """,
            tuple(cart),
        )
        games = cur.fetchall()
        total = sum(float(g[2]) for g in games)
    else:
        games, total = [], 0.0

    cur.close()
    return render_template("cart.html", games=games, total=total)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cart = session.get("cart", [])
    if not cart:
        return "Your cart is empty."

    cur = mysql.connection.cursor()

    format_strings = ",".join(["%s"] * len(cart))
    cur.execute(
        f"SELECT gameID, title, price FROM game WHERE gameID IN ({format_strings})",
        cart,
    )
    games = cur.fetchall()

    total = sum(g[2] for g in games)

    if request.method == "POST":
        cc_number = request.form["cc_number"]
        cvv = request.form["cvv"]
        exp_month = request.form["exp_month"]
        exp_year = request.form["exp_year"]
        street = request.form["street"]
        city = request.form["city"]
        state = request.form["state"]
        country = request.form["country"]

        cur.execute(
            """
            INSERT INTO address (street_addr, city, state, country)
            VALUES (%s, %s, %s, %s)
        """,
            (street, city, state, country),
        )

        billing_address = cur.lastrowid

        exp_date = f"{exp_year}-{exp_month}-01"
        user_id = session["userID"]

        cur.execute(
            """
        INSERT INTO payment_info (userID, card_num, cvv, exp_date, billing_address)
        VALUES (%s, %s, %s, %s, %s)
        """,
            (user_id, cc_number, cvv, exp_date, billing_address),
        )
        payment_id = cur.lastrowid

        # For each game: create a transaction and add to owned_game
        for game in games:
            game_id = game[0]
            price = game[2]
            payment_time = datetime.now()

            # Insert transaction
            cur.execute(
                """
                INSERT INTO `transaction` (paymentID, gameID, payment_time, amnt_due, subscription)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (payment_id, game_id, payment_time, price, False),
            )

            # Add to owned_game
            cur.execute(
                """
                INSERT INTO owned_game (ownerID, gameID, completed_checkpoints)
                VALUES (%s, %s, 0)
            """,
                (user_id, game_id),
            )

        mysql.connection.commit()
        cur.close()

        session["cart"] = []

        return redirect(url_for("library"))

    cur.close()
    return render_template("checkout.html", games=games, total=total)


@app.route("/remove_from_cart/<int:game_id>", methods=["POST"])
def remove_from_cart(game_id):
    cart = session.get("cart", [])
    if game_id in cart:
        cart.remove(game_id)
        session["cart"] = cart
        flash("Removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/user_profile/<int:id>", methods=["POST", "GET"])
def user_profile(id: int):
    cur = mysql.connection.cursor()

    if request.method == "GET":
        is_self = False
        dev = False
        if "loggedin" in session:
            if session["userID"] == id:
                is_self = True

            if session["developer"] == 1:
                cur.execute(f"SELECT about FROM developer WHERE developerID = {id};")

                dev = cur.fetchall()[0]

        user = {}
        user["userID"] = id

        cur.execute(f"SELECT bio, status, username FROM user WHERE userID = {id};")

        data = cur.fetchall()[0]

        user["bio"] = data[0]
        user["status"] = data[1]
        user["username"] = data[2]

        # cur.execute(
        #     f"SELECT f.friendID, u.username FROM friends f JOIN user u ON u.userID = f.friendID AND f.userID = {id};"
        # )

        # user["friends"] = cur.fetchall()

        if user["status"] == "ONLINE":
            user["color"] = "green"
        elif user["status"] == "OFFLINE":
            user["color"] = "gray"
        elif user["status"] == "DO NOT DISTURB":
            user["color"] = "red"
        else:  # Away
            user["color"] = "yellow"

        cur.close()

        return render_template("profile.html", user=user, is_self=is_self, dev=dev)
    else:
        if "bio-input" in request.form:
            cur.execute(
                f'UPDATE user SET bio="{request.form.get("bio-input")}" WHERE userID = {session["userID"]}'
            )

        if "set-status" in request.form:
            cur.execute(
                f'UPDATE user SET status="{request.form["set-status"]}" WHERE userID = {session["userID"]};'
            )

        if "dev-about-input" in request.form:
            cur.execute(
                f'UPDATE developer SET about="{request.form["dev-about-input"]}" WHERE developerID = {session["userID"]};'
            )

        mysql.connection.commit()

        cur.close()

        return redirect(f"/user_profile/{id}")


@app.route("/add_to_wishlist/<int:game_id>")
def add_to_wishlist(game_id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    try:
        cur.execute(
            "INSERT INTO wishlist (userID, gameID) VALUES (%s, %s)",
            (session["userID"], game_id),
        )
        mysql.connection.commit()
        flash("Game added to wishlist!", "success")
    except MySQLdb.IntegrityError:
        flash("Game is already in your wishlist", "info")

    cur.close()
    return redirect(request.referrer or url_for("games"))


@app.route("/wishlist")
def wishlist():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT g.gameID, g.title, g.price, d.name 
        FROM wishlist w
        JOIN game g ON w.gameID = g.gameID
        JOIN developer d ON g.developerID = d.developerID
        WHERE w.userID = %s
    """,
        (session["userID"],),
    )

    wishlist_items = cur.fetchall()
    cur.close()

    return render_template("wishlist.html", wishlist_items=wishlist_items)


@app.route("/move_to_cart/<int:game_id>")
def move_to_cart(game_id):
    if "loggedin" not in session:
        return redirect(url_for("login"))

    # Remove from wishlist
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM wishlist WHERE userID = %s AND gameID = %s",
        (session["userID"], game_id),
    )
    mysql.connection.commit()

    # Add to cart session
    cart = session.get("cart", [])
    if game_id not in cart:
        cart.append(game_id)
        session["cart"] = cart

    cur.close()
    flash("Game moved to cart!", "success")
    return redirect(url_for("wishlist"))


@app.route("/friends")
def friends():
    if "loggedin" in session:
        cur = mysql.connection.cursor()

        cur.execute(
            f"""
                SELECT friendID, userID, date_friended
                FROM friends
                where userID = {session["userID"]};
            """
        )

        data = cur.fetchall()

        cur.close()

        for friends in data:
            print(data)

        return render_template("friends.html", data=data)

    else:
        return render_template("library.html", user=False)


@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "loggedin" in session:
        user_id = session["userID"]
        friend_id = request.form["friendID"]

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO friends (friendID, userID, date_friended) VALUES (%s, %s, NOW())",
            (friend_id, user_id),
        )

        mysql.connection.commit()

        cur.close()

        return redirect(url_for("friends"))

    return redirect(url_for("friends"))


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
