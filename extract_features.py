"""Extraction des features par acquisition (1 fichier = 1 s de vibration à 20 kHz).

Usage : python extract_features.py <dossier_du_test> <nom_test> <n_canaux>
Produit cache/features_<nom_test>.csv (une ligne par fichier et par roulement)
et cache/samples_<nom_test>.npz (quelques signaux bruts pour les sections FFT/ondelettes).

Pour le 1st test (8 canaux = 2 accéléromètres x et y par roulement), on garde le canal x
(colonnes 0, 2, 4, 6) afin d'avoir 1 signal par roulement comme dans les 2nd et 3rd tests.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

FS = 20000


def signal_features(sig):
    """Mêmes définitions que l'interface HTML (RMS, Énergie, Entropie spectrale, Kurtosis)."""
    rms = np.sqrt(np.mean(sig ** 2))
    energy = np.sum(sig ** 2)
    spec = np.abs(np.fft.rfft(sig - sig.mean()))
    p = spec / (spec.sum() + 1e-12)
    ent = -np.sum(p * np.log(p + 1e-12))
    return {
        'MeanAbs': np.mean(np.abs(sig)),
        'RMS': rms,
        'Energy': energy,
        'Entropy': ent,
        'Kurtosis': float(kurtosis(sig)),
        'Skewness': float(skew(sig)),
        'Peak': np.max(np.abs(sig)),
        'Crest': np.max(np.abs(sig)) / (rms + 1e-12),
    }


def main(test_dir, test_name, n_channels):
    files = sorted(f for f in os.listdir(test_dir) if not f.startswith('.'))
    channels = [0, 2, 4, 6] if n_channels == 8 else [0, 1, 2, 3]
    rows, samples = [], {}
    keep = {0, len(files) // 2, len(files) - 1}
    for k, f in enumerate(files):
        data = pd.read_csv(os.path.join(test_dir, f), sep='\t', header=None).to_numpy()
        ts = pd.to_datetime(f, format='%Y.%m.%d.%H.%M.%S')
        for b, ch in enumerate(channels):
            feats = signal_features(data[:, ch])
            rows.append({'File': f, 'Date': ts, 'Bearing': b + 1, **feats})
        if k in keep:
            samples[f'idx{k}'] = data[:, channels].astype(np.float32)
        if k % 200 == 0:
            print(f'{test_name}: {k}/{len(files)}', flush=True)
    os.makedirs('cache', exist_ok=True)
    pd.DataFrame(rows).to_csv(f'cache/features_{test_name}.csv', index=False)
    np.savez_compressed(f'cache/samples_{test_name}.npz',
                        **samples, names=np.array([files[i] for i in sorted(keep)]))
    print(f'{test_name}: terminé ({len(files)} fichiers)')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
