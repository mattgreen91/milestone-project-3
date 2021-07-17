import os
from flask import (Flask, flash, render_template, redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
def index():
    posts = mongo.db.spotting_post.find()
    return render_template("index.html", posts=posts, page_title="Home")


@app.route("/new_user", methods=["GET", "POST"])
def new_user():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("This username is already taken")
            return redirect(url_for("new_user"))

        new_user = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(new_user)

        # put the user into active session cookie
        session["user"] = request.form.get("username").lower()
        flash("New user created successfully")
        return redirect(url_for("account_settings", username=session["user"]))

    return render_template("new_user.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username already exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # check hashed password matches same user inputted
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome back {}".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "account_settings", username=session["user"]))
            else:
                # incorrect password
                flash("Incorrect login details entered. Please try again")
                return redirect(url_for("login"))

        else: 
            # incorrect username
            flash("Incorrect login details entered. Please try again")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        post = {
            "car_make": request.form.get("car_make"),
            "car_model": request.form.get("car_model"),
            "country": request.form.get("country"),
            "city": request.form.get("city"),
            "date_seen": request.form.get("date_seen"),
            "posted_by": session["user"]
        }
        mongo.db.spotting_post.insert_one(post)
        flash("Spotting Post Added Successfully")
        return redirect(url_for("index"))

    car = mongo.db.car.find().sort("car_make", 1)
    location = mongo.db.location.find().sort("country", 1)
    return render_template("add.html", car=car, location=location)


@app.route("/edit/<post_id>", methods=["GET", "POST"])
def edit(post_id):
    post = mongo.db.spotting_post.find_one({"_id": ObjectId(post_id)})


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/<username>", methods=["GET", "POST"])
def account_settings(username):
    # take username from session on database
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    
    if session["user"]:
        return render_template("account_settings.html", username=username)

    return redirect(url_for("login.html"))


@app.route("/logout")
def logout():
    # delete active cookie session, so user is logged out
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True)
