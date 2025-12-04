# 🎵 Smart Playlist Generator — Desktop App

Smart Playlist Generator adalah aplikasi desktop yang mampu membuat playlist musik secara otomatis berdasarkan *mood*, *activity*, *time of day*, serta *genre optional*. Program ini dibangun menggunakan **Python**, **Tkinter GUI**, dan **ytmusicapi**, serta dilengkapi fitur modern seperti background threading, ekspor playlist, dan voice command.

---

## 🚀 Features

### ✔ Playlist Generator
Menghasilkan playlist berdasarkan kombinasi:
- Mood → chill, happy, sad, energetic, dll.
- Activity → study, workout, relax, sleep, commute.
- Time of Day → morning, afternoon, evening, night.
- Genre (opsional)

### ✔ Modern Spotify-Style GUI
- Dark mode + Spotify green
- Blurred background
- Responsive layout
- Interactive sidebar + playlist panel

### ✔ Voice Command
- Tekan tombol 🎤, bicara → aplikasi otomatis memahami perintah
- Contoh: *"buat playlist chill study malam"*

### ✔ Background Worker
- Tidak membuat UI freeze saat proses generate

### ✔ Undo Support
- Kembalikan playlist sebelumnya dengan 1 klik

### ✔ Export
- Save playlist ke **TXT**
- Save playlist ke **JSON**

### ✔ YouTube Music Integration
- Cari lagu dari YT Music
- Double-click untuk membuka musik di browser

---

## 🛠 Requirements

- Python **3.10 – 3.12**
- Internet (untuk YT Music API)

Install dependencies:
pip install -r requirements.txt

Jika belum punya requirements.txt, gunakan:
ytmusicapi
pillow
speechrecognition
pyaudio

---

## ▶️ Cara Menjalankan Program

python main.py
Jika voice command tidak bekerja di Windows, jalankan:
pip install pipwin
pipwin install pyaudio

---

## 📘 How It Works

1. Pemilih mood, activity, time, genre
2. Recommender membuat query → "chill study night music"
3. Program memanggil YTMusicAPI.search()
4. Data diubah menjadi objek Track
5. Playlist ditampilkan di TreeView

User dapat:
- membuka lagu
- menyimpan playlist
- undo
- redo
- menjalankan voice command

---

## 🧠 Tech Stack
- Komponen	Teknologi
- GUI	Tkinter
- API	ytmusicapi
- Image Processing	Pillow
- Voice Recognition	SpeechRecognition
- Background Task	Threading + Queue

---

## 📄 License
MIT License — bebas digunakan, dimodifikasi, dan dikembangkan.
