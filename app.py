from flask import Flask, redirect, url_for, render_template, request, jsonify, send_from_directory, send_file, make_response
from pymongo import MongoClient
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from jwt.exceptions import ExpiredSignatureError, DecodeError
from functools import wraps
from bson.objectid import ObjectId
from os.path import join, dirname
from dotenv import load_dotenv
import jwt
import hashlib
import os
import requests
# import weasyprint

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = "./static/profile_pics"
app.config['UPLOAD_FOLDER'] = 'static/dokumen_calon_santri'

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")
SECRET_KEY = os.environ.get("SECRET_KEY")
TOKEN_KEY = os.environ.get("TOKEN_KEY")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]


# Untuk Fungsi autentikasi user
def userTokenAuth(view_func):
    @wraps(view_func)
    def decorator(*args, **kwargs):
        token_receive = request.cookies.get("token")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            email = payload.get('email')
            user_info = db.users.find_one({'email': email})
            if user_info:
                users = [user_info]
                return view_func(*args, users=users, **kwargs)
            else:
                return redirect(url_for('login'))
        except jwt.ExpiredSignatureError:
            msg = 'Your token has expired'
            return redirect(url_for('login', msg=msg))
        except jwt.exceptions.DecodeError:
            print("Received token:", token_receive)
            msg = 'There was a problem logging you in'
            return redirect(url_for('login', msg=msg))

    return decorator

# Untuk Fungsi autentikasi admin
def adminTokenAuth(view_func):
    @wraps(view_func)
    def decorator(*args, **kwargs):
        token_receive = request.cookies.get("token")
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            email = payload.get('email')
            admin_info = db.admin.find_one({'email': email})
            if admin_info:
                admin = [admin_info]
                return view_func(*args, admin=admin, **kwargs)
            else:
                return redirect(url_for('ppdb_console'))
        except jwt.ExpiredSignatureError:
            msg = 'Your token has expired'
            return redirect(url_for('ppdb_console', msg=msg))
        except jwt.exceptions.DecodeError:
            print("Received token:", token_receive)
            msg = 'There was a problem logging you in'
            return redirect(url_for('ppdb_console', msg=msg))

    return decorator

# Route untuk logout
@app.route('/logout')
def logout():
    # Hapus token dari cookie
    response = make_response(redirect(url_for('login')))
    response.set_cookie('token', '', expires=0)
    return response

#UNTUK HALAMAN LANDING PAGE
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("landingpage.html")

#UNTUK HALAMAN LOGIN/REGISTRASI
@app.route("/login")
def login():
    return render_template("loginregister.html")

#UNTUK REGISTRASI AKUN
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

#UNTUK CEK EMAIL SUDAH DI PAKAI OLEH ORANG LAIN
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

