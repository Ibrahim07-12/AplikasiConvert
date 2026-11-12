---
title: Flux — All-in-One File Toolkit
emoji: ⚡
colorFrom: orange
colorTo: yellow
sdk: docker
app_port: 7860
---

# Flux — All-in-One File Toolkit

PWA berbasis FastAPI dengan desain Brutalist Modern. Saat ini mendukung:

- Gambar: PNG, JPG/JPEG, WEBP -> PNG, JPG, WEBP, PDF
- PDF -> JPG atau PNG (semua halaman dikirim sebagai ZIP bila lebih dari satu)
- Office: DOC/DOCX, XLS/XLSX, PPT/PPTX -> PDF melalui LibreOffice
- Batch conversion hingga 10 file -> ZIP
- Drag & drop, dynamic format selector, progress, dan installable PWA
- Image Tools: compress gambar JPG, PNG, dan WEBP
- Install sebagai aplikasi desktop/mobile melalui PWA
- Windows desktop app offline melalui native launcher + PyInstaller
- Tool image/PDF aktif melalui endpoint `/tools/run`

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

## Aplikasi Windows offline

Versi desktop menjalankan FastAPI secara lokal dan membuka Flux dalam window
native, jadi tidak membutuhkan browser atau koneksi internet. Siapkan Python
3.12 dan LibreOffice di Windows terlebih dahulu, lalu jalankan:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\build_windows.ps1
```

Hasil portable tersedia di `dist\Flux\Flux.exe`. Folder `dist\Flux` harus
dibagikan utuh karena berisi dependency aplikasi.

Untuk membuat installer `.exe`, install Inno Setup, jalankan `build_windows.ps1`,
lalu buka [installer/Flux.iss](./installer/Flux.iss) dengan Inno Setup dan pilih
**Compile**. Hasilnya ada di folder `installer-output`.

LibreOffice belum dibundel ke executable karena ukurannya besar dan lisensinya
memiliki distribusi tersendiri. Install LibreOffice sekali di Windows agar fitur
PPT/DOCX/XLSX -> PDF berjalan offline. Image/PDF tools tidak membutuhkan internet.
Pada komputer pengembangan ini LibreOffice sudah terpasang dan terdeteksi dari
`C:\Program Files\LibreOffice\program\soffice.exe`.

## Android dan iOS

Versi PWA dapat dipasang di Android/iOS setelah aplikasi tersedia melalui URL
HTTPS (misalnya domain hosting atau tunnel). Android Chrome memakai **Install
App/Add to Home Screen**, sedangkan iOS Safari memakai **Share > Add to Home
Screen**. Backend tetap harus online untuk konversi karena Android/iOS tidak
membawa LibreOffice desktop.

Versi Windows native tidak dapat dijalankan langsung di Android/iOS. Untuk APK/IPA
native diperlukan build mobile terpisah, Android SDK untuk APK, serta macOS/Xcode
untuk IPA. PWA adalah jalur lintas-platform yang sudah tersedia sekarang.

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
| POST | `/tools/run` | Menjalankan tool dari dual mapping |

Request konversi menggunakan `multipart/form-data`:

- `file`: satu file untuk `/convert`
- `files`: satu atau beberapa file untuk `/convert/batch`
- `target_format`: misalnya `pdf`, `png`, atau `jpg`

Endpoint compress menggunakan:

- `file`: gambar JPG, PNG, atau WEBP
- `quality`: angka `1` sampai `100`

Tool lokal yang aktif:

- Image: convert, compress, resize, crop, rotate, flip, grayscale, watermark, remove-bg
- PDF: convert, merge, split, remove-pages, rotate-pages, compress, to-images,
  add-page-numbers, extract-text, protect
- Office: convert ke PDF/JPG/PNG, compress ke PDF, extract-images untuk DOCX/PPTX
- HTML: minify dan convert/screenshot ke PDF/JPG/PNG melalui LibreOffice

Konversi PDF ke DOCX/XLSX/PPTX menghasilkan container Office berisi render visual
setiap halaman. Ini menjaga isi halaman tetap terlihat, tetapi bukan rekonstruksi
sempurna struktur teks/tabel asli.

Struktur saat ini menggunakan package `app/` sebagai backend aktif (setara dengan
`backend/` pada blueprint awal) agar endpoint dokumen/PDF yang sudah ada tetap kompatibel.
Folder `backend/` berisi adapter kompatibilitas untuk struktur blueprint tersebut.

File temporary dibersihkan setelah response selesai dikirim. Batas setiap file adalah 25 MB.

## Deploy ke Hugging Face Spaces dengan Docker

File [Dockerfile](./Dockerfile) sudah memasang LibreOffice secara otomatis dan
menjalankan FastAPI pada port `7860`, sesuai konfigurasi Docker Spaces.

### Opsi A — Upload melalui Git

1. Buat Space baru di https://huggingface.co/new-space.
2. Pilih **Docker** sebagai SDK.
3. Pilih visibility **Public** atau **Private**.
4. Clone repository Space tersebut.
5. Salin project ini ke repository Space.
6. Commit dan push ke Hugging Face.
7. Tunggu proses build selesai, lalu buka URL Space.

Contoh:

```powershell
git clone https://huggingface.co/spaces/USERNAME/SPACE_NAME
Copy-Item -Path .\* -Destination .\SPACE_NAME -Recurse -Force
Set-Location .\SPACE_NAME
git add .
git commit -m "Deploy Flux to Hugging Face Spaces"
git push
```

### Opsi B — Upload melalui halaman Space

Buat Space dengan SDK **Docker**, lalu upload file berikut di root Space:

```text
Dockerfile
README.md
requirements.txt
app/
frontend/
backend/
```

Front matter README harus tetap memiliki:

```yaml
sdk: docker
app_port: 7860
```

Hugging Face akan membaca Dockerfile dan membangun container otomatis.

Build lokal:

```powershell
docker build -t universal-converter .
docker run --rm -p 7860:7860 universal-converter
```

Uji LibreOffice di container:

```powershell
docker run --rm universal-converter soffice --version
```

### Environment Variables

Tidak ada environment variable wajib. Hugging Face Spaces memakai port `7860`
yang sudah dikonfigurasi di README Space dan Dockerfile.

### Catatan penyimpanan

File upload dan output hanya berada di folder temporary selama request dan
dihapus setelah response selesai. Jangan menyimpan credential atau data sensitif
di Space. Konversi tetap membutuhkan koneksi ke Space; PWA hanya menyimpan
app shell untuk membuka UI saat offline.

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
