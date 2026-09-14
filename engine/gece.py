# -*- coding: utf-8 -*-
"""
GECE TOPLU DONUSTURUCU
4 su-aritma PDF'ini marker-pdf ile OCR'lar, bolumlerine ayirir ve
C:\\kitap\\kutuphane\\<kitap>\\ altina md + 00-index.md kaydeder.

- Her kitap: 200 sayfalik bloklar halinde OCR (durum.json -> kaldigi yerden devam)
- Icindekiler agaci varsa gercek bolumlere ayirir; yoksa ~40 basili sayfalik
  parcalara boler (kisim-NN)
- Sayfa offset'i (basili = PDF - offset) otomatik bulunur
- Tek bir kitap patlarsa digerlerine gecer

Calistir (Windows, venv acik):
    python C:\\kitap\\araclar\\gece.py
"""
import json, re, shutil, subprocess, sys, time, unicodedata, collections
from pathlib import Path

KUTUPHANE = Path(r"C:\kitap\kutuphane")
OUTKOK    = Path(r"C:\kitap\out")
KITAPDF   = Path(r"C:\kitap\Kitapdf")
LOG       = Path(r"C:\kitap\gece-log.txt")
BLOK      = 200
FLAGS     = ["--force_ocr", "--paginate_output"]
CHUNK_SAYFA = 40   # outline yoksa parca basina basili sayfa

# (pdf dosya adi, cikti slug, blockquote metni)
KITAPLAR = [
    ("David Hendricks-wastewater.pdf", "hendricks",
     "David W. Hendricks, *Fundamentals of Water Treatment Unit Processes: Physical, Chemical, and Biological*", 44),
    ("Dissolved Air Flotation_ Equipment, Best Practice and Roumen Kaltchev.pdf", "daf-kaltchev",
     "Roumen Kaltchev, *Dissolved Air Flotation: Equipment, Best Practice*", 21),
    ("Dissolved air flotation for water clarification- Edzwald, James K; Haarhoff, Johannes.pdf", "daf-edzwald-haarhoff",
     "Edzwald & Haarhoff, *Dissolved Air Flotation for Water Clarification*", None),
    ("Johannes Haarhoff.pdf", "haarhoff",
     "Johannes Haarhoff, *Dissolved Air Flotation*", None),
]

SAYFA_RE  = re.compile(r'^\s*\{(\d+)\}-{3,}\s*$')
KISIM_RE  = re.compile(r'^#{1,6}\s*\*{0,2}\s*(\d{1,2})[.\-\u2013](\d{1,3})((?:[.\-\u2013]\d{1,3})*)\s*(.*)$')
RESIM_RE  = re.compile(r'!\[\]\(.*?(_page_\d+_[A-Za-z]+_\d+\.(?:jpeg|jpg|png))\)')
TABSEK_RE = re.compile(r'^[#*\s]*(Table|Tablo|Figure|Fig\.?)\s*(\d{1,2}[.\-\u2013]\d{1,3})[\s.:*]*(.{0,90})', re.IGNORECASE)

CH_RE  = re.compile(r'^\s*(?:Chapter|Bolum|Bölüm)\s+\d+', re.IGNORECASE)
CH_RE2 = re.compile(r'^\s*(\d{1,2})\s+[A-Za-z]')      # "1 Fundamentals"
APP_RE = re.compile(r'^\s*(?:Appendix|Ek)\b', re.IGNORECASE)
PART_RE= re.compile(r'^\s*(?:Part|Kisim|Kısım)\b', re.IGNORECASE)
IDX_RE = re.compile(r'^\s*Index\s*$', re.IGNORECASE)

def log(msg):
    line=f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG,"a",encoding="utf-8") as f: f.write(line+"\n")

def slug(m, uz=60):
    m=unicodedata.normalize("NFKD",m).encode("ascii","ignore").decode()
    m=re.sub(r"[^a-zA-Z0-9]+","-",m).strip("-").lower()
    return re.sub(r"-{2,}","-",m)[:uz] or "x"

# ---------- OCR ----------
def toplam_sayfa(pdf):
    import pypdfium2 as pdfium
    d=pdfium.PdfDocument(str(pdf)); n=len(d); d.close(); return n

