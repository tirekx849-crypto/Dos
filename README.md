# 🟢 GREEN STORM v3.0 — SUPER GANS EDITION

> **Network Stress Tester** — Multiprocessing + Asyncio + `sendmmsg` batch.  
> **No root required.** 100% nyata, zero simulasi.

![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20android%20%7C%20termux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ⚠️ DISCLAIMER — BACA DULU

> **Tool ini HANYA untuk pengujian beban (stress testing) pada jaringan yang KAMU MILIKI atau punya izin tertulis eksplisit untuk diuji.**
>
> Menjalankan tool ini terhadap jaringan, server, atau perangkat milik orang lain **tanpa izin** adalah **tindakan ilegal** di hampir semua yurisdiksi — termasuk pelanggaran UU ITE (Indonesia), CFAA (AS), Computer Misuse Act (UK), dan regulasi serupa di negara lain.
>
> **Penulis tidak bertanggung jawab atas penyalahgunaan.** Dengan menggunakan tool ini, kamu setuju bahwa kamu bertanggung jawab penuh atas segala konsekuensi hukum maupun teknis.
>
> Gunakan hanya di:
> - ✅ Lab pribadi / homelab
> - ✅ Jaringan kantor dengan izin tertulis
> - ✅ Infrastruktur cloud milik sendiri (AWS/Azure/GCP)
> - ✅ Target CTF / lab legal (HackTheBox, TryHackMe, VulnHub)
>
> ❌ **JANGAN** gunakan di jaringan publik, ISP, WiFi tetangga, atau server orang lain.

---

## 📖 Apa Itu GREEN STORM?

**GREEN STORM** adalah tool **stress testing jaringan** yang dirancang untuk menguji ketahanan infrastruktur terhadap serangan DoS (Denial of Service) di layer 3, 4, dan 7. 

Berbeda dari tool "simulasi", GREEN STORM mengirim **paket jaringan sungguhan** melalui socket kernel — persis seperti `hping3`, `slowloris`, atau `goldeneye` — tapi dengan arsitektur modern yang jauh lebih efisien:

- **Multiprocessing** — Setiap vektor berjalan di proses terpisah, semua core CPU terpakai.
- **asyncio** — Ribuan koneksi L7 paralel per proses tanpa *thread overhead*.
- **`sendmmsg` syscall** (Linux) — Kirim 64 paket UDP dalam 1 syscall, bukan 64 syscall.
- **Zero throttling** — Tidak ada `sleep` antar-paket, full-speed sesuai kapasitas hardware & jaringan.

---

## ✨ Fitur (14 Mode Serangan)

| # | Vektor | Layer | Deskripsi |
|---|--------|-------|-----------|
| 01 | **HTTP GET Flood** | L7 | Async GET request terus-menerus ke target. |
| 02 | **Slowloris Burst** | L7 | Ribuan koneksi keep-alive dibuka bersamaan. |
| 03 | **TLS Handshake Flood** | L7 | Full TLS handshake berulang, membebani CPU server. |
| 04 | **UDP sendmmsg Batch** | L4 | 64 paket UDP per syscall via `sendmmsg`. |
| 05 | **UDP Broadcast Storm** | L4 | Paket ke `255.255.255.255` di ~30 port, banjiri LAN. |
| 06 | **SSDP + mDNS Multicast** | L4 | Multicast flood, saturasi access point / switch. |
| 07 | **SYN Connect Flood** | L4 | Non-blocking connect, memenuhi backlog server. |
| 08 | **ICMP Flood** | L3 | Ping payload maksimum (65507 byte), via subprocess. |
| 09 | **DNS Flood** | L4 | Query DNS batch 64× per loop. |
| 10 | **NTP Flood** | L4 | Request NTP mode 3 batch 64×. |
| 11 | **Memcached Flood** | L4 | Request memcached UDP batch 64×. |
| 12 | **★ SUPER GANS L7 Assault** | L7 | HTTP + TLS + Slowloris serentak. |
| 13 | **★ SUPER GANS LAN Blackout** | L3–4 | Broadcast + SSDP + mDNS + gateway flood. |
| 14 | **★ SUPER GANS All-Out** | ALL | Semua vektor nyala bareng, satu target + seluruh LAN. |

---

## 📦 Panduan Instalasi & Penggunaan

Tool ini murni menggunakan **Python 3 Standard Library**. **Tidak butuh** `pip install` library apa pun.

### 📱 CARA 1: Menjalankan di Termux (Android)

Termux sangat cocok untuk mode L4 (UDP/TCP) dan L7 (HTTP/TLS). *Catatan: Fitur L3 (ICMP/Ping) biasanya diblokir oleh sistem Android tanpa root.*

1. **Buka Termux**, lalu update repositori package:
   ```bash
   pkg update && pkg upgrade -y
