import requests
import json
import re
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- KONFIGURASI ---
BASE_URL = "https://academic.ui.ac.id/main"
AUTH_URL = f"{BASE_URL}/Authentication/Index"
CHANGEROLE_URL = f"{BASE_URL}/Authentication/ChangeRole"

# Inisialisasi aplikasi Flask
app = Flask(__name__)
CORS(app) # Mengizinkan request dari domain lain (penting untuk Vercel)

def scrape_my_schedule(username, password, period):
    """
    Fungsi utama untuk login, mengambil, dan mem-parse jadwal mata kuliah.
    (Isi fungsi ini sama persis dengan yang kamu berikan, tidak perlu diubah)
    """
    session = requests.Session()
    schedule_url = f"{BASE_URL}/Schedule/Index?period={period}"

    try:
        login_payload = {'u': username, 'p': password}
        # Tambahkan timeout untuk mencegah fungsi berjalan terlalu lama di Vercel
        r = session.post(AUTH_URL, data=login_payload, verify=False, timeout=10) 
        r = session.get(CHANGEROLE_URL, timeout=10)

        if "Login" in r.text or "SSO" in r.text:
            return {"error": "Login GAGAL! Periksa kembali username dan password."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error saat koneksi: {e}"}

    r = session.get(schedule_url)
    if r.status_code != 200:
        return {"error": "Gagal mengambil halaman jadwal."}

    soup = BeautifulSoup(r.text, 'html.parser')
    all_courses = []
    course_headers = soup.find_all('th', class_='sub border2 pad2')
    
    if not course_headers:
        return [] # Kembalikan list kosong jika tidak ada jadwal

    for header in course_headers:
        header_text = header.get_text(separator=' ', strip=True)
        course_code_match = re.search(r'([A-Z]{4}\d{6})', header_text)
        course_name_match = re.search(r'\s-\s(.*?)\s\(\d+\sSKS', header_text)
        sks_match = re.search(r'\((\d+)\sSKS', header_text)
        term_match = re.search(r'Term\s(\d+)', header_text)

        course_data = {
            "kode_mk": course_code_match.group(1) if course_code_match else None,
            "nama_mk": course_name_match.group(1) if course_name_match else None,
            "sks": int(sks_match.group(1)) if sks_match else None,
            "term": int(term_match.group(1)) if term_match else None,
            "kelas": []
        }
        
        for row in header.parent.find_next_siblings('tr'):
            if row.find('th', class_='sub') or not row.get('class'):
                break

            cells = row.find_all('td')
            if len(cells) > 6:
                raw_class_name = cells[1].get_text(strip=True)
                class_name = raw_class_name.replace("Kelas", "").strip()
                schedule = [s.strip() for s in cells[4].decode_contents().strip().split('<br/>')]
                room = [r.strip() for r in cells[5].decode_contents().strip().split('<br/>')]
                raw_lecturers = cells[6].decode_contents().strip().split('<br/>')
                lecturers = [p.strip().lstrip('-').strip() for p in raw_lecturers if p.strip()]

                course_data["kelas"].append({
                    "nama_kelas": class_name,
                    "jadwal": schedule,
                    "ruang": room,
                    "pengajar": lecturers
                })
        
        all_courses.append(course_data)

    return all_courses

# Buat endpoint API di /api/scrape
@app.route('/api/scrape', methods=['POST'])
def handle_scrape():
    # Ambil data dari body request yang dikirim oleh frontend
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data or 'period' not in data:
        return jsonify({"error": "Data tidak lengkap: username, password, dan period dibutuhkan."}), 400

    username = data.get('username')
    password = data.get('password')
    period = data.get('period') # Formatnya harus "TAHUN-PERIODE", contoh: "2025-1"

    # Panggil fungsi scraper
    result = scrape_my_schedule(username, password, period)

    # Jika ada error dari fungsi scraper
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 401 # Unauthorized atau error lain

    # Kembalikan hasil dalam format JSON
    return jsonify(result)