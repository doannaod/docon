# -*- coding: utf-8 -*-
"""
Programın motor çalıştırıcısı. Programın kurduğu çalışma ortamındaki Python ile çalışır
(torch + marker + pypdf + pypdfium2 orada kuruludur).

gece.py'ye DOKUNMAZ: gece2.py'nin yaptığı gibi dosyayı yükler, FLAGS / LOG değerlerini
dışarıdan verir ve log satırlarını arayüzün okuyacağı JSON olaylarına çevirir.

Kullanım:
    python kosucu.py --pdf "kitap.pdf" --ham "<cikti>\\_ham-ocr" --hedef "<cikti>" \
                     --force-ocr 0|1 --baslik "Kitap adı" --log "<log dosyası>"

Çıktı (stdout, satır başına bir JSON):
    {"t":"bloklar","n":1048,"m":6}          toplam sayfa / blok
    {"t":"blok_basla","k":3,"a":400,"b":599}
    {"t":"blok_atla","k":1}                  önceki koşuda bitmiş
    {"t":"blok_tamam","k":3,"sn":734}
    {"t":"blok_hata","k":3,"rc":1}
    {"t":"asama","n":2}                      bölme başlıyor
    {"t":"outline","bolum":18,"ek":4}  |  {"t":"outline_yok","parca":40}
    {"t":"dosya","ad":"bolum-01-....md"}
    {"t":"log","msg":"..."}                  diğer her satır
    {"t":"sonuc","bolum":18,"ek":4,"sekil":214,"bayt":43210000,"tam":true}
    {"t":"hata","msg":"..."}
"""
import argparse
import json
import re
import subprocess
import sys
import time
import traceback
import types
from pathlib import Path

BURADA = Path(__file__).resolve().parent
GECE = BURADA / "gece.py"

R_BLOKLAR = re.compile(r"^\s*(\d+) sayfa, (\d+) blok")
R_BASLA = re.compile(r"^\s*blok (\d+) basliyor\s+s\.(\d+)-(\d+)")
R_ATLA = re.compile(r"^\s*blok (\d+) atlandi")
R_TAMAM = re.compile(r"^\s*blok (\d+) TAMAM \((\d+)sn\)")
R_HATA = re.compile(r"^\s*blok (\d+) HATA rc=(-?\d+)")
R_OUTLINE = re.compile(r"^\s*outline: (\d+) bolum, (\d+) ek")
R_OUTLINE_YOK = re.compile(r"^\s*outline yok, (\d+) sayfalik")
R_DOSYA = re.compile(r"^\s{4}(\S+\.md)\s")


