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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500


@app.route("/")
def index():
    posts = list(mongo.db.spotting_post.find())
    return render_template("index.html", posts=posts, page_title="Home")


@app.route("/search", methods=["GET", "POST"])
def search():
    searchitem = request.form.get("searchitem")
    posts = list(mongo.db.spotting_post.find({"$text": {"$search": searchitem}}))
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


@app.route("/modify_cars")
def modify_cars():
    cars = list(mongo.db.car.find().sort("car_make", 1))
    if session["user"] == "admin123":
        return render_template("modify_cars.html", cars=cars)
    else:
        return redirect(url_for("index"))


@app.route("/new_make", methods=["GET", "POST"])
def new_make():
    if request.method == "POST":
        car_make = {
            "car_make": request.form.get("car_make"),
        }
        mongo.db.car.insert_one(car_make)
        flash("Car Make Added Successfully")
        return redirect(url_for("modify_cars"))


@app.route("/remove_make/<car_id>")
def remove_make(car_id):
    mongo.db.car.delete_one({"_id": ObjectId(car_id)})
    flash("Car Make Has Been Removed")
    return redirect(url_for("modify_cars"))


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
    if request.method == "POST":
        submit = {
            "car_make": request.form.get("car_make"),
            "car_model": request.form.get("car_model"),
            "country": request.form.get("country"),
            "city": request.form.get("city"),
            "date_seen": request.form.get("date_seen"),
            "posted_by": session["user"]
        }
        mongo.db.spotting_post.update({"_id": ObjectId(post_id)}, submit)
        flash("Spotting Post Changed Successfully")

    post = mongo.db.spotting_post.find_one({"_id": ObjectId(post_id)})
    car = mongo.db.car.find().sort("car_make", 1)
    location = mongo.db.location.find().sort("country", 1)
    return render_template("edit.html", post=post, car=car, location=location)


@app.route("/remove/<post_id>")
def remove(post_id):
    mongo.db.spotting_post.delete_one({"_id": ObjectId(post_id)})
    flash("Spotting Post Has Been Removed")
    return redirect(url_for("index"))


@app.route("/account_settings", methods=["GET", "POST"])
def account_settings():
    # take username from session on database
    if session["user"]:
        username = session["user"]

        user = mongo.db.users.find_one(
        {"username": username})

        if user:
            return render_template("account_settings.html", user=user)

    return redirect(url_for("login.html"))


@app.route("/logout")
def logout():
    # delete active cookie session, so user is logged out
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/change_password/<user_id>", methods=["GET", "POST"])
def change_password(user_id):
    
    if request.method == "POST":
        mongo.db.users.update_one({"_id": ObjectId(user_id)},{"$set":{"password": generate_password_hash(request.form.get("password"))}})

        flash("Password updated successfully")
        return redirect(url_for("account_settings", username=session["user"]))

    return render_template("account_settings.html")


@app.route("/delete_account/<user_id>")
def delete_account(user_id):
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    flash("User Deleted")
    session.pop("user")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False)
