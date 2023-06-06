from flask import Flask, redirect, url_for, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt
import hashlib
import bson
import bcrypt

app = Flask(__name__)

SECRET_KEY = "ppdb"

client = MongoClient(
    "mongodb+srv://test:sparta@cluster0.jvoejms.mongodb.net/?retryWrites=true&w=majority"
)
db = client.dbTester


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("landingpage.html")


@app.route("/login")
def login():
    return render_template("loginregister.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    first_name = data["first_name"]
    last_name = data["last_name"]
    email = data["email"]
    password = data["password"]

    # Hash password using SHA256
    hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()

    user = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password,
    }

    # Save user to MongoDB
    db.users.insert_one(user)

    return jsonify({"message": "User registered successfully"})

@app.route("/check-email", methods=["POST"])
def check_email():
    data = request.get_json()
    email = data["email"]

    # Cek apakah email sudah terdaftar
    existing_user = db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"exists": True})
    else:
        return jsonify({"exists": False})
    
    

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run("0.0.0.0", port=5000, debug=True)
