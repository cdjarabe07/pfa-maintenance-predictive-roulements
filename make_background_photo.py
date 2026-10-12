"""Fond du site : photo « 2015 F.A.G. NJ306E Roller Bearing » (Andydevon, CC BY-SA 4.0, Wikimedia Commons),
recadrée en 16:9 (roulement à droite), assombrie, teintée bleu nuit et vignettée.
L'image dérivée est diffusée sous la même licence CC BY-SA 4.0.
Usage : python make_background_photo.py <photo originale> <sortie.jpg>"""
import sys

import numpy as np
from PIL import Image, ImageFilter

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB')
w, h = im.size                                    # 3888 x 2592
W = int(h * 16 / 9)                               # toile 16:9 de même hauteur
canvas = Image.new('RGB', (W, h), (6, 9, 13))
off = int(0.68 * W - 0.52 * w)                    # centre du roulement à 68 % de la largeur
canvas.paste(im, (off, 0))
a = np.asarray(canvas).astype(np.float32) / 255

# étalonnage : désaturation partielle, assombrissement, teinte bleu nuit
lum = a @ np.array([.299, .587, .114], dtype=np.float32)
a = lum[..., None] * .55 + a * .45
a = np.power(a, 1.35) * .9
tint = np.array([.78, .95, 1.08], dtype=np.float32)
a = np.clip(a * tint, 0, 1)

# vignettage centré sur le roulement + fondu vers la gauche
yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
r = np.sqrt(((xx - .68 * W) / (.42 * W)) ** 2 + ((yy - .52 * h) / (.62 * h)) ** 2)
vig = np.clip(1.15 - .85 * r, 0, 1) ** 1.4
left = np.clip((xx / W - .2) / .45, 0, 1)
a = a * (vig * left)[..., None] + np.array([6, 9, 13], dtype=np.float32) / 255 * (1 - vig * left)[..., None]

img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((2400, 1350), Image.LANCZOS)
img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))
img.save(out, quality=82, optimize=True, progressive=True)
print(out, img.size)
