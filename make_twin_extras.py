"""Données complémentaires de l'interface (twin_extras.json) :
- émergence BPFO/BPFI/BSF du spectre d'enveloppe pour chaque acquisition et chaque palier du 2nd test
  (produit par envelope_validation.py -> cache/envelope_test2.csv) ;
- spectres d'enveloppe 0–1000 Hz, une acquisition par heure et par palier, quantifiés sur 8 bits (échelle log, 80 dB) ;
- deux fichiers bruts complets (4 voies) pour les exemples du mode « diagnostic instantané ».
Usage : python make_twin_extras.py <dossier 2nd_test>"""
import base64
import json
import os
import sys

import numpy as np
import pandas as pd

folder = sys.argv[1]
files = sorted(os.listdir(folder))
env = pd.read_csv('cache/envelope_test2.csv')
n = len(files)
emergence = {}
for b in range(1, 5):
    x = env[env.Bearing == b].set_index('idx')
    emergence[b] = {k: [None if i not in x.index else round(float(x.at[i, k]), 1) for i in range(n)]
                    for k in ('BPFO', 'BPFI', 'BSF')}

FS, STEP = 20000, 6


def env_spectrum(x):  # même calcul que l'interface (envelopeSpectrum)
    x = x - x.mean(); n = len(x)
    X = np.fft.fft(x); f = np.fft.fftfreq(n, 1 / FS)
    Z = np.zeros_like(X); m = (f >= 2000) & (f <= 8000); Z[m] = 2 * X[m]
    env = np.abs(np.fft.ifft(Z)); env -= env.mean()
    E = np.abs(np.fft.rfft(env)) / n
    return E[:int(1000 / (FS / n)) + 1]


spectra = []
for i in range(0, n, STEP):
    sig = pd.read_csv(os.path.join(folder, files[i]), sep='\t', header=None).to_numpy()
    for b in range(4):
        if np.sqrt(np.mean(sig[:, b] ** 2)) < 0.01:
            continue
        a = env_spectrum(sig[:, b]); hi = np.log10(a.max()); lo = hi - 4
        q = np.clip(np.round((np.log10(np.maximum(a, 1e-30)) - lo) / (hi - lo) * 255), 0, 255).astype(np.uint8)
        spectra.append({'idx': i, 'b': b + 1, 'hi': round(float(hi), 5), 'q': base64.b64encode(q.tobytes()).decode()})

examples = []
for idx, label in [(300, 'Acquisition en fonctionnement sain'), (974, 'Acquisition en fin d’essai (défaut développé)')]:
    sig = pd.read_csv(os.path.join(folder, files[idx]), sep='\t', header=None).to_numpy().astype('<f4')
    examples.append({'name': files[idx], 'label': label, 'channels': sig.shape[1],
                     'f32': base64.b64encode(sig.tobytes()).decode()})  # ordre ligne par ligne (20480 x 4)

json.dump({'emergence': emergence, 'spectra': spectra, 'df': FS / 20480, 'examples': examples}, open('twin_extras.json', 'w'), separators=(',', ':'))
print(f'twin_extras.json écrit ({os.path.getsize("twin_extras.json") / 1e6:.2f} Mo)')
