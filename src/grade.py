import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out, sheet_path = sys.argv[1], sys.argv[2], sys.argv[3]
N = 560
# kitty face roughly centered and at a similar scale in every frame
CROPS = {
    1:  ("1.webp",  (56, 56, 680, 680)),
    2:  ("2.webp",  (40, 330, 716, 1006)),
    3:  ("3.webp",  (300, 440, 1000, 1140)),
    4:  ("4.webp",  (360, 120, 1024, 784)),
    5:  ("5.webp",  (60, 60, 700, 700)),
    6:  ("6.webp",  (60, 0, 736, 676)),
    7:  ("7.webp",  (40, 230, 720, 910)),
    8:  ("8.webp",  (90, 200, 630, 740)),
    9:  ("9.webp",  (50, 50, 686, 686)),
    10: ("10.webp", (0, 40, 860, 900)),
    11: ("11.webp", (300, 320, 940, 960)),
    12: ("12.png",  (0, 210, 600, 810)),
    13: ("13.png",  (70, 20, 412, 362)),
    14: ("14.webp", (60, 60, 660, 660)),
}
INK, MID, CREAM = np.array([70, 42, 52]), np.array([222, 160, 170]), np.array([255, 245, 242])

STRENGTH = {4: (0.97, 0.16), 9: (0.68, 0.34)}

def grade(im, k):
    sat, mix = STRENGTH.get(k, (0.82, 0.3))
    a = np.asarray(im, dtype=np.float32) / 255.0
    # 1. pull every photo toward neutral white balance (partial gray world)
    avg = a.reshape(-1, 3).mean(0)
    a = np.clip(a * (avg.mean() / avg) ** 0.6, 0, 1)
    # 2. same overall exposure
    lum = a @ np.array([0.299, 0.587, 0.114])
    g = np.log(0.6) / np.log(max(lum.mean(), 1e-3))
    a = np.clip(a ** np.clip(g, 0.6, 1.6), 0, 1)
    # 3. a little less saturation
    lum = (a @ np.array([0.299, 0.587, 0.114]))[..., None]
    a = lum + (a - lum) * sat
    # 4. shared pink film tone: blend in a gradient map ink -> rose -> cream
    t = lum[..., 0]
    lo = np.clip(t / 0.55, 0, 1)[..., None]
    hi = np.clip((t - 0.55) / 0.45, 0, 1)[..., None]
    gm = np.where(t[..., None] < 0.55, INK + (MID - INK) * lo, MID + (CREAM - MID) * hi) / 255.0
    a = a * (1 - mix) + gm * mix
    # 5. soft lift in the shadows so nothing goes inky black
    a = 0.06 + a * 0.94
    # 6. gentle rose vignette
    yy, xx = np.mgrid[0:N, 0:N] / (N - 1) - 0.5
    v = np.clip((np.sqrt(xx ** 2 + yy ** 2) - 0.28) / 0.3, 0, 1)[..., None] ** 1.6
    a = a * (1 - 0.22 * v) + (MID / 255.0) * 0.22 * v
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

before, after = [], []
for k, (fn, box) in CROPS.items():
    im = Image.open(f"{src}/{fn}").convert("RGB").crop(box).resize((N, N), Image.LANCZOS)
    gi = grade(im, k)
    gi.save(f"{out}/k{k}.webp", "WEBP", quality=82, method=6)
    before.append(im); after.append(gi)

# comparison sheet: before row over after row, circles like the page shows them
T = 150
mask = Image.new("L", (T, T), 0); ImageDraw.Draw(mask).ellipse((0, 0, T - 1, T - 1), fill=255)
cols = 7
sheet = Image.new("RGB", (cols * (T + 10) + 10, 4 * (T + 10) + 10), (255, 243, 246))
for row, imgs in enumerate([before[:7], after[:7], before[7:], after[7:]]):
    for c, im in enumerate(imgs):
        sheet.paste(im.resize((T, T), Image.LANCZOS), (10 + c * (T + 10), 10 + row * (T + 10)), mask)
sheet.save(sheet_path)
print("ok")
