# Jangarekam

Adalah aplikasi sederhana yang dibangun menggunakan bahasa pemrograman Python dan pustaka OpenCV untuk merekam video dari beberapa webcam atau cctv sekaligus.

Aplikasi ini dirancang dengan tujuan memudahkan pengguna dalam melakukan perekaman video dari beberapa sumber kamera secara bersamaan. Berikut adalah fitur dan deskripsi dari aplikasi ini:

## Fitur Utama:

- **Bisa merekam banyak Webcam atau CCTV:** Mendukung perekaman video dari beberapa webcam atau cctv yang terhubung ke komputer.

- **Menyimpan video secara lokal:** Video yang direkam dapat disimpan ke dalam format file AVI atau mp4 dan bisa ditentukan lokasinya di file config `webcam_config.yaml`.

- **Menggunakan `commandline`:** Aplikasi memiliki tampilan `commandline` yang mudah dipahami, dan bisa berjalan secara tersembunyi.

- **Memiliki file konfigurasi yang sederhana:** Pengguna dapat mengatur resolusi dan frame rate dan lain-lain sesuai dengan kebutuhan, hanya dengan mengubah file konfigurasi `webcam_config.yaml`.

- **Metadata:** Hasil rekaman dicatat dalam format `json`, sehingga memudahkan untuk di integrasikan dengan aplikasi lainnya.

- **Durasi video rekaman bisa di pecah:** Hasil video rekaman bisa di pecah-pecah dalam durasi tertentu. Misalkan per 15 menit, 30 menit, dll

## Instalasi

Install `python3` dengan perintah dibawah, khusus untuk linux keluarga `debian`

``$ sudo apt install -y python3``

Dapatkan kode `jangarekam` di github dengan url dibawah

``$ git clone git@github.com:yan13to/jangarekam.git``

Masuk ke direktori utama

``$ cd jangarekam``

Install paket-paket yang dibutuhkan untuk menjalankan aplikasinya dengan perintah dibawah

``$ pip install -r requirements.txt``

Copy `webcam_config.yaml.example` ke `webcam_config.yaml`

``$ cp webcam_config.yaml.example webcam_config.yaml``

Ubah file konfigurasi sesuai dengan kebutuhan, kemudian simpan

``$ vim webcam_config.yaml`` 

Ketik perintah dibawah untuk memulai proses perekaman cctv

``$ python3 record.py``

Untuk menghentikan perekaman cukup dengan mengetikan perintah

``Ctrl + D``

## Service

Untuk bisa merekam secara otomatis dan tersembunyi pada saat komputer dinyalakan, perlu dibuat `service` untuk menjalankan aplikasi diatas, saat ini hanya akan dibahas bagaimana cara membuat `service` di `ubuntu` dengan memanfaatkan `systemd` yang populer. Gunakan template file unit `systemd` yang berada di folder `ci`, dan sesuaikan dengan sistem yang ada. 

### 1. Misalkan file unit-nya dinamai `jangarekam.service` kemudian simpan di direktori `/etc/systemd/system/`.

```
[Unit]
Description=Aplikasi untuk merekam webcam atau cctv secara bersamaan
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/jangarekam/record.py
WorkingDirectory=/opt/jangarekam
StandardOutput=inherit
StandardError=inherit
Restart=always
User=your_user
Group=your_group
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target

```
### 2. Sesuaikan Izin file dan Reload Systemd

Setelah Anda membuat file unit, pastikan file tersebut memiliki izin yang benar dan kemudian muat ulang konfigurasi `systemd`.

``$ sudo chmod 644 /etc/systemd/system/jangarekam.service``

``$ sudo systemctl daemon-reload``

### 3. Aktifkan Service

Hidupkan service dan pastikan service tersebut aktif saat booting.

``$ sudo systemctl start jangarekam.service``

``$ sudo systemctl enable jangarekam.service``

### 4. Periksa Status

``$ sudo systemctl status jangarekam.service``

### 5. Loggin

Jika ingin melihat log dari service ini, gunakan perintah ``journalctl``

``$ journalctl -u record_webcams.service -f``