def ocr(pdf, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    durum_f=outdir/"durum.json"
    durum=json.loads(durum_f.read_text()) if durum_f.exists() else {}
    n=toplam_sayfa(pdf)
    bloklar=[]; i=0
    while i<n: bloklar.append((i,min(i+BLOK-1,n-1))); i+=BLOK
    log(f"  {n} sayfa, {len(bloklar)} blok")
    for idx,(a,b) in enumerate(bloklar,1):
        k=f"{idx:03d}"
        if durum.get(k)=="ok":
            log(f"  blok {k} atlandi (bitmis)"); continue
        hedef=outdir/f"blok_{k}"
        t0=time.time()
        log(f"  blok {k} basliyor  s.{a}-{b}")
        runner=("import sys;from marker.scripts.convert_single import convert_single_cli;"
                "sys.argv=['marker_single']+sys.argv[1:];convert_single_cli()")
        komut=[sys.executable,"-c",runner,str(pdf),"--output_dir",str(hedef),"--page_range",f"{a}-{b}"]+FLAGS
        r=subprocess.run(komut)
        if r.returncode==0 and list(hedef.rglob("*.md")):
            durum[k]="ok"; log(f"  blok {k} TAMAM ({time.time()-t0:.0f}sn)")
        else:
            durum[k]="hata"; log(f"  blok {k} HATA rc={r.returncode}")
        durum_f.write_text(json.dumps(durum,indent=2))
    return all(v=="ok" for v in durum.values()) and len(durum)==len(bloklar)

# ---------- offset ----------
def offset_bul(pdf):
    import pypdf
    r=pypdf.PdfReader(str(pdf)); n=len(r.pages)
    c=collections.Counter()
    for idx in range(min(20,n), min(n,250)):
        t=r.pages[idx].extract_text() or ""
        ls=[x.strip() for x in t.split("\n") if x.strip()]
        for l in ls[:2]+ls[-2:]:
            if re.fullmatch(r'\d{1,4}',l):
                v=int(l)
                if 0<v<idx+5: c[idx-v]+=1
    if c:
        off,cnt=c.most_common(1)[0]
        if cnt>=6: return off
    return 0

# ---------- outline birimleri ----------
def outline_birimler(pdf):
    import pypdf
    r=pypdf.PdfReader(str(pdf))
    ol=r.outline if r.outline else []
    leaves=[]
    def walk(o):
        for it in o:
            if isinstance(it,list): walk(it)
            else:
                try: pg=r.get_destination_page_number(it)
                except: pg=None
                if pg is not None: leaves.append((pg,(it.title or "").strip()))
    walk(ol)
    leaves.sort()
    chapters=[]; apps=[]; parts=[]; idxpg=None
    for pg,t in leaves:
        if IDX_RE.match(t): idxpg=idxpg or pg
        elif APP_RE.match(t): apps.append((pg,t))
        elif PART_RE.match(t): parts.append((pg,t))
        elif CH_RE.match(t) or CH_RE2.match(t): chapters.append((pg,t))
    # tekille + sirala
    def uniq(x):
        s={}; 
        for pg,t in x: s.setdefault(pg,t)
        return sorted(s.items())
    chapters=uniq(chapters); apps=uniq(apps); parts=uniq(parts)
    return chapters, apps, parts, idxpg, len(r.pages)

def temiz_baslik(t):
    t=re.sub(r'^\s*(Chapter|Bolum|Bölüm)\s+[\d.]+[.\s]*','',t,flags=re.I)
    return t.strip(" .:-")

# ---------- yardimci ----------
def bloklari_oku(outdir):
    sat=[]
    for d in sorted(outdir.glob("blok_*")):
        mds=sorted(d.rglob("*.md"))
        if mds: sat.extend(mds[0].read_text(encoding="utf-8",errors="replace").splitlines())
    return sat

def resim_haritasi(outdir):
    h={}
    for u in ("*.jpeg","*.jpg","*.png"):
        for p in outdir.rglob(u): h.setdefault(p.name,p)
    return h

def birim_yaz(hedef, dosya, klasor, baslik, blockq, ekbilgi, ilk, son, off, govde_satirlar, resimler):
    govde_l=[]; sayfa_sozluk={}
    for i,s in govde_satirlar:
        m=SAYFA_RE.match(s)
        if m:
            nn=int(m.group(1)); sayfa_sozluk[i]=nn
            govde_l.append(f"\n<!-- PDF {nn} | basili s.{nn-off} -->\n")
        else:
            govde_l.append(s)
    govde="\n".join(govde_l).strip("\n")
    sekk=hedef/"sekiller"/klasor
    adlar=set(RESIM_RE.findall(govde))
    if adlar: sekk.mkdir(parents=True,exist_ok=True)
    kopya=0
    for nm in adlar:
        src=resimler.get(nm)
        if src and src.exists():
            dst=sekk/nm
            if not dst.exists(): shutil.copy2(src,dst)
            kopya+=1
    govde=RESIM_RE.sub(lambda m:f"![](sekiller/{klasor}/{m.group(1)})",govde)
    bas=f"# {baslik}\n\n> {blockq}\n"
    if ekbilgi: bas+=f"> {ekbilgi}\n"
    bas+=f"> Basili sayfa {ilk-off}-{son-off} (PDF {ilk}-{son})\n\n---\n\n"
    (hedef/dosya).write_text(bas+govde+"\n",encoding="utf-8")
    return kopya

# ---------- bolme ----------
def bol(pdf, outdir, hedef, blockq, off_override=None):
    hedef.mkdir(parents=True,exist_ok=True)
    sat=bloklari_oku(outdir)
    if not sat: log("  UYARI: OCR ciktisi yok, bolme atlandi"); return
    resimler=resim_haritasi(outdir)
    off=off_override if off_override is not None else offset_bul(pdf)
    log(f"  offset={off}, {len(sat)} satir, {len(resimler)} resim")
    # sayfa isaretleri
    sayfa_isaret=[(i,int(m.group(1))) for i,s in enumerate(sat) if (m:=SAYFA_RE.match(s))]
    if not sayfa_isaret: log("  HATA: sayfa isareti yok"); return
    def satir_of(pg):
        best=None
        for ln,p in sayfa_isaret:
            if p==pg: return ln
            if p>pg and best is None: best=ln
        return best if best is not None else 0

    chapters,apps,parts,idxpg,npdf=outline_birimler(pdf)
    birimler=[]  # (satir, tur, ad, dosya, klasor)
    if len(chapters)>=3:
        log(f"  outline: {len(chapters)} bolum, {len(apps)} ek")
        # front matter
        ilkbol=chapters[0][0]
        birimler.append((0,"on","On kisim (kapak, icindekiler, onsoz)","00-on-kisim.md","on-kisim"))
        for no,(pg,t) in enumerate(chapters,1):
            bas=pg
            for ppg,pt in parts:            # part divider'i sonraki bolume kat
                if bas-4<=ppg<bas: bas=ppg
            ad=temiz_baslik(t)
            birimler.append((satir_of(bas),"bolum",f"{no} {ad}",f"bolum-{no:02d}-{slug(ad)}.md",f"bolum-{no:02d}"))
        for ei,(pg,t) in enumerate(apps,1):
            ad=temiz_baslik(t) or f"Ek {ei}"
            birimler.append((satir_of(pg),"ek",ad,f"ek-{ei:02d}-{slug(ad)}.md",f"ek-{ei:02d}"))
        if idxpg:
            birimler.append((satir_of(idxpg),"index","Index","99-kitap-indeksi.md","index"))
    else:
        # outline yok -> ~CHUNK_SAYFA basili sayfalik parcalar
        log(f"  outline yok, {CHUNK_SAYFA} sayfalik parcalara bolunuyor")
        sayfalar=sorted(set(p for _,p in sayfa_isaret))
        gruplar=[sayfalar[i:i+CHUNK_SAYFA] for i in range(0,len(sayfalar),CHUNK_SAYFA)]
        for gi,g in enumerate(gruplar,1):
            birimler.append((satir_of(g[0]),"kisim",f"Kisim {gi} (s.{g[0]-off}-{g[-1]-off})",
                             f"kisim-{gi:02d}.md",f"kisim-{gi:02d}"))

    # satir araliklarina cevir
    birimler.sort()
    sinir=[b[0] for b in birimler]+[len(sat)]
    yazilan=[]
    for k,(a,tur,ad,dosya,klasor) in enumerate(birimler):
        z=sinir[k+1]
        pgs=[p for ln,p in sayfa_isaret if a<=ln<z]
        if not pgs: continue
        ilk,son=pgs[0],pgs[-1]
        # alt kisimlar
        kisimlar=[]; tabsek=[]; sf=ilk
        for i in range(a,z):
            m2=SAYFA_RE.match(sat[i])
            if m2: sf=int(m2.group(1)); continue
            km=KISIM_RE.match(sat[i])
            if km:
                kod=f"{km.group(1)}.{km.group(2)}{km.group(3)}"
                kisimlar.append((kod,km.group(4).strip(' *#:-'),sf))
            ts=TABSEK_RE.match(sat[i])
            if ts:
                tur2=("Tablo" if ts.group(1).lower().startswith(("table","tablo")) else "Sekil")
                tabsek.append((tur2,ts.group(2),ts.group(3).strip(' *#:-'),sf))
        ekbilgi=f"{len(kisimlar)} alt kisim" if kisimlar else None
        sekil=birim_yaz(hedef,dosya,klasor,ad,blockq,ekbilgi,ilk,son,off,
                        [(i,sat[i]) for i in range(a,z)],resimler)
        yazilan.append(dict(dosya=dosya,ad=ad,ilk=ilk,son=son,off=off,
                            kisimlar=kisimlar,tabsek=tabsek,sekil=sekil,tur=tur))
        log(f"    {dosya[:44]:44s} s.{ilk-off:>4}-{son-off:<5}{len(kisimlar):>3} kisim {sekil:>4} sekil")

    (hedef/"birlesik.md").write_text("\n".join(sat),encoding="utf-8")
    # index
    ix=[f"# Icerik Haritasi","",blockq.replace('*',''),"",f"Basili sayfa = PDF sayfa - {off}","",
        "## Birimler","","| Dosya | Birim | Basili sayfa | Kisim | Sekil |","|---|---|---|---|---|"]
    for p in yazilan:
        ix.append(f"| `{p['dosya']}` | {p['ad']} | {p['ilk']-off}-{p['son']-off} | {len(p['kisimlar'])} | {p['sekil']} |")
    ix+=["","## Alt kisimlar",""]
    for p in yazilan:
        if not p["kisimlar"]: continue
        ix+=[f"### {p['ad']}",f"`{p['dosya']}`",""]
        for kod,b,sf in p["kisimlar"]:
            ix.append(f"- **{kod}** {b}  (s.{sf-off})")
        ix.append("")
    ix+=["## Tablo ve sekil listesi",""]
    for p in yazilan:
        if not p.get("tabsek"): continue
        ix+=[f"### {p['ad']}","","| Tur | No | Aciklama | Basili sayfa |","|---|---|---|---|"]
        gor=set()
        for tur2,no2,ad2,sf in p["tabsek"]:
            if (tur2,no2) in gor: continue
            gor.add((tur2,no2))
            ix.append(f"| {tur2} | {no2} | {ad2.replace('|','/')} | {sf-off} |")
        ix.append("")
    (hedef/"00-index.md").write_text("\n".join(ix),encoding="utf-8")
    log(f"  BITTI -> {hedef} ({len(yazilan)} dosya)")

def main():
    log("="*60); log("GECE KOSUSU BASLADI")
    for dosya,slug_ad,blockq,off_ov in KITAPLAR:
        pdf=KITAPDF/dosya
        log("-"*60); log(f"KITAP: {slug_ad}  ({dosya})")
        if not pdf.exists(): log(f"  ATLA: PDF yok: {pdf}"); continue
        try:
            tam=ocr(pdf, OUTKOK/slug_ad)
            if not tam: log("  UYARI: OCR bloklari eksik, yine de bolunecek")
            bol(pdf, OUTKOK/slug_ad, KUTUPHANE/slug_ad, blockq, off_ov)
        except Exception as e:
            log(f"  KITAP HATASI ({slug_ad}): {e}")
    log("="*60); log("GECE KOSUSU BITTI")

if __name__=="__main__":
    main()