"""Image de fond du site : spectrogramme réel du roulement 1 (2nd test IMS), 1 acquisition par heure.
Usage : python make_background.py <dossier 2nd_test> <sortie.jpg>"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn  # noqa: F401  (enregistre la palette « mako »)
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

folder, out = sys.argv[1], sys.argv[2]
files = sorted(os.listdir(folder))[:-2:3]          # toutes les 30 min, sans les 2 fichiers plats finaux
cols = []
for f in files:
    x = pd.read_csv(os.path.join(folder, f), sep='\t', header=None).to_numpy()[:, 0]
    x = x - x.mean()
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x))))[: len(x) // 2]
    cols.append(np.log10(mag.reshape(-1, 20).mean(1) + 1e-9))   # 512 bandes de ≈ 10 Hz, 0–10 kHz
S = np.array(cols).T
S = gaussian_filter(S, (1.2, 0.8))
S = (S - np.percentile(S, 5)) / (np.percentile(S, 99.7) - np.percentile(S, 5))
fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.axis('off')
ax.imshow(np.clip(S, 0, 1), aspect='auto', origin='lower', cmap='mako' if 'mako' in plt.colormaps() else 'viridis', interpolation='bicubic')
fig.savefig(out, dpi=100, pil_kwargs={'quality': 82, 'optimize': True, 'progressive': True})
print(out, os.path.getsize(out) // 1024, 'Ko', S.shape)
