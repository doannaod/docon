"""Kitap emojisinden çok boyutlu app/assets/icon.ico üretir (Segoe UI Emoji fontundan).

Kullanım: .venv\\Scripts\\python scripts\\make_icon.py
Yeniden üretmek gerekirse (emoji değişirse, boyut eklenirse) burayı çalıştır.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

EMOJI = "\U0001F4D6"  # 📖 open book
SRC_SIZE = 160  # font'un rahat çizdiği büyük boy; sonra küçültülür
OUT = Path(__file__).resolve().parent.parent / "app" / "assets" / "icon.ico"
SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
FONT_PATH = r"C:\Windows\Fonts\seguiemj.ttf"


def main() -> None:
    font = ImageFont.truetype(FONT_PATH, SRC_SIZE)
    canvas = Image.new("RGBA", (SRC_SIZE + 40, SRC_SIZE + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    bbox = d.textbbox((0, 0), EMOJI, font=font, embedded_color=True)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pos = ((canvas.width - w) // 2 - bbox[0], (canvas.height - h) // 2 - bbox[1])
    d.text(pos, EMOJI, font=font, embedded_color=True)

    bbox2 = canvas.getbbox()
    cropped = canvas.crop(bbox2)
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    square.save(OUT, sizes=[(s, s) for s in SIZES])
    print("yazildi:", OUT, square.size)


if __name__ == "__main__":
    main()
