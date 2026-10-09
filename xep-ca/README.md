# 927HG - Xep ca (Hau Giang)

Quy trinh moi tuan: off list -> Bang diem (ns927.py) -> rank tu tinh (cot A, RANK()) -> doc rank xep lich.

## Sheet
- ID: 1-F12RqlqV6YAT6mIws61K5OtjvEHR1TEMZ0SkNY1DFs (tab "Lich lam viec" gid=0, "Bang diem" gid=1117803095)
- Off-table: D:J rows 3-21
- Band 1 (T2/T3/T4): rows 1-15, cols Q/X/AE. Band 2 (T5/T6/T7/CN): rows 20-34, cols Q/X/AE/AL
- Moi block 6 cot: doi | ca | rankS | tenS | rankK | tenK

## Thuat toan (da xac nhan voi chu salon)
- Rank doc tu cot A tab Bang diem, so nho = tot. Stylist va skinner sort rieng.
- Stylist: bo Duyen (luon ca3, row +8, cot stylist), con lai rank asc, tiebreak theo dong sheet.
- Skinner: Uyen forced vi tri dau, con lai rank asc, tiebreak theo dong sheet.
- Fill: slot 1-2 -> ca1, 3-4 -> ca2, 5-8 -> ca2.1, #9 (skinner) -> ca3 (row +8), #10 -> overflow (row +9, chi ghi rank+ten, khong co doi/ca).
- Nguoi OFF bi loai khoi danh sach, KHONG bu nguoi. Cho trong de blank.
- n_off > 2 -> 3 dong OFF, bo Ho tro.
- Layout row trong block: ca1 +0..+1, ca2 +2..+3, ca2.1 +4..+7, ca3 +8, overflow +9, sau do OFF / Ho tro.
- Ten ca: ca 1 (8h30-19h40), ca 2 (8h45-20h20), ca 2.1 (9h45-20h30), ca 3 (11h45-21h). Doi 1/2/3/4.
- Bridge POST tra "ok" plain text, khong phai JSON.

## Ghi chu
- Khanh va N.H.Kha di lam nhung nang suat = 0 (dung, khong phai loi ten).
- xepca_dry.py: chay thu, chi in ket qua, KHONG ghi sheet. Da doi chieu T6 (khong ai off) khop 100% voi lich da xep.
- Buoc ghi vao cac cot Q/X/AE/AL CHUA viet. Ky toi: user gui lich off -> dry-run -> user xem -> moi ghi that.

## xepca.py (thay xepca_dry.py)
`BRIDGE_TOKEN=... python3 xep-ca/xepca.py <thu-2 YYYY-MM-DD> off.json [--write]`
off.json: {"T2":{"s":["ten stylist off"],"k":["ten skinner off"]},...}. Khong co --write = chi in.
Da doi chieu T6/T7/CN (khong ai off): vi tri nguoi khop 100%; chi khac chu nhan ca (sheet cu go sai "8h45", thieu nhan ca 3).
Token bridge KHONG luu trong repo (lay tu prompt routine / bien moi truong).
