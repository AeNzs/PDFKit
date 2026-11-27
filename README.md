# PDF整理工具

Aplikasi desktop Windows berbasis **PySide6** yang menyatukan 5 alur kerja dokumen kantor (PDF & Excel) dalam satu tampilan antarmuka multibahasa (**Bahasa Indonesia**, **简体中文**, **English**) lengkap dengan mode **Terang / Gelap**.

---

## Fitur Utama

1. **01 PDF Split & TTD (Split PDF + Tanda Tangan Otomatis)**
   - Memisahkan halaman PDF sumber berdasarkan kata kunci di file Excel (Kolom A: kata kunci, Kolom B: nama file output).
   - Menempel gambar tanda tangan (`.png` / `.jpg`) secara otomatis berdasarkan teks jangkar (`PyMuPDF`) maupun koordinat halaman.
   - **Preview & Atur Koordinat TTD interaktif:** tampilkan halaman PDF asli beserta posisi gambar tanda tangan, seret kotak TTD untuk menggeser koordinat, seret sudut kanan-bawah untuk ubah ukuran, atau klik dua kali untuk memindahkan posisi dengan koordinat PDF real-time.
   - Mendukung tambah, edit, hapus, simpan, muat, dan reset aturan tanda tangan (`signature_rules.json`).
2. **02 Pindah File Excel (Batch File Mover)**
   - Membaca `mapping.xlsx` langsung via `openpyxl` (mulai baris 2, Kolom A: nama file, Kolom B: folder tujuan) tanpa perlu Microsoft Excel terinstal.
   - Fitur cari `mapping.xlsx` otomatis ke folder induk, preview status file sebelum dipindahkan, serta ringkasan hasil nyata (*Dipindahkan*, *Tidak Ditemukan*, *Kesalahan*).
3. **03 Export Daftar File (List Exporter)**
   - Menghasilkan file teks UTF-8 (`folderlist.txt`, `filelist.txt`, `folder_file_list.txt`) dari satu folder target lengkap dengan panel preview sebelum export.
4. **04 Mapping by Logic (Tanpa Excel)**
   - Mode 1: membuat folder invoice otomatis (`PJI-{PT}-{BULAN}物资结算开票资料`) dari file bulanan mentah lewat **Tabel Alias Kode -> PT** & Regex, memindahkan file bulanan (`MOVE`), lalu otomatis menyalin (`COPY`) file tetap (konsinyasi, NPWP, dll.) dari 1, 2, 3, atau lebih jalur folder sumber (termasuk folder jaringan UNC).
   - Mode 2: memindai subfolder yang sudah ada via patokan Regex dan menyisipkan file master yang cocok.
5. **Auto-Update & Cek Versi**
   - Pengecekan versi otomatis ke GitHub Releases saat aplikasi dibuka serta tombol **Cek Update** manual dengan progress download & auto-restart installer.

---

## Cara Install (Untuk Pengguna Umum, Tanpa Python)

Pengguna biasa **tidak perlu menginstal Python, library apa pun, ataupun Microsoft Excel**.

### File yang Harus Di-download / Di-install
- **Nama file installer:** `PDF整理工具_Setup.exe`
- **Lokasi file:**
  - Dari halaman **Releases** GitHub: https://github.com/AeNzs/PDFKit/releases
  - Atau di folder hasil build lokal: `installer_output\PDF整理工具_Setup.exe`
- **Kebutuhan sistem:** Windows 10 / Windows 11 (64-bit)

### Langkah Instalasi
1. Download atau salin file **`PDF整理工具_Setup.exe`** ke komputer Windows target.
2. Klik dua kali **`PDF整理工具_Setup.exe`**.
   - Jika muncul jendela biru **Windows Defender SmartScreen** (*"Windows protected your PC"*), klik **More info** lalu klik **Run anyway**.
3. Pilih mode instalasi yang diinginkan:
   - **Install for me only** (disarankan, tidak memerlukan password Administrator).
   - **Install for all users** (memasang ke `Program Files`, membutuhkan izin Administrator).
4. Ikuti wizard instalasi sampai selesai (centang **Create a desktop shortcut** jika ingin ikon di Desktop).
5. Buka aplikasi melalui shortcut **`PDF整理工具`** di Desktop atau Start Menu.

### Lokasi Penyimpanan Aturan Tanda Tangan & Uninstall
- **File aturan tanda tangan (`signature_rules.json`):** tersimpan otomatis di `%APPDATA%\PDF整理工具\signature_rules.json`.
- **Cara uninstall:** buka **Windows Settings -> Apps -> Installed apps**, cari **`PDF整理工具`**, lalu klik **Uninstall**.

---

## Menjalankan dari Source Code (Untuk Developer)

Kebutuhan: **Python 3.11 atau lebih baru** (64-bit).

```powershell
git clone https://github.com/AeNzs/PDFKit.git
cd PDFKit

python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

---

## Build Ulang Installer (`PDF整理工具_Setup.exe`)

Kebutuhan tambahan: **Inno Setup 6** (https://jrsoftware.org/isinfo.php).

Jalankan skrip berikut dari folder proyek:

```powershell
.\packaging\build_exe.bat
```

Skrip ini akan otomatis:
1. Membuat virtual environment `.venv` dan menginstal dependensi dari `requirements.txt` (jika belum ada).
2. Mengonversi `assets\applogo.png` menjadi `assets\applogo.ico`.
3. Mem-build bundle aplikasi via PyInstaller ke `dist\PDF整理工具\`.
4. Mengompilasi installer Windows ke `installer_output\PDF整理工具_Setup.exe`.

---

## Struktur Proyek

```text
PDF整理工具/
├── app.py                  # Entry point aplikasi
├── requirements.txt        # Daftar dependensi Python
├── assets/                 # Logo aplikasi (PNG & ICO)
│   ├── applogo.png
│   └── applogo.ico
├── core/                   # Mesin logika & kamus bahasa
│   ├── i18n.py
│   ├── pdf_sign.py
│   ├── file_mover.py
│   └── list_exporter.py
├── ui/                     # Antarmuka PySide6 & tema Light/Dark
│   ├── main_window.py
│   ├── theme.py
│   ├── widgets.py
│   ├── tab_pdf_sign.py
│   ├── tab_file_mover.py
│   └── tab_list_exporter.py
└── packaging/              # Skrip icon, PyInstaller, dan Inno Setup
    ├── make_icon.py
    ├── build_exe.bat
    └── installer.iss
```