#UNTUK MASUK SEBAGAI USER
@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    result = db.users.find_one({"email": email, "password": pw_hash})
    if result:
        payload = {
            "email": email,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        response = make_response(
            jsonify({
                "message": "success",
                "email": email,
                "token": token
            })
        )

        response.set_cookie("token", token)

        return response
    else:
        return jsonify({
            "message": "fail",
            "error": "We could not find a user with that email/password combination"
        })
    

@app.route("/ppdb_console")
def ppdb_console():
    return render_template("adminlogin.html")


@app.route("/login-admin", methods=["POST"])
def login_admin():
    data = request.get_json()
    email = data["email"]
    password = data["password"]
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    result = db.admin.find_one({"email": email, "password": pw_hash})

    if result:
        payload = {
            "email": email,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        response = make_response(
            jsonify({
                "message": "success",
                "email": email,
                "token": token
            })
        )
        response.set_cookie("token", token)
        return response

    else:
        return jsonify({
            "message": "fail",
            "error": "We could not find a user with that email/password combination"
        })


@app.route("/home_admin", methods=['GET'])
@adminTokenAuth
def homeadmin(admin):
    grafik = db.users.find_one({})
    return render_template('home_admin.html', grafik=grafik, admin=admin)

@app.route('/data_jenis_kelamin')
def data_jenis_kelamin():
    pendaftar = db.users.find({}, {'jenis_kelamin': 1})  # Mengambil semua dokumen dengan hanya mengambil jenis_kelamin
    jumlah_laki_laki = 0
    jumlah_perempuan = 0
    for p in pendaftar:
        if 'jenis_kelamin' in p:
            if p['jenis_kelamin'] == 'laki-laki':
                jumlah_laki_laki += 1
            elif p['jenis_kelamin'] == 'perempuan':
                jumlah_perempuan += 1
    data = {
        'laki_laki': jumlah_laki_laki,
        'perempuan': jumlah_perempuan
    }
    return jsonify(data)


@app.route('/dashboard', methods=['GET'])
@userTokenAuth
def dashboard(users):
    return render_template('index.html', users=users)



@app.route("/profile",  methods=['GET'])
@userTokenAuth
def profile(users):
    profile = db.users.find_one({'_id': ObjectId(users[0]['_id'])})
    return render_template("profile.html", profile=profile, users=users)


@app.route('/save/profil', methods=['POST'])
@userTokenAuth
def tambah_profil(users):
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    foto = request.files['foto']
    extension = foto.filename.split('.')[-1]
    profilename = f'static/profile_pics/profile-{mytime}.{extension}'
    foto.save(profilename)

    jenis_kelamin = request.form["jenis_kelamin"]
    alamat = request.form["alamat"]
    tempat_lahir = request.form["tempat_lahir"]
    tanggal_lahir_str = request.form["tanggal_lahir"]
    tanggal_lahir = datetime.strptime(tanggal_lahir_str, "%Y-%m-%d").date()

    # Simpan data ke MongoDB
    profil = {
            'foto': profilename,
            'jenis_kelamin': jenis_kelamin,
            'alamat': alamat,
            'tempat_lahir': tempat_lahir,
            'tanggal_lahir': tanggal_lahir.strftime('%Y-%m-%d')
    }

    # Menyimpan profil sesuai dengan ID pengguna saat registrasi
    user_id = ObjectId(users[0]['_id'])
    db.users.update_one({'_id': user_id}, {'$set': profil}, upsert=True)

    return 'Profil berhasil ditambahkan'


@app.route("/pendaftaran", methods=['GET', 'POST'])
@userTokenAuth
def pendaftaran(users):
    return render_template('pendaftaran.html', users=users)

def fetchProvinces():
    api_key = '61f11a92448099f51314a6558e627d9d6adb58b7937e314da7c276ff6b7a7614'
    url = f"https://api.binderbyte.com/wilayah/provinsi?api_key={api_key}"

    response = requests.get(url)
    provinces = response.json()["value"]
    
    return provinces

def fetchCities(provinceId):
    api_key = '61f11a92448099f51314a6558e627d9d6adb58b7937e314da7c276ff6b7a7614'
    url = f"https://api.binderbyte.com/wilayah/kabupaten?api_key={api_key}&id_provinsi={provinceId}"

    response = requests.get(url)
    json_data = response.json()
    
    if "value" in json_data:
        cities = json_data["value"]
    else:
        cities = []
    
    return cities



@app.route('/kirim-data', methods=['POST'])
@userTokenAuth
def kirim_data(users):

    # Mengambil data yang ada dalam tag {{ }} dari form
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
    status = request.form.get('status')

    # Mengambil nama file dokumen yang diunggah
    file = request.files['dokumen']
    extension = file.filename.split('.')[-1]
    filename = f'static/dokumen_calon_santri/dokumen_{nama_lengkap}.{extension}'
    file.save(filename)

    
    # Mengambil ID pengguna dari parameter users
    user_id = ObjectId(users[0]['_id'])

    # Menyiapkan data untuk pembaruan
    form_data = {
        "$set": {
            "nama_lengkap": nama_lengkap,
            "nama_panggilan": nama_panggilan,
            "asal_provinsi": asal_provinsi,
            "asal_kota": asal_kota,
            "jenis_kelamin": jenis_kelamin,
            "nama_ayah": nama_ayah,
            "nama_ibu": nama_ibu,
            "hobi": hobi,
            "cita_cita": cita_cita,
            "bidang": bidang,
            "tokoh": tokoh,
            "nomor_hp": nomor_hp,
            "status": status,
            "dokumen": filename}
    }

    # Memperbarui dokumen pengguna berdasarkan ID pengguna
    db.users.update_one({"_id": user_id}, form_data)

   

    # Mengembalikan respons sukses tanpa merender template HTML
    return redirect(url_for('verifikasi', status='menunggu'))

@app.route("/verifikasi")
@userTokenAuth
def verifikasi(users):
    
    return render_template("verifikasi_data.html", users=users)

    
# @app.route("/unduh-pdf", methods=['GET'])
# @userTokenAuth
# def unduh_pdf(users):
#     # Mendapatkan path direktori "Downloads" pengguna
#     download_dir = os.path.expanduser("~/Downloads")

#     if users:
#         user = users[0]  # Ambil pengguna pertama dari daftar pengguna
#         nama_lengkap = user.get('nama_lengkap')

#         if nama_lengkap:
#             # Menentukan nama file PDF tujuan dengan menggunakan nama lengkap pengguna
#             file_name = f"{nama_lengkap.replace(' ', '_')}_kartu_ujian.pdf"  # Ubah spasi menjadi underscore

#             # Menentukan path lengkap file PDF tujuan
#             file_path = os.path.join(download_dir, file_name)

#             # Render template HTML untuk file "layout_kartu_ujian.html" dengan gambar dari folder "static"
#             rendered_template = render_template("layout_kartu_ujian.html", users=users)

#             # Konversi HTML menjadi PDF menggunakan WeasyPrint dengan opsi konfigurasi untuk format landscape
#             pdf = weasyprint.HTML(string=rendered_template, base_url=request.host_url).write_pdf(
#                 stylesheets=[weasyprint.CSS(string="@page { size: landscape; }")]
#             )

#             # Simpan file PDF ke path tujuan
#             with open(file_path, 'wb') as file:
#                 file.write(pdf)

#             # Kirim file PDF sebagai respons unduhan dengan menggunakan nama file yang sesuai
#             return send_from_directory(directory=download_dir, path=file_name, as_attachment=True)

#     return "Nama lengkap tidak tersedia atau pengguna tidak ditemukan."


    
@app.route("/unduh_kartu_ujian")
@userTokenAuth
def unduh_kartu_ujian(users):
    return render_template("layout_kartu_ujian.html", users=users)


# Pengumuman
@app.route("/inputpengumuman", methods=["GET", "POST"])
@adminTokenAuth
def pengumuman(admin):
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
@adminTokenAuth
def isi_pengumuman(admin):
    pengumumanadmin = db.pengumuman.find()

    return render_template("pengumumanadmin.html", pengumumanadmin=pengumumanadmin)


@app.route("/delete/<isipengumuman>")
@adminTokenAuth
def delete(isipengumuman):
    db.pengumuman.delete_one({"isipengumuman": isipengumuman})

    return redirect("/pengumumanadmin")


@app.route("/edit/<isipengumuman>")
@adminTokenAuth
def edit_data(isipengumuman):
    pengumumanadmin = db.pengumuman.find_one({"isipengumuman": isipengumuman})
    return render_template("editpengumuman.html", data=pengumumanadmin)


@app.route("/update/<isipengumuman>", methods=["POST"])
@adminTokenAuth
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
@userTokenAuth
def pengumumanuser_(users):
    data = db.pengumuman.find()
    return render_template("pengumumanuser.html", pengumumanuser=data, users=users)

#list pendaftar
@app.route('/listpendaftar')
@adminTokenAuth
def list_pendaftar(admin):
    users = db.users.find()
    return render_template('listpendaftar.html', users=users)

#validasi Data Calon Santri
@app.route("/validasidata")
@adminTokenAuth
def valid_data(admin):
    users = db.users.find()
    return render_template('validasidata.html', users=users)



@app.route('/validasi', methods=['GET'])
@adminTokenAuth
def validasi(admin):
    # Mendapatkan ID user dari parameter URL
    user_id = request.args.get('id')

    # Ambil data user dari MongoDB berdasarkan ID
    user = get_user_from_mongodb(user_id)

    asal_provinsi = user.get('asal_provinsi')
    asal_provinsi = fetchProvinces()


    # Mengirimkan data user ke template validasisantri.html
    return render_template('validasisantri.html', user=user, asal_provinsi=asal_provinsi)

def fetchProvinceById(provinceId):
    api_key = '61f11a92448099f51314a6558e627d9d6adb58b7937e314da7c276ff6b7a7614'
    url = f"https://api.binderbyte.com/wilayah/provinsi?api_key={api_key}"

    response = requests.get(url)
    provinces = response.json()["value"]

    # Mencari provinsi dengan ID yang sesuai
    for province in provinces:
        if province["id"] == provinceId:
            return province

    # Jika ID provinsi tidak ditemukan, kembalikan None
    return None

# Fungsi untuk mengambil data user dari MongoDB berdasarkan ID
def get_user_from_mongodb(user_id):
    # Kode untuk mengambil data user dari MongoDB berdasarkan ID
    # Gantikan dengan implementasi Anda sendiri
    # Contoh:
    user = db.users.find_one({'_id': ObjectId(user_id)})  # Menggunakan ObjectId untuk mencocokkan _id

    # Mendapatkan ID provinsi dari data user
    provinsi_id = user.get('asal_provinsi')

    # Mendapatkan nama provinsi berdasarkan ID provinsi dari API
    provinsi = fetchProvinceById(provinsi_id)
    nama_provinsi = provinsi.get('name')

    # Menambahkan informasi nama provinsi ke dalam data user
    user['asal_provinsi'] = nama_provinsi

    return user


@app.route("/editvalid", methods=["GET", "POST"])
@adminTokenAuth
def edit_valid(admin):
    user_id = request.args.get('id')
    print("user_id:", user_id)  # Add this line to check the value

    user = get_user_from_mongodb(user_id)
    return render_template("editvalidasidata.html", user=user, user_id=user_id)

    

@app.route('/updatevalid', methods=['POST'])
@adminTokenAuth
def update_valid():
    user_id = request.args.get('id')  # Memperbarui untuk mengambil user_id dari argumen URL
    tanggal_ujian = request.form.get('tanggal_ujian')
    tempat_ujian = request.form.get('tempat_ujian')
    tanggal_wawancara = request.form.get('tanggal_wawancara')
    tempat_wawancara = request.form.get('tempat_wawancara')
    status_validasi = request.form.get('status')

     # Print the received form data for debugging
    print("User ID:", user_id)
    print("Tanggal Ujian:", tanggal_ujian)
    print("Tempat Ujian:", tempat_ujian)
    print("Tanggal Wawancara:", tanggal_wawancara)
    print("Tempat Wawancara:", tempat_wawancara)
    print("Status Validasi:", status_validasi)

     # Perbarui data di MongoDB berdasarkan user_id
    filter_query = {'_id': ObjectId(user_id)}  # Use '_id' instead of 'user_id'
    update_query = {
        '$set': {
            'tanggal_ujian': tanggal_ujian,
            'tempat_ujian': tempat_ujian,
            'tanggal_wawancara': tanggal_wawancara,
            'tempat_wawancara': tempat_wawancara,
            'status': status_validasi
        }   
    }
    db.users.update_one(filter_query, update_query)

    return redirect(url_for('valid_data'))  # Redirect ke fungsi valid_data

@app.route("/contact", methods=["GET", "POST"])
@userTokenAuth
def contact_us(users):
    return render_template("contact.html", users=users)

if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run("0.0.0.0", port=5000, debug=True)
