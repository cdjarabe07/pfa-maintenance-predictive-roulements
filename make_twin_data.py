"""Données du mode « rejeu » de l'interface (twin_replay.json).

- Modèle CNN-LSTM entraîné SANS le 2nd test (3 autres pannes) : le rejeu du 2nd test
  montre donc une prédiction sur un roulement jamais vu, comme en section 7.4 du notebook.
- Séries des 4 features pour les 4 roulements du 2nd test.
- 3 signaux bruts du Bearing 1 (début, milieu, fin) pour le spectre d'enveloppe.
"""
import base64
import json

import numpy as np

from rul_lib import (FAILURES, FEATS, N_BASE, WINDOW, build_cnn_lstm, failure_trajectory, fit_keras,
                     healthy_reference, load_features, piecewise_rul, relative_features,
                     sliding_windows)

CAP = 3.0


def prepare(b):
    Xr = np.log(relative_features(b[FEATS].to_numpy(), healthy_reference(b)))
    return sliding_windows(Xr, piecewise_rul(b['RUL'].to_numpy(), CAP))


def train_set(keys_, seed=0):
    Xs, ys = [], []
    for k in keys_:
        Xw, yw = prepare(failure_trajectory(*FAILURES[k]))
        keep = (yw < CAP) | (np.arange(len(yw)) % 5 == 0)
        Xs.append(Xw[keep]); ys.append(yw[keep])
    X_, y_ = np.concatenate(Xs), np.concatenate(ys)
    perm = np.random.default_rng(seed).permutation(len(X_)); nv = int(0.15 * len(X_))
    return X_[perm[nv:]], y_[perm[nv:]], X_[perm[:nv]], y_[perm[:nv]]


def export_weights(model):
    flat = lambda a: np.asarray(a, dtype=np.float32).ravel().round(6).tolist()
    by = lambda t: [l for l in model.layers if l.__class__.__name__ == t]
    W = {}
    for i, (c, n) in enumerate(zip(by('Conv1D'), by('BatchNormalization')), start=1):
        k, bias = c.get_weights(); g, beta, mm, mv = n.get_weights()
        W.update({f'conv{i}_k': flat(k), f'conv{i}_b': flat(bias), f'bn{i}_g': flat(g),
                  f'bn{i}_b': flat(beta), f'bn{i}_m': flat(mm), f'bn{i}_v': flat(mv)})
    lk, lu, lb = by('LSTM')[0].get_weights()
    d1, d2 = by('Dense')
    W.update({'lstm_k': flat(lk), 'lstm_u': flat(lu), 'lstm_b': flat(lb),
              'dense1_w': flat(d1.get_weights()[0]), 'dense1_b': flat(d1.get_weights()[1]),
              'dense2_w': flat(d2.get_weights()[0]), 'dense2_b': flat(d2.get_weights()[1])})
    return W


Xtr, ytr, Xva, yva = train_set([k for k in FAILURES if k != 'test2_B1'])
model = build_cnn_lstm(); fit_keras(model, Xtr, ytr, Xva, yva, epochs=80, patience=10)

d = load_features('test2')
t0 = d.Date.min()
bearings = {}
for b in range(1, 5):
    s = d[d.Bearing == b].sort_values('Date')
    bearings[b] = s[FEATS].round(6).to_numpy().tolist()
dates = d[d.Bearing == 1].sort_values('Date').Date
s = np.load('cache/samples_test2.npz')
raw = {k: base64.b64encode(s[k][:, 0].astype('<f4').tobytes()).decode() for k in s.files if k != 'names'}
idx = {k: int(k[3:]) for k in raw}

out = {'weights': export_weights(model), 'start': str(t0), 'failure': str(dates.max()),
       'minutes': ((dates - t0).dt.total_seconds() / 60).round().astype(int).tolist(),
       'bearings': bearings, 'raw_b1': [{'idx': idx[k], 'f32': raw[k]} for k in sorted(raw, key=idx.get)]}
json.dump(out, open('twin_replay.json', 'w'), separators=(',', ':'))

# Contrôle : prédiction Keras sur 3 fenêtres du Bearing 1 (à comparer avec le JS)
b1 = failure_trajectory('test2', 1)
Xw, _ = prepare(b1)
for i in (300, 700, len(Xw) - 1):
    print(f'fenêtre {i}: RUL réelle {b1.RUL.iloc[i + WINDOW - 1]:.2f} j, prédite {model.predict(Xw[i:i+1], verbose=0)[0, 0]:.3f} j')
print('twin_replay.json écrit')
