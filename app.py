from flask import Flask, redirect, url_for, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import jwt
import hashlib
import bson
import bcrypt

app = Flask(__name__)

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
            token = jwt.encode(payload, str(app.config["SECRET_KEY"]), algorithm="HS256")

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
            token = jwt.encode(payload, str(app.config["SECRET_KEY"]), algorithm="HS256")

            return jsonify({"message": "Berhasil login", "token": token})
        else:
            return jsonify({"message": "Email atau password salah"})
    else:
        return jsonify({"message": "Email atau password salah"})


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/pendaftaran")
def pendaftaran():
    return render_template("pendaftaran.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/profile", methods=["GET"])
def get_profile():
    # Ambil profil dari MongoDB
    profile = db.profiles.find_one()

    if profile:
        return jsonify(profile)
    else:
        return jsonify({"message": "Profil tidak ditemukan"})
    
@app.route("/profile", methods=["POST"])
def create_profile():
    data = request.get_json()
    nama = data.get("nama")
    jenis_kelamin = data.get("jenis_kelamin")
    alamat = data.get("alamat")
    tempat_lahir = data.get("tempat_lahir")
    tanggal_lahir = data.get("tanggal_lahir")
    foto = data.get("foto")

    if not (nama and jenis_kelamin and alamat and tempat_lahir and tanggal_lahir):
        return jsonify({"message": "Semua form harus diisi"}), 400

    profile = {
        "nama": nama,
        "jenis_kelamin": jenis_kelamin,
        "alamat": alamat,
        "tempat_lahir": tempat_lahir,
        "tanggal_lahir": tanggal_lahir,
        "foto": foto
    }

    # Simpan profil ke MongoDB
    db.profiles.insert_one(profile)

    return jsonify({"message": "Profil berhasil disimpan"})

@app.route("/profile", methods=["PUT"])
def update_profile():
    data = request.get_json()
    nama = data.get("nama")
    jenis_kelamin = data.get("jenis_kelamin")
    alamat = data.get("alamat")
    tempat_lahir = data.get("tempat_lahir")
    tanggal_lahir = data.get("tanggal_lahir")
    foto = data.get("foto")

    if not (nama and jenis_kelamin and alamat and tempat_lahir and tanggal_lahir):
        return jsonify({"message": "Semua form harus diisi"}), 400

    profile = {
        "nama": nama,
        "jenis_kelamin": jenis_kelamin,
        "alamat": alamat,
        "tempat_lahir": tempat_lahir,
        "tanggal_lahir": tanggal_lahir,
        "foto": foto
    }

    # Perbarui profil di MongoDB
    db.profiles.update_one({}, {"$set": profile})

    return jsonify({"message": "Profil berhasil diperbarui"})

@app.route("/profile/foto", methods=["DELETE"])
def delete_photo():
    # Hapus foto dari profil di MongoDB
    db.profiles.update_one({}, {"$unset": {"foto": ""}})

    return jsonify({"message": "Foto berhasil dihapus"})

# Pengumuman
@app.route('/inputpengumuman', methods=['GET', 'POST'])
def pengumuman():
    if request.method == 'POST':
        tglpengumuman = request.form['tglpengumuman']
        isipengumuman = request.form['isipengumuman']
        link = request.form['link']

        db.pengumuman.insert_one({
            'tglpengumuman': tglpengumuman,
            'isipengumuman': isipengumuman,
            'link':link
        })

        return redirect('/pengumumanadmin')
    
    return render_template('inputpengumuman.html')


@app.route('/pengumumanadmin')
def isi_pengumuman():
    pengumumanadmin = db.pengumuman.find()

    return render_template('pengumumanadmin.html', pengumumanadmin=pengumumanadmin)


@app.route('/delete/<isipengumuman>')
def delete(isipengumuman):
    db.pengumuman.delete_one({'isipengumuman': isipengumuman})

    return redirect('/pengumumanadmin')

@app.route('/edit/<isipengumuman>')
def edit_data(isipengumuman):
    pengumumanadmin = db.pengumuman.find_one({'isipengumuman': isipengumuman})
    return render_template('editpengumuman.html', data=pengumumanadmin)

@app.route('/update/<isipengumuman>', methods=['POST'])
def update_data(isipengumuman):
    tglpengumuman_baru = request.form['tglpengumuman']
    isipengumuman_baru = request.form['isipengumuman']
    link_baru = request.form['link']
    db.pengumuman.update_one({'isipengumuman': isipengumuman},{'$set': {'tglpengumuman': tglpengumuman_baru, 'isipengumuman': isipengumuman_baru, 'link':link_baru}})
    return redirect(url_for('isi_pengumuman'))

@app.route('/pengumumanuser')
def pengumumanuser_():
    data = db.pengumuman.find()
    return render_template('pengumumanuser.html', pengumumanuser=data)

if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run("0.0.0.0", port=5000, debug=True)
