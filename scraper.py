import requests
import json
import re
from bs4 import BeautifulSoup


# MADE BY LOOKMAN WITH GEMINI
# THANKS TO BACKEND RISTEK FASILKOM UI
# --- KONFIGURASI ---
# INSTALL requests, json, re, dan bs4 dulu. Bisa pakai pip3 install (nama)
# Ganti dengan username dan password SSO lo
# PERINGATAN: Jangan pernah upload file ini dengan password asli ke tempat publik seperti GitHub!
USERNAME = "XXXXX"
PASSWORD = "XXXXX"

# URL SIAK NG
BASE_URL = "https://academic.ui.ac.id/main"
AUTH_URL = f"{BASE_URL}/Authentication/Index"
CHANGEROLE_URL = f"{BASE_URL}/Authentication/ChangeRole"
# Ganti '2025-1' dengan periode yang lo mau
SCHEDULE_URL = f"{BASE_URL}/Schedule/Index?period=2025-1"

def scrape_my_schedule():
    """
    Fungsi utama untuk login, mengambil, dan mem-parse jadwal mata kuliah.
    """
    session = requests.Session()

    print("Mencoba login...")
    try:
        login_payload = {'u': USERNAME, 'p': PASSWORD}
        r = session.post(AUTH_URL, data=login_payload, verify=False)
        r = session.get(CHANGEROLE_URL)

        if "Login" in r.text:
            print("Login GAGAL! Periksa kembali username dan password.")
            return
        print("Login BERHASIL!")
    except requests.exceptions.RequestException as e:
        print(f"Error saat koneksi: {e}")
        return

    print(f"Mengambil jadwal dari periode: {SCHEDULE_URL.split('period=')[1].split('&')[0]}")
    r = session.get(SCHEDULE_URL)
    if r.status_code != 200:
        print("Gagal mengambil halaman jadwal.")
        return

    print("Mem-parsing data...")
    soup = BeautifulSoup(r.text, 'html.parser')
    all_courses = []

    course_headers = soup.find_all('th', class_='sub border2 pad2')

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
                # --- PERUBAHAN DI SINI ---
                # Ambil nama kelas mentah, lalu hapus kata "Kelas" dan spasi ekstra
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

    print("Parsing SELESAI!")
    return all_courses

if __name__ == "__main__":
    jadwal_kuliah = scrape_my_schedule()

    if jadwal_kuliah:
        nama_file_output = "jadwal.json" # Pastikan nama file output sesuai
        print(f"\nMenyimpan hasil scraping ke file: {nama_file_output}")
        with open(nama_file_output, 'w', encoding='utf-8') as f:
            json.dump(jadwal_kuliah, f, indent=2, ensure_ascii=False)
        print("File berhasil disimpan!")