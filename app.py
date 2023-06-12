from flask import Flask, redirect, url_for, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import jwt
import hashlib
import os
import requests

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"
SECRET_KEY = "secret_key"

client = MongoClient(
    "mongodb://grup4kelompok1:kelompok1@ac-pgwmogi-shard-00-00.fl0gdtc.mongodb.net:27017,ac-pgwmogi-shard-00-01.fl0gdtc.mongodb.net:27017,ac-pgwmogi-shard-00-02.fl0gdtc.mongodb.net:27017/?ssl=true&replicaSet=atlas-jhyhsx-shard-0&authSource=admin&retryWrites=true&w=majority"
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

    if len(password) < 8:
        return jsonify({"message": "Password harus memiliki minimal 8 karakter"})

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


@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()
    email = data["email"]
    password = data["password"]

    # Cari pengguna berdasarkan alamat email
    user = db.users.find_one({"email": email})

    if user:
        # Verifikasi password
        hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if hashed_password == user["password"]:
            # Buat token JWT
            payload = {"email": email}
            token = jwt.encode(
                payload, str(app.config["SECRET_KEY"]), algorithm="HS256"
            )

            return jsonify({"message": "Berhasil login", "token": token})
        else:
            return jsonify({"message": "Email atau password salah"})
    else:
        return jsonify({"message": "Email atau password salah"})


@app.route("/ppdb-console")
def ppdb_console():
    return render_template("adminlogin.html")


@app.route("/admin", methods=["POST"])
def admin():
    data = request.get_json()
    email = data["email"]
    password = data["password"]

    # Cari pengguna berdasarkan alamat email
    user = db.admin.find_one({"email": email})

    if user:
        # Verifikasi password
        hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if hashed_password == user["password"]:
            # Buat token JWT
            payload = {"email": email}
            token = jwt.encode(
                payload, str(app.config["SECRET_KEY"]), algorithm="HS256"
            )

            return jsonify({"message": "Berhasil login", "token": token})
        else:
            return jsonify({"message": "Email atau password salah"})
    else:
        return jsonify({"message": "Email atau password salah"})


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


@app.route("/pendaftaran", methods=['GET', 'POST'])
def pendaftaran():
    return render_template("pendaftaran.html")

def fetch_provinces(api_key):
    url = f'https://api.binderbyte.com/wilayah/provinsi?api_key={api_key}'

    response = requests.get(url)
    if response.status_code == 200:
        provinces_data = response.json()
        provinces = provinces_data.get('value')
        return provinces
    else:
        return None

def fetch_cities(api_key, province_id):
    url = f'https://api.binderbyte.com/wilayah/kabupaten?id_provinsi={province_id}&api_key={api_key}'

    response = requests.get(url)
    if response.status_code == 200:
        cities_data = response.json()
        cities = cities_data.get('value')
        return cities
    else:
        return None

@app.route("/validasi", methods=["GET", "POST"])
def validasi():
    api_key = '61f11a92448099f51314a6558e627d9d6adb58b7937e314da7c276ff6b7a7614'
    nama_lengkap = request.form.get('nama_lengkap')
    nama_panggilan = request.form.get('nama_panggilan')
    asal_provinsi = request.form.get('asal_provinsi')
    asal_kota = request.form.get('asal_kota')
    jenis_kelamin = request.form.get('jenis_kelamin')
    nama_ayah = request.form.get('nama_ayah')
    nama_ibu = request.form.get('nama_ibu')
    hobi = request.form.get('hobi')
    cita_cita = request.form.get('cita_cita')
    bidang = request.form.get('bidang')
    tokoh = request.form.get('tokoh')
    nomor_hp = request.form.get('nomor_hp')
    foto = request.files.get('foto')

    # Mendapatkan data provinsi
    provinces = fetch_provinces(api_key)

    # Mendapatkan data kota berdasarkan provinsi terpilih
    cities = None
    if asal_provinsi:
        cities = fetch_cities(api_key, asal_provinsi)


    return render_template("validasisantri.html",
                            nama_lengkap=nama_lengkap,
                            nama_panggilan=nama_panggilan,
                            asal_provinsi=asal_provinsi,
                            asal_kota=asal_kota,
                            jenis_kelamin=jenis_kelamin,
                            nama_ayah=nama_ayah,
                            nama_ibu=nama_ibu,
                            hobi=hobi,
                            cita_cita=cita_cita,
                            bidang=bidang,
                            tokoh=tokoh,
                            nomor_hp=nomor_hp,
                            provinces=provinces,
                            cities=cities)


@app.route("/profile")
def profile():
    profile = db.profiles.find_one({})
    return render_template("profile.html", profile=profile)



# Pengumuman
@app.route("/inputpengumuman", methods=["GET", "POST"])
def pengumuman():
    if request.method == "POST":
        tglpengumuman = request.form["tglpengumuman"]
        isipengumuman = request.form["isipengumuman"]
        link = request.form["link"]

        db.pengumuman.insert_one(
            {
                "tglpengumuman": tglpengumuman,
                "isipengumuman": isipengumuman,
                "link": link,
            }
        )

        return redirect("/pengumumanadmin")

    return render_template("inputpengumuman.html")


@app.route("/pengumumanadmin")
def isi_pengumuman():
    pengumumanadmin = db.pengumuman.find()

    return render_template("pengumumanadmin.html", pengumumanadmin=pengumumanadmin)


@app.route("/delete/<isipengumuman>")
def delete(isipengumuman):
    db.pengumuman.delete_one({"isipengumuman": isipengumuman})

    return redirect("/pengumumanadmin")


@app.route("/edit/<isipengumuman>")
def edit_data(isipengumuman):
    pengumumanadmin = db.pengumuman.find_one({"isipengumuman": isipengumuman})
    return render_template("editpengumuman.html", data=pengumumanadmin)


@app.route("/update/<isipengumuman>", methods=["POST"])
def update_data(isipengumuman):
    tglpengumuman_baru = request.form["tglpengumuman"]
    isipengumuman_baru = request.form["isipengumuman"]
    link_baru = request.form["link"]
    db.pengumuman.update_one(
        {"isipengumuman": isipengumuman},
        {
            "$set": {
                "tglpengumuman": tglpengumuman_baru,
                "isipengumuman": isipengumuman_baru,
                "link": link_baru,
            }
        },
    )
    return redirect(url_for("isi_pengumuman"))


@app.route("/pengumumanuser")
def pengumumanuser_():
    data = db.pengumuman.find()
    return render_template("pengumumanuser.html", pengumumanuser=data)




if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run("0.0.0.0", port=5000, debug=True)