def yay(**olay):
    sys.stdout.write(json.dumps(olay, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def gece_yukle(log_dosyasi: Path, force_ocr: bool, blok: int | None = None, parca: int | None = None,
               sayfa_limiti: int | None = None):
    src = GECE.read_text(encoding="utf-8").replace('if __name__=="__main__":\n    main()', "")
    g = types.ModuleType("gece")
    g.__dict__["__name__"] = "gece_motor"
    exec(compile(src, str(GECE), "exec"), g.__dict__)

    g.FLAGS = ["--paginate_output"] + (["--force_ocr"] if force_ocr else [])
    g.LOG = log_dosyasi
    if blok:
        g.BLOK = int(blok)
    if parca:
        g.CHUNK_SAYFA = int(parca)
    if sayfa_limiti:
        # Test koşusu: yalnız ilk N sayfa. gece.ocr() sayfa sayısını toplam_sayfa()'dan alır;
        # burada onu sınırlarız, motorun geri kalanı aynı kalır.
        gercek = g.toplam_sayfa
        g.toplam_sayfa = lambda pdf: min(gercek(pdf), int(sayfa_limiti))
        g.BLOK = int(sayfa_limiti)

    def log(msg):
        satir = f"[{time.strftime('%H:%M:%S')}] {msg}"
        with open(log_dosyasi, "a", encoding="utf-8") as f:
            f.write(satir + "\n")
        m = R_BLOKLAR.match(msg)
        if m:
            yay(t="bloklar", n=int(m.group(1)), m=int(m.group(2))); return
        m = R_BASLA.match(msg)
        if m:
            yay(t="blok_basla", k=int(m.group(1)), a=int(m.group(2)), b=int(m.group(3))); return
        m = R_ATLA.match(msg)
        if m:
            yay(t="blok_atla", k=int(m.group(1))); return
        m = R_TAMAM.match(msg)
        if m:
            yay(t="blok_tamam", k=int(m.group(1)), sn=int(m.group(2))); return
        m = R_HATA.match(msg)
        if m:
            yay(t="blok_hata", k=int(m.group(1)), rc=int(m.group(2))); return
        m = R_OUTLINE.match(msg)
        if m:
            yay(t="outline", bolum=int(m.group(1)), ek=int(m.group(2))); return
        m = R_OUTLINE_YOK.match(msg)
        if m:
            yay(t="outline_yok", parca=int(m.group(1))); return
        m = R_DOSYA.match(msg)
        if m:
            yay(t="dosya", ad=m.group(1)); return
        yay(t="log", msg=msg.strip())

    g.log = log

    # marker alt-sürecinin tqdm çıktısı stdout'u kirletmesin: log dosyasına yönlendir
    def run(komut, *a, **kw):
        with open(log_dosyasi, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[marker] {' '.join(str(x) for x in komut[3:])}\n")
            f.flush()
            return subprocess.run(komut, stdout=f, stderr=subprocess.STDOUT,
                                  creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    g.subprocess = types.SimpleNamespace(run=run)
    return g


def ozet(hedef: Path):
    bolum = len(list(hedef.glob("bolum-*.md"))) + len(list(hedef.glob("kisim-*.md")))
    ek = len(list(hedef.glob("ek-*.md")))
    sek = hedef / "sekiller"
    sekil = sum(1 for p in sek.rglob("*") if p.is_file()) if sek.exists() else 0
    bayt = 0
    for p in hedef.rglob("*"):
        if p.is_file() and "_ham-ocr" not in p.parts and "_test" not in p.parts:
            bayt += p.stat().st_size
    return bolum, ek, sekil, bayt


R_BOS_DENK = re.compile(r"^\$\$(\\begin\{array\}\{[a-z|]*\s*)?\$\$$")
R_RESIM = re.compile(r"!\[\]\(([^)]+)\)")
R_KISIM = re.compile(r"^#{1,6}\s*\*{0,2}\s*\d{1,2}[.\-–]\d{1,3}")


def test_ozeti(ham: Path, sayfa: int) -> dict:
    """Test koşusunun ham md çıktısından kullanıcıya gösterilecek sade özet."""
    mds = sorted(ham.rglob("*.md"))
    if not mds:
        return {"sayfa": sayfa, "md_var": False}
    metin = mds[0].read_text(encoding="utf-8", errors="replace")
    satirlar = metin.splitlines()
    resimler = R_RESIM.findall(metin)
    resim_var = sum(1 for r in resimler if (mds[0].parent / Path(r).name).exists() or any(mds[0].parent.rglob(Path(r).name)))
    karakter = len(re.sub(r"\s+", "", metin))
    return {
        "sayfa": sayfa, "md_var": True, "karakter": karakter,
        "karakter_sayfa": round(karakter / max(1, sayfa)),
        "denklem": metin.count("$$") // 2 + len(re.findall(r"(?<!\$)\$(?!\$)[^$\n]{2,}\$", metin)),
        "bos_denklem": sum(1 for s in satirlar if R_BOS_DENK.match(s.strip())),
        "tablo": sum(1 for s in satirlar if s.strip().startswith("|") and set(s.strip()) - set("|-: ")),
        "resim": len(resimler), "resim_var": resim_var,
        "baslik": sum(1 for s in satirlar if s.startswith("#")),
        "kisim_basligi": sum(1 for s in satirlar if R_KISIM.match(s)),
        "bozuk_karakter": metin.count("�") + len(re.findall(r"\(cid:\d+\)", metin)),
        "ornek": "\n".join(s for s in satirlar if s.strip())[:1200],
        "md": str(mds[0]),
    }


def simule(pdf: Path, ham: Path, hedef: Path, log_f: Path):
    """Geliştirme amaçlı benzetim (DOCON_SIMULE=1): marker yokken arayüz akışını denemek için.
    Sahte bloklar ve sahte çıktı dosyaları üretir; durum.json ile devam mantığı gerçek."""
    import os
    ham.mkdir(parents=True, exist_ok=True); hedef.mkdir(parents=True, exist_ok=True)
    durum_f = ham / "durum.json"
    durum = json.loads(durum_f.read_text()) if durum_f.exists() else {}
    n = 1048; m = (n + 199) // 200
    bekle = float(os.environ.get("DOCON_SIMULE_SN", "1.5"))
    yay(t="asama", n=1); yay(t="bloklar", n=n, m=m)
    for k in range(1, m + 1):
        key = f"{k:03d}"
        if durum.get(key) == "ok":
            yay(t="blok_atla", k=k); continue
        a, b = (k - 1) * 200, min(k * 200 - 1, n - 1)
        yay(t="blok_basla", k=k, a=a, b=b)
        time.sleep(bekle)
        durum[key] = "ok"; durum_f.write_text(json.dumps(durum, indent=2))
        yay(t="blok_tamam", k=k, sn=int(bekle))
    yay(t="asama", n=2); yay(t="outline", bolum=6, ek=1)
    (hedef / "sekiller" / "bolum-01").mkdir(parents=True, exist_ok=True)
    for i in range(1, 7):
        ad = f"bolum-{i:02d}-ornek-bolum.md"; (hedef / ad).write_text(f"# Bölüm {i}\n\nÖrnek metin.\n", encoding="utf-8")
        yay(t="dosya", ad=ad); time.sleep(0.2)
    (hedef / "ek-01-ornek.md").write_text("# Ek\n", encoding="utf-8")
    (hedef / "00-index.md").write_text("# Icerik Haritasi\n", encoding="utf-8")
    (hedef / "birlesik.md").write_text("# Kitap\n" * 200, encoding="utf-8")
    for j in range(3):
        (hedef / "sekiller" / "bolum-01" / f"_page_{j}_Figure_1.jpeg").write_bytes(b"\xff\xd8\xff" + bytes(64))
    bolum, ek, sekil, bayt = ozet(hedef)
    yay(t="sonuc", bolum=bolum, ek=ek, sekil=sekil, bayt=bayt, tam=True)
    return 0


def simule_test(n: int, ham: Path) -> int:
    import os
    ham.mkdir(parents=True, exist_ok=True)
    bekle = float(os.environ.get("DOCON_SIMULE_SN", "1.5"))
    yay(t="asama", n=1); yay(t="bloklar", n=n, m=1); yay(t="blok_basla", k=1, a=0, b=n - 1)
    time.sleep(bekle)
    d = ham / "blok_001"; d.mkdir(exist_ok=True)
    (d / "test.md").write_text("# Örnek Bölüm\n\n{1}------------------------------------------------\n\n"
                               "Bu bir örnek paragraf. $E = mc^2$\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
                               "![](_page_3_Figure_1.jpeg)\n" * 5, encoding="utf-8")
    (d / "_page_3_Figure_1.jpeg").write_bytes(b"\xff\xd8\xff" + bytes(32))
    yay(t="blok_tamam", k=1, sn=int(bekle))
    yay(t="test_sonuc", **test_ozeti(ham, n))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--ham", required=True)
    ap.add_argument("--hedef", required=True)
    ap.add_argument("--force-ocr", type=int, default=0)
    ap.add_argument("--baslik", default="")
    ap.add_argument("--log", required=True)
    ap.add_argument("--offset", type=int, default=None)
    ap.add_argument("--blok", type=int, default=None, help="blok sayfa sayısı (varsayılan gece.py: 200)")
    ap.add_argument("--parca", type=int, default=None, help="outline yokken parça sayfa sayısı (varsayılan 40)")
    ap.add_argument("--test", type=int, default=None, help="yalnız ilk N sayfayı çevir, bölme yapma, özet ver")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pdf, ham, hedef, log_f = Path(a.pdf), Path(a.ham), Path(a.hedef), Path(a.log)
    log_f.parent.mkdir(parents=True, exist_ok=True)
    baslik = a.baslik or f"*{pdf.stem}*"
    import os
    if os.environ.get("DOCON_SIMULE") == "1":
        if a.test:
            return simule_test(a.test, ham)
        return simule(pdf, ham, hedef, log_f)
    try:
        if a.test:
            g = gece_yukle(log_f, bool(a.force_ocr), sayfa_limiti=a.test)
            yay(t="asama", n=1)
            g.ocr(pdf, ham)                       # tek blok: sayfa 0..N-1
            yay(t="test_sonuc", **test_ozeti(ham, a.test))
            return 0
        g = gece_yukle(log_f, bool(a.force_ocr), a.blok, a.parca)
        yay(t="asama", n=1)
        tam = g.ocr(pdf, ham)
        if not tam:
            yay(t="log", msg="UYARI: OCR bloklarının bir kısmı eksik, yine de bölünecek")
        yay(t="asama", n=2)
        g.bol(pdf, ham, hedef, baslik, a.offset)
        bolum, ek, sekil, bayt = ozet(hedef)
        yay(t="sonuc", bolum=bolum, ek=ek, sekil=sekil, bayt=bayt, tam=bool(tam))
        return 0
    except Exception as e:
        with open(log_f, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        yay(t="hata", msg=f"{type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
