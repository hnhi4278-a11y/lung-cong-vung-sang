"""Xep ca 927HG. Mac dinh DRY-RUN (khong ghi). Them --write de ghi that.
Doc: Bang diem (rank cot A) + lich off (JSON/CLI). Ghi vao tab 'Lich lam viec'."""
import csv, io, json, os, sys, unicodedata, urllib.request
from datetime import date, timedelta
N=lambda x:unicodedata.normalize('NFC',str(x).strip())
SSID='1-F12RqlqV6YAT6mIws61K5OtjvEHR1TEMZ0SkNY1DFs'
EXP=f'https://docs.google.com/spreadsheets/d/{SSID}/export?format=csv&gid='
CAS=[('đội 1','ca 1 (8h30-19h40)'),('đội 2','ca 2 (8h45-20h20)'),('đội 3','ca 2.1 (9:45-20h30)'),('đội 4','ca 3 (11:45-21h)')]
def col(n):
    s='';n+=1
    while n:n,r=divmod(n-1,26);s=chr(65+r)+s
    return s
def get(gid): return list(csv.reader(io.StringIO(urllib.request.urlopen(EXP+str(gid),timeout=30).read().decode())))
def rank_lists(bd):
    def rk(r):
        try:return int(r[0])
        except:return 99
    sty=[(rk(r),i,N(r[1])) for i,r in enumerate(bd[5:14],6) if r[1].strip()]
    ski=[(rk(r),i,N(r[1])) for i,r in enumerate(bd[24:36],25) if r[1].strip() and r[1].strip()!='Tên skinner']
    return sty,ski
def plan(lst,off,duyen=False,uyen=False):
    av=[x for x in lst if x[2] not in off and not(duyen and 'Duyên' in x[2])]
    if uyen:
        f=[x for x in av if 'UYÊN' in x[2].upper()]
        av=f+sorted([x for x in av if x not in f],key=lambda x:(x[0],x[1]))
    else: av=sorted(av,key=lambda x:(x[0],x[1]))
    return av
def day_cells(sty,ski,off_s,off_k):
    """tra ve list 14 dong (offset 0..13 tu data row dau), moi dong 6 gia tri."""
    S=plan(sty,off_s,duyen=True); K=plan(ski,off_k,uyen=True)
    duyen=[x for x in sty if 'Duyên' in x[2]]
    rows=[['']*6 for _ in range(14)]
    for k,(d,c) in enumerate(CAS):
        for r in ([0,2,4,8][k],): rows[r][0],rows[r][1]=d,c
    for i,x in enumerate(S[:8]): rows[i][2:4]=[x[0],x[2]]
    if duyen: rows[8][2:4]=[duyen[0][0],duyen[0][2]]
    for i,x in enumerate(K[:9]): rows[i][4:6]=[x[0],x[2]]
    for x in K[9:10]: rows[9][4:6]=[x[0],x[2]]
    offs_s=sorted([x for x in sty if x[2] in off_s]); offs_k=sorted([x for x in ski if x[2] in off_k])
    n=max(len(offs_s),len(offs_k),2); n=3 if max(len(offs_s),len(offs_k))>2 else 2
    for i in range(n):
        r=10+i; rows[r][0]=rows[r][1]='OFF'
        if i<len(offs_s): rows[r][2:4]=[offs_s[i][0],offs_s[i][2]]
        if i<len(offs_k): rows[r][4:6]=[offs_k[i][0],offs_k[i][2]]
    if n==2: rows[12][0]='Hỗ trợ'
    return rows

BRIDGE='https://script.google.com/macros/s/AKfycbz35LEGjHI01V1p8puJYWFepvOvTdD-__TwUVlLgy1QYryHt16WHFceOnq1UmenPs61/exec'
DAYS=[('T2',1,16),('T3',1,23),('T4',1,30),('T5',20,16),('T6',20,23),('T7',20,30),('CN',20,37)]
THU={'T2':'THỨ 2','T3':'THỨ 3','T4':'THỨ 4','T5':'THỨ 5','T6':'THỨ 6','T7':'THỨ 7','CN':'CHỦ NHẬT'}
def post(tab,rng,vals):
    d=json.dumps({'token':os.environ['BRIDGE_TOKEN'],'id':SSID,'sheet':tab,'range':rng,'values':vals}).encode()
    r=urllib.request.Request(BRIDGE,data=d,headers={'Content-Type':'application/json'},method='POST')
    import time
    for i in range(8):
        try: return urllib.request.urlopen(r,timeout=60).read().decode()[:30]
        except Exception as e: err=str(e); time.sleep(2*(i+1))
    raise RuntimeError('bridge loi: '+err)
def run(monday,off,write=False):
    """monday: date; off: {'T2':{'s':[ten day du],'k':[...]},...}"""
    bd=get(1117803095); sty,ski=rank_lists(bd)
    for i,(d,base,c0) in enumerate(DAYS):
        o=off.get(d,{}); rows=day_cells(sty,ski,{N(x) for x in o.get('s',[])},{N(x) for x in o.get('k',[])})
        dt=monday+timedelta(i); first=base+2
        rng=f'{col(c0)}{first}:{col(c0+5)}{first+13}'
        print(d,dt,rng)
        for r in rows:
            if any(r): print('   ',r)
        if write:
            print('  ghi:',post('Lịch làm việc',rng,rows))
            print('  ngay:',post('Lịch làm việc',f'{col(c0+3)}{base}',[[f'{dt.day}/{dt.month}/{dt.year}']]),
                  post('Lịch làm việc',f'{col(c0+3)}{base+1}',[[f'LỊCH {THU[d]}' if d!='CN' else 'LỊCH LÀM VIỆC CHỦ NHẬT']]))
if __name__=='__main__':
    # python3 xepca.py 2026-10-12 off.json [--write]
    run(date.fromisoformat(sys.argv[1]),json.load(open(sys.argv[2])),'--write' in sys.argv)
