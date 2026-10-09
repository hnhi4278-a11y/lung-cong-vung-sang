import csv
rows=list(csv.reader(open('/tmp/bd.csv',encoding='utf-8')))
def rk(r):
    try: return int(r[0])
    except: return 99
sty=[(rk(r),i,r[1]) for i,r in enumerate(rows[5:14],6)]
ski=[(rk(r),i,r[1]) for i,r in enumerate(rows[24:35],25) if r[1].strip()]
short={'Trí':'Võ Văn Trí','H.V.Kha':'Huỳnh Văn Kha','Trọng':'Võ Quốc Trọng','N.H.Kha':'Nguyễn Hoàng Kha','Tỷ':'Trương Phúc Tỷ',
 'Linh':'Đỗ Thị Linh','Phương':'Ngô Thuỳ Phương','Trâm':'Nguyễn Ngọc Bích Trâm','Ánh':'Ngô Thị Ngọc Ánh','Thanh Thanh':'Phó Nguyễn Thanh Thanh','Ngọc Anh':'Võ Thành Ngọc Anh'}
off={'T2 5/10':(['Trí','H.V.Kha'],['Linh','Phương']),'T3 6/10':(['Trọng','N.H.Kha'],['Trâm']),
 'T4 7/10':(['Tỷ','N.H.Kha'],['Ánh','Phương','Thanh Thanh']),'T5 8/10':([],['Ngọc Anh']),
 'T6 9/10':([],[]),'T7 10/10':([],[]),'CN 11/10':([],[])}
def plan(lst,offn,duyen=False,uyen=False):
    o={short[x] for x in offn}
    av=[x for x in lst if x[2] not in o and not (duyen and 'Duyên' in x[2])]
    if uyen:
        f=[x for x in av if 'UYÊN' in x[2].upper()]; rest=sorted([x for x in av if x not in f],key=lambda x:(x[0],x[1])); av=f+rest
    else: av=sorted(av,key=lambda x:(x[0],x[1]))
    n=[x[2] for x in av]
    return dict(ca1=n[0:2],ca2=n[2:4],ca21=n[4:8],ca3=n[8:9],over=n[9:])
for d,(so,ko) in off.items():
    s=plan(sty,so,duyen=True); k=plan(ski,ko,uyen=True)
    print(f'== {d}  OFF stylist={so} skinner={ko}')
    for c in ['ca1','ca2','ca21','ca3']:
        st=s[c] if c!='ca3' else ['Trần Nhất Duyên']
        print(f'  {c:5} S: {", ".join(st)}   |   K: {", ".join(k[c])}')
    if k['over']: print('  overflow K:',k['over'])
