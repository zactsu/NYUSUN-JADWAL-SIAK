from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
from bs4 import BeautifulSoup

# --- FUNGSI SCRAPER ASLI KAMU (sedikit dimodifikasi) ---
# Tidak ada lagi variabel global untuk URL, semuanya ada di dalam fungsi
def scrape_my_schedule(username, password, period):
    BASE_URL = "https://academic.ui.ac.id/main"
    AUTH_URL = f"{BASE_URL}/Authentication/Index"
    CHANGEROLE_URL = f"{BASE_URL}/Authentication/ChangeRole"
    schedule_url = f"{BASE_URL}/Schedule/Index?period={period}"

    session = requests.Session()
    
    print(f"Mencoba login untuk user: {username}...")
    try:
        login_payload = {'u': username, 'p': password}
        r = session.post(AUTH_URL, data=login_payload, verify=False)
        r = session.get(CHANGEROLE_URL)

        if "Login" in r.text or "SSO" in r.text:
            print("Login GAGAL!")
            return {"error": "Login GAGAL! Periksa kembali username dan password."}
        print("Login BERHASIL!")
    except requests.exceptions.RequestException as e:
        print(f"Error saat koneksi: {e}")
        return {"error": f"Error saat koneksi: {e}"}

    print(f"Mengambil jadwal dari periode: {period}")
    r = session.get(schedule_url)
    if r.status_code != 200:
        return {"error": "Gagal mengambil halaman jadwal."}

    print("Mem-parsing data...")
    soup = BeautifulSoup(r.text, 'html.parser')
    all_courses = []
    course_headers = soup.find_all('th', class_='sub border2 pad2')
    
    if not course_headers:
        return {"error": "Tidak ada jadwal ditemukan untuk periode ini."}

    # ... (Sisa dari logika parsing-mu SAMA PERSIS seperti sebelumnya) ...
    for header in course_headers:
        # ... (kode parsing header) ...
        course_data = {
            "kode_mk": ...,
            "nama_mk": ...,
            "sks": ...,
            "term": ...,
            "kelas": []
        }
        for row in header.parent.find_next_siblings('tr'):
            # ... (kode parsing baris dan sel) ...
            course_data["kelas"].append({ ... })
        all_courses.append(course_data)

    print("Parsing SELESAI!")
    return all_courses

# --- BAGIAN SERVER FLASK ---
app = Flask(__name__)
CORS(app) # Mengizinkan request dari JavaScript

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['POST'])
def handler(path):
    # Ambil data JSON yang dikirim dari JavaScript
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    period = data.get('period')

    if not all([username, password, period]):
        return jsonify({"error": "Username, password, atau periode tidak lengkap"}), 400

    # Panggil fungsi scraper dengan data yang diterima
    hasil_scrape = scrape_my_schedule(username, password, period)
    
    # Kirim kembali hasilnya ke JavaScript
    return jsonify(hasil_scrape)