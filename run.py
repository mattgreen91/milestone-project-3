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
    return render_template("index.html", page_title="Home Page", posts=posts)


@app.route("/new_user")
def new_user():
    return render_template("new_user.html", page_title="New User")


@app.route("/about")
def about():
    return render_template("about.html", page_title="About")


@app.route("/blog")
def products():
    return render_template("blog.html", page_title="Blog")


@app.route("/store")
def store():
    return render_template("store.html")


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=True)
