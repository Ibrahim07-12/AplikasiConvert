# Flux — All-in-One File Toolkit

PWA berbasis FastAPI dengan desain Brutalist Modern. Saat ini mendukung:

- Gambar: PNG, JPG/JPEG, WEBP -> PNG, JPG, WEBP, PDF
- PDF -> JPG atau PNG (semua halaman dikirim sebagai ZIP bila lebih dari satu)
- Office: DOC/DOCX, XLS/XLSX, PPT/PPTX -> PDF melalui LibreOffice
- Batch conversion hingga 10 file -> ZIP
- Drag & drop, dynamic format selector, progress, dan installable PWA
- Image Tools: compress gambar JPG, PNG, dan WEBP
- Install sebagai aplikasi desktop/mobile melalui PWA

## Menjalankan lokal

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Buka `http://127.0.0.1:8000`.

## Install sebagai aplikasi

Jalankan server melalui HTTPS atau `localhost`, lalu buka URL di Chrome/Edge.
Klik tombol **INSTALL APP** di header jika muncul, atau gunakan menu browser
**Install Flux / Add to Home Screen**. Setelah terpasang, Flux terbuka di window
standalone tanpa address bar seperti aplikasi biasa.

Shell aplikasi (UI, CSS, JavaScript, logo) tersedia offline setelah pernah dibuka.
Proses konversi dan compress tetap membutuhkan koneksi ke server karena engine
FastAPI/LibreOffice berjalan di backend online. Jika sedang offline, aplikasi
masih dapat dibuka dan menampilkan status OFFLINE, tetapi operasi server akan
ditunda sampai koneksi kembali.

### LibreOffice

Konversi dokumen Office membutuhkan LibreOffice di mesin server:

- Windows: install dari https://www.libreoffice.org/download/download/, lalu restart server Uvicorn.
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y libreoffice`

Untuk memastikan instalasi Windows terdeteksi, jalankan:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```

Jika path tersebut tidak ada, LibreOffice belum terpasang. Dockerfile project memasang
LibreOffice otomatis, tetapi hanya digunakan jika aplikasi dijalankan melalui Docker.
Tanpa LibreOffice, endpoint tetap berjalan dan mengembalikan pesan error yang jelas untuk file Office.

## Endpoint

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/` | Aplikasi web |
| GET | `/supported-formats` | Format sumber dan tujuan |
| GET | `/health` | Status server |
| POST | `/convert` | Konversi satu file |
| POST | `/convert/batch` | Konversi hingga 10 file menjadi ZIP |
| POST | `/tools/image/compress` | Compress gambar dengan `quality` 1-100 |

Request konversi menggunakan `multipart/form-data`:

- `file`: satu file untuk `/convert`
- `files`: satu atau beberapa file untuk `/convert/batch`
- `target_format`: misalnya `pdf`, `png`, atau `jpg`

Endpoint compress menggunakan:

- `file`: gambar JPG, PNG, atau WEBP
- `quality`: angka `1` sampai `100`

Struktur saat ini menggunakan package `app/` sebagai backend aktif (setara dengan
`backend/` pada blueprint awal) agar endpoint dokumen/PDF yang sudah ada tetap kompatibel.
Folder `backend/` berisi adapter kompatibilitas untuk struktur blueprint tersebut.

File temporary dibersihkan setelah response selesai dikirim. Batas setiap file adalah 25 MB.

## Deploy ke Render dengan Docker

File [Dockerfile](./Dockerfile) sudah memasang LibreOffice secara otomatis.

1. Push repository ke GitHub.
2. Di Render pilih **New > Web Service**, lalu hubungkan repository.
3. Pilih environment **Docker**.
4. Deploy. Render akan mengisi variabel `PORT`; container sudah menggunakannya otomatis.
5. Setelah selesai, buka URL HTTPS dari Render.

Build lokal:

```powershell
docker build -t universal-converter .
docker run --rm -p 8000:8000 universal-converter
```

Uji LibreOffice di container:

```powershell
docker run --rm universal-converter soffice --version
```

## Testing cepat

1. Jalankan server dan buka halaman utama.
2. Seret gambar, PDF, atau dokumen Office ke area upload.
3. Pilih tool seperti **Convert** atau **Compress**.
4. Atur format/quality lalu klik **Run tool**.
5. Untuk pemasangan PWA, gunakan Chrome/Edge pada `localhost` atau HTTPS lalu pilih **Install App**.

Pemeriksaan otomatis yang digunakan:

```powershell
python -m compileall -q app
python -c "from app.main import app; print(app.title)"
```
