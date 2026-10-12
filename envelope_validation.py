"""Validation du détecteur à un seul fichier (spectre d'enveloppe) sur les 984 acquisitions brutes du 2nd test.
Même algorithme que l'interface : passe-bande 2–8 kHz par FFT, enveloppe de Hilbert, FFT de l'enveloppe,
émergence = moyenne des 3 premières harmoniques / médiane du spectre (20–1000 Hz)."""
import os
import sys

import numpy as np
import pandas as pd

FS = 20000
n_r, d, D, a, fr = 16, .331, 2.815, np.deg2rad(15.17), 2000 / 60
q = d / D * np.cos(a)
GEOM = {'BPFO': n_r / 2 * fr * (1 - q), 'BPFI': n_r / 2 * fr * (1 + q), 'BSF': D / (2 * d) * fr * (1 - q * q)}


def emergence(x):
    x = x - x.mean(); n = len(x)
    X = np.fft.fft(x); f = np.fft.fftfreq(n, 1 / FS)
    Z = np.zeros_like(X); m = (f >= 2000) & (f <= 8000); Z[m] = 2 * X[m]
    env = np.abs(np.fft.ifft(Z)); env -= env.mean()
    E = np.abs(np.fft.rfft(env)) / n; fe = np.fft.rfftfreq(n, 1 / FS)
    sel = fe <= 1000; E, fe = E[sel], fe[sel]
    noise = np.median(E[fe > 20]) + 1e-12
    out = {}
    for k, F in GEOM.items():
        out[k] = np.mean([E[np.abs(fe - h * F) <= .03 * h * F].max() for h in (1, 2, 3)]) / noise
    return out


folder = sys.argv[1]
files = sorted(os.listdir(folder))
rows = []
for i, fn in enumerate(files):
    sig = pd.read_csv(os.path.join(folder, fn), sep='\t', header=None).to_numpy()
    for b in range(4):
        if np.sqrt(np.mean(sig[:, b] ** 2)) < 0.01:
            continue
        rows.append({'idx': i, 'Bearing': b + 1, **emergence(sig[:, b])})
r = pd.DataFrame(rows)
r.to_csv('cache/envelope_test2.csv', index=False)
fail = r.idx.max()
for b in range(1, 5):
    x = r[r.Bearing == b]
    for k in GEOM:
        hit = x[x[k] >= 8]
        first = hit.idx.min() if len(hit) else None
        print(f'B{b} {k}: émergence médiane {x[k].median():.1f} | max {x[k].max():.1f} | '
              f'>=8 sur {len(hit)} fichiers' + (f', premier au fichier {first} ({(fail - first) * 10 / 60:.1f} h avant la fin)' if first is not None else ''))
