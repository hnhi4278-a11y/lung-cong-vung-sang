#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Báo cáo tuần 927 HG (gửi sếp) — số liệu CHUẨN khớp báo cáo Năng Suất của sếp.

Nguồn:
- Lượt khách / DT / AOV / Khách mới / R90 / R90-180 / R180+ : báo cáo Sale v7 (0019)
  `sale-salon-day/sale-salon-day-<ngày>.json` lọc Salon_ID=22 — 30Shine tự ghi mỗi ngày,
  LUÔN TƯƠI, khớp 100% báo Năng Suất của sếp. ĐÂY LÀ SỐ CHUẨN.
- CSKH (gọi menu Booking/Hủy) + Hotline (mục tiêu/đã gọi): reports.30shine.com 0024 & 0001.
- FB: báo 0005 (rating-cldv), bill 1-2-3 sao + tag.
- Để trống (điền tay): GSC (giám sát cam, cần token), MKT Google Map/Clip, Truyền thông.

Chạy sáng Thứ 2: so tuần vừa rồi (T2–CN) với tuần trước nữa.
  python3 build_bc_tuan_927.py            # tự lấy theo hôm nay
  python3 build_bc_tuan_927.py 2026-10-20 # giả lập chạy ngày đó
"""
import sys, json, re, urllib.request
from collections import Counter
from datetime import date, timedelta

SALON = 22
CHUA = [0, 19, 20, 21, 17]
NOTCALLED = 17
B19 = "https://reports.30shine.com/0019_baocao-sale-v7/sale-salon-day/sale-salon-day-"
HLS_URL = "https://maya-cao.github.io/hen-lich-stylist/"  # stylist đặt lịch (mã hoá, mật khẩu ở env HLS_PW)
B5 = "https://reports.30shine.com/0005_BaocaoChatluong"
B1 = "https://reports.30shine.com/0001-phannhomkhachhang"
B24 = "https://reports.30shine.com/0024-bc-goi-menu-book-huy"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Accept": "*/*"}


def _fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def get_json(url):
    try:
        d = json.loads(_fetch(url))
        return d if isinstance(d, list) else d.get("data", d)
    except Exception:
        return []


# ---- Nguồn CHUẨN: báo cáo Sale v7 (0019), sale-salon-day theo ngày, lọc Salon_ID=22 ----
# Map field 0019 -> khoá dùng trong report
_F19 = {"tong": "DT_all", "khach": "SL_khach_BI", "kh_moi": "SL_khach_moi",
        "kh_r90": "SL_khach_r90", "kh_r90_180": "SL_khach_r90_180", "kh_r180plus": "SL_khach_r180plus"}
_DAY_CACHE = {}
def salon_day(d):
    """Trả về dict số liệu salon 927 cho 1 ngày (hoặc None nếu chưa có data)."""
    if d in _DAY_CACHE:
        return _DAY_CACHE[d]
    out = None
    for row in get_json(f"{B19}{d}.json"):
        if row.get("Salon_ID") == SALON:
            out = {k: (row.get(f19) or 0) for k, f19 in _F19.items()}
            break
    _DAY_CACHE[d] = out
    return out


def dn(s):
    return str(s or "").replace("/", "-")[:10]


# ---- Stylist đặt lịch (báo cáo maya-cao, AES-GCM, mật khẩu ở env HLS_PW) ----
def _aesgcm_decrypt(key, iv, ctfull):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(iv, ctfull, None)
    except ImportError:
        pass
    try:
        from Crypto.Cipher import AES  # pycryptodome
        return AES.new(key, AES.MODE_GCM, nonce=iv).decrypt_and_verify(ctfull[:-16], ctfull[-16:])
    except ImportError:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cryptography"], check=False)
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(iv, ctfull, None)


def stylist_week(days):
    """Trả (lượt hẹn h, lượt nhận khách n, số stylist có hẹn) salon 927 cho các ngày `days` giao với data report."""
    import os, base64, hashlib
    pw = os.environ.get("HLS_PW", "").strip()
    if not pw:
        return None
    try:
        s = _fetch(HLS_URL)
        enc = json.loads(re.search(r"ENC\s*=\s*(\{.*?\});", s, re.S).group(1))
        key = hashlib.pbkdf2_hmac("sha256", pw.encode(), base64.b64decode(enc["salt"]), enc["iter"], 32)
        pt = _aesgcm_decrypt(key, base64.b64decode(enc["iv"]), base64.b64decode(enc["ct"]))
        d = json.loads(pt)
        dates = d["dates"]
        wk = set(days)
        n = h = 0
        sty = set()
        for r in d["rows"]:
            if r[0] != SALON:
                continue
            if 0 <= r[2] < len(dates) and dates[r[2]] in wk:
                n += r[3]; h += r[4]
                if r[4] > 0:
                    sty.add(r[1])
        cov = [dt for dt in dates if dt in wk]
        return dict(h=h, n=n, sty=len(sty), cov=cov)
    except Exception:
        return None


def week_bounds(run_day):
    monday_this = run_day - timedelta(days=run_day.weekday())
    last_mon = monday_this - timedelta(days=7)
    prev_mon = monday_this - timedelta(days=14)
    def days(mon):
        return [(mon + timedelta(days=i)).isoformat() for i in range(7)]
    return days(last_mon), days(prev_mon), last_mon, prev_mon


def compute(days):
    rev = {k: 0 for k in ["tong", "khach", "kh_moi", "kh_r90", "kh_r90_180", "kh_r180plus"]}
    for d in days:
        r = salon_day(d)
        if r:
            for k in rev:
                rev[k] += r.get(k, 0) or 0
    # Hotline: phân phối (mục tiêu gọi) & đã gọi (đã xử lý)
    pp_t = xl_t = 0
    for d in days:
        pp, kn, cxn = set(), set(), set()
        for x in get_json(f"{B1}/data/callhis_{d}.json"):
            if x.get("SalonId") != SALON:
                continue
            cid = x["CustomerId"]; sub = x.get("SubStatus")
            pp.add(cid)
            if sub is not None:
                (cxn if int(sub) in CHUA else kn).add(cid)
        pp_t += len(pp); xl_t += len(kn) + len(cxn)
    # CSKH: gọi menu Booking (2) & Hủy (9)
    seen = {2: {}, 9: {}}
    for d in days:
        for r in get_json(f"{B24}/data/call-book-huy_{d}.json"):
            if r.get("salon_id") != SALON:
                continue
            t = r.get("type")
            if t not in (2, 9):
                continue
            ss = r.get("sub_status")
            called = ss is not None and int(ss) != NOTCALLED
            key = f"{dn(r['call_date'])}|{r.get('customer_id')}"
            seen[t][key] = seen[t].get(key, False) or called
    def a(m):
        return len(m), sum(1 for v in m.values() if v)
    # FB báo 0005
    stars = {k: 0 for k in ["1_sao", "2_sao", "3_sao", "4_sao", "5_sao"]}
    tags = Counter(); low_bills = []
    for d in days:
        for r in get_json(f"{B5}/data/rating-cldv-salon-{d}.json"):
            if "927" in (r.get("salon_name") or ""):
                for k in stars:
                    stars[k] += r.get(k, 0) or 0
        for r in get_json(f"{B5}/data/rating-cldv-raw-salon-{d}.json"):
            if "927" in (r.get("salon_name") or ""):
                for t in re.split(r"[;,]", r.get("Category_FB_name") or r.get("FB_name") or ""):
                    t = t.strip()
                    if t:
                        tags[t] += 1
                if r.get("rating") in (1, 2, 3):
                    low_bills.append((r.get("date_rating"), r.get("rating"),
                                      (r.get("FB_detail") or "").strip()[:60],
                                      (r.get("Category_FB_name") or "").strip()[:50]))
    return dict(kh=rev["khach"], dt=rev["tong"], aov=(rev["tong"] / rev["khach"] if rev["khach"] else 0),
                kh_moi=rev["kh_moi"], r90=rev["kh_r90"], r90_180=rev["kh_r90_180"], r180=rev["kh_r180plus"],
                pp=pp_t, xl=xl_t, bk=a(seen[2]), hu=a(seen[9]),
                fb_tot=sum(stars.values()), low=stars["1_sao"] + stars["2_sao"] + stars["3_sao"],
                low_bills=low_bills, khen=[t for t, _ in tags.most_common(3)])


def arrow(now, prev):
    if prev == 0:
        return ""
    d = (now - prev) / prev * 100
    return f" {'▲' if d > 0 else ('▼' if d < 0 else '=')} {d:+.1f}%"


def delta(now, prev):
    return f"{'▲' if now > prev else ('▼' if now < prev else '=')} ({now - prev:+.0f})"


def pct(a, b):
    return f"{round(100*a/b)}%" if b else "-"


def main():
    run = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    this_days, prev_days, lm, pm = week_bounds(run)
    n = compute(this_days)
    p = compute(prev_days)
    lmt = f"{lm.strftime('%d/%m')}–{(lm+timedelta(days=6)).strftime('%d/%m')}"
    pmt = f"{pm.strftime('%d/%m')}–{(pm+timedelta(days=6)).strftime('%d/%m')}"

    L = [f"BÁO CÁO TUẦN – 927 HG ({lmt} vs {pmt})", ""]
    if n["kh"] == 0:
        L.append("⚠️ Chưa lấy được số Lượt khách/DT từ báo cáo Sale v7 0019 (data tuần này có thể chưa cập nhật).")
    L.append(f"Lượt khách: {n['kh']:.0f} vs {p['kh']:.0f}{arrow(n['kh'], p['kh'])}")
    L.append(f"  Khách mới: {n['kh_moi']:.0f} vs {p['kh_moi']:.0f} {delta(n['kh_moi'], p['kh_moi'])}")
    L.append(f"  R90 (<90 ngày): {n['r90']:.0f} vs {p['r90']:.0f} {delta(n['r90'], p['r90'])}")
    L.append(f"  R90-180: {n['r90_180']:.0f} vs {p['r90_180']:.0f} {delta(n['r90_180'], p['r90_180'])}")
    L.append(f"  R180+ (lâu chưa quay lại): {n['r180']:.0f} vs {p['r180']:.0f} {delta(n['r180'], p['r180'])}")
    L.append(f"AOV: {n['aov']:,.0f}đ vs {p['aov']:,.0f}đ{arrow(n['aov'], p['aov'])} · DT: {n['dt']/1e6:.1f}tr vs {p['dt']/1e6:.1f}tr{arrow(n['dt'], p['dt'])}")
    L.append(f"CSKH (gọi Booking): {pct(n['bk'][1], n['bk'][0])} vs {pct(p['bk'][1], p['bk'][0])} · menu Hủy: {pct(n['hu'][1], n['hu'][0])} vs {pct(p['hu'][1], p['hu'][0])}")
    L.append(f"Hotline: đã gọi {n['xl']}/{n['pp']} ({pct(n['xl'], n['pp'])}) vs {p['xl']}/{p['pp']} ({pct(p['xl'], p['pp'])})")
    fb = f"FB: {n['fb_tot']} đánh giá · bill 1-2-3 sao: {n['low']} vs {p['low']}{' ▲' if n['low'] > p['low'] else (' ▼' if n['low'] < p['low'] else '')}"
    if n["khen"]:
        fb += f" · khen: {', '.join(x.split(' - ')[-1] for x in n['khen'])}"
    L.append(fb)
    for db in n["low_bills"]:
        L.append(f"   • {db[0]} ⭐{db[1]}: {db[2] or db[3] or ''}")
    L.append("GSC (giám sát cam): ……… [cần token / điền tay]")
    L.append("MKT Google Map: ………   |   MKT Clip: ………   [điền tay]")
    sty = stylist_week(this_days)
    if sty and sty["n"]:
        pm_note = "" if len(sty["cov"]) == 7 else f" [data phủ {len(sty['cov'])}/7 ngày: {sty['cov'][0]}→{sty['cov'][-1]}]"
        L.append(f"Stylist đặt lịch KH: {sty['h']} lượt hẹn / {sty['n']} nhận khách ({pct(sty['h'], sty['n'])}) · {sty['sty']} stylist có hẹn{pm_note}")
    else:
        L.append("Stylist đặt lịch KH: ……… [điền tay – báo cáo maya-cao/hen-lich-stylist]")
    L.append("Nhân sự gọi tên khách: ……… [điền tay]")
    L.append("Truyền thông 2 định hướng mới: ……… [điền tay]")
    L.append("")
    L.append("VÌ SAO:")
    cu_n = n["r90"] + n["r90_180"] + n["r180"]
    cu_p = p["r90"] + p["r90_180"] + p["r180"]
    if n["kh"] > p["kh"] and n["kh_moi"] < p["kh_moi"]:
        L.append(f"🔸 Khách tăng ({n['kh']-p['kh']:+.0f}) nhưng nhờ KHÁCH CŨ quay lại ({cu_n-cu_p:+.0f}); KHÁCH MỚI giảm ({n['kh_moi']-p['kh_moi']:+.0f}) → đẩy MKT hút khách mới.")
    elif n["kh"] < p["kh"]:
        drop = "khách mới" if (p["kh_moi"] - n["kh_moi"]) >= (cu_p - cu_n) else "khách cũ quay lại"
        L.append(f"🔸 Khách giảm ({n['kh']-p['kh']:+.0f}) — giảm chủ yếu ở {drop}.")
    if n["aov"] < p["aov"] and n["kh"] > p["kh"]:
        L.append("🔸 AOV giảm dù khách đông hơn → khách chi ít hơn / dịch vụ rẻ hơn → đẩy upsell/combo.")
    elif n["aov"] > p["aov"]:
        L.append("🔸 AOV tăng → khách chi nhiều hơn / thêm dịch vụ.")
    if n["bk"][0] and p["bk"][0] and (n["bk"][1]/max(n["bk"][0],1)) < (p["bk"][1]/max(p["bk"][0],1)):
        L.append("🔸 CSKH gọi Booking giảm → nhắc nhân sự giữ nhịp gọi nhắc lịch.")
    if n["low"] > p["low"]:
        L.append("🔸 FB xấu hơn: xuất hiện thêm bill 1-2-3 sao → kiểm lại khâu bị phàn nàn.")
    print("\n".join(L))


if __name__ == "__main__":
    main()
