# 🟢 GREEN STORM v3.0 — SUPER GANS EDITION

> **Network Stress Tester** — multiprocessing + asyncio + `sendmmsg` batch.  
> **No root required.** 100% nyata, zero simulasi.

---

## ⚠️ DISCLAIMER — BACA DULU

> **Tool ini HANYA untuk pengujian beban (stress testing) pada jaringan yang KAMU MILIKI atau punya izin tertulis eksplisit untuk diuji.**
>
> Menjalankan tool ini terhadap jaringan, server, atau perangkat milik orang lain **tanpa izin** adalah **tindakan ilegal** di hampir semua yurisdiksi — termasuk pelanggaran UU ITE (Indonesia), CFAA (AS), Computer Misuse Act (UK), dan regulasi serupa di negara lain.
>
> **Penulis tidak bertanggung jawab atas penyalahgunaan.** Dengan menggunakan tool ini, kamu setuju bahwa kamu bertanggung jawab penuh atas segala konsekuensi hukum maupun teknis.
>
> Gunakan di:
> - ✅ Lab pribadi / homelab
> - ✅ Jaringan kantor dengan izin tertulis
> - ✅ Infrastruktur cloud milik sendiri (AWS/Azure/GCP)
> - ✅ Target CTF / lab legal (HackTheBox, TryHackMe, VulnHub)
>
> ❌ **JANGAN** gunakan di jaringan publik, ISP, WiFi tetangga, atau server orang lain.

---

## 📖 Apa Itu GREEN STORM?

**GREEN STORM** adalah tool **stress testing jaringan** yang dirancang untuk menguji ketahanan infrastruktur terhadap berbagai vektor serangan DoS (Denial of Service) di layer 3, 4, dan 7.

Berbeda dari tool "simulasi" atau "fake packet", GREEN STORM mengirim **paket jaringan sungguhan** melalui socket kernel — persis seperti yang dilakukan tool profesional seperti `hping3`, `slowloris`, atau `goldeneye` — tapi dengan arsitektur modern yang jauh lebih efisien:

- **Multiprocessing** — setiap vektor berjalan di proses terpisah, semua core CPU terpakai.
- **asyncio** — ribuan koneksi L7 paralel per proses tanpa thread overhead.
- **`sendmmsg` syscall** (Linux) — kirim 64 paket UDP dalam 1 syscall, bukan 64 syscall.
- **Zero throttling** — tidak ada `sleep` antar-paket, full-speed sesuai kapasitas hardware & jaringan.

---

## ✨ Fitur

### Vektor Serangan (14 Mode)

| # | Vektor | Layer | Deskripsi |
|---|--------|-------|-----------|
| 01 | **HTTP GET Flood** | L7 | Async GET request terus-menerus ke target |
| 02 | **Slowloris Burst** | L7 | Ribuan koneksi keep-alive dibuka bersamaan |
| 03 | **TLS Handshake Flood** | L7 | Full TLS handshake berulang, membebani CPU server |
| 04 | **UDP sendmmsg Batch** | L4 | 64 paket UDP per syscall via `sendmmsg` |
| 05 | **UDP Broadcast Storm** | L4 | Paket ke `255.255.255.255` di ~30 port, banjiri LAN |
| 06 | **SSDP + mDNS Multicast** | L4 | Multicast flood, saturasi access point / switch |
| 07 | **SYN Connect Flood** | L4 | Non-blocking connect, hampir tanpa close, backlog penuh |
| 08 | **ICMP Flood** | L3 | Ping payload maksimum (65507 byte), via subprocess |
| 09 | **DNS Flood** | L4 | Query DNS batch 64× per loop |
| 10 | **NTP Flood** | L4 | Request NTP mode 3 batch 64× |
| 11 | **Memcached Flood** | L4 | Request memcached UDP batch 64× |
| 12 | **★ SUPER GANS L7 Assault** | L7 | HTTP + TLS + Slowloris serentak |
| 13 | **★ SUPER GANS LAN Blackout** | L3–4 | Broadcast + SSDP + mDNS + gateway flood |
| 14 | **★ SUPER GANS All-Out** | ALL | Semua vektor nyala bareng, satu target + seluruh LAN |

### Keunggulan

- 🚀 **No root** — semua vektor bisa jalan sebagai user biasa.
- 🧠 **Auto CPU scaling** — jumlah worker = jumlah core CPU.
- 📊 **Real-time stats** — PPS (packets/detik) & total live di terminal.
- 🎯 **Dual-mode** — bisa hantam satu target IP, atau bikin **seluruh jaringan LAN lag**.
- 🎨 **UI neon hijau** — keren, jelas, gampang dibaca.
- ⏱️ **Durasi fleksibel** — angka = detik, `0` = infinite sampai `Ctrl+C`.

---

## 📦 Instalasi & Penggunaan

### Prasyarat
- **Python 3.8+**
- **Linux** (rekomendasi — `sendmmsg` aktif), macOS, atau Windows
- Tidak butuh library eksternal (Pure stdlib).

### Clone & jalankan

```bash
git clone https://github.com/tirekx849-crypto/Dos.git
cd Dos
python3 green_storm_v3.py
