import subprocess, tempfile, os
from PIL import Image


def ocr_band(img_path, top, bot, psm=6, scale=2, pad=4):
    im = Image.open(img_path).convert("L")
    w, h = im.size
    box = (0, max(0, top - pad), w, min(h, bot + pad))
    crop = im.crop(box)
    if scale != 1:
        crop = crop.resize(
            (crop.width * scale, crop.height * scale), Image.LANCZOS
        )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        crop.save(f.name)
        tmp = f.name
    try:
        r = subprocess.run(
            [
                "tesseract",
                tmp,
                "stdout",
                "-l",
                "deu",
                "--psm",
                str(psm),
                "-c",
                "preserve_interword_spaces=1",
            ],
            capture_output=True,
            text=True,
        )
        return r.stdout.strip()
    finally:
        os.unlink(tmp)
