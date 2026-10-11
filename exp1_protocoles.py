"""Expérience 1 : effet du protocole d'évaluation sur le 2nd test (Bearing 1).
A = protocole d'origine (fenêtres mélangées, early stopping sur le test)
B = split chronologique (train = début de vie, test = fin de vie jamais vue)."""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from rul_lib import (FEATS, build_cnn_lstm, failure_trajectory, fit_keras, metrics,
                     piecewise_rul, sliding_windows)

b = failure_trajectory('test2', 1)
X_raw = b[FEATS].to_numpy()
rul = b['RUL'].to_numpy()
idx = np.arange(len(b), dtype=float)  # simple numéro d'acquisition

res = []

# --- A : protocole d'origine
X = MinMaxScaler().fit_transform(X_raw)
Xw, yw = sliding_windows(X, rul)
Xtr, Xte, ytr, yte = train_test_split(Xw, yw, test_size=0.2, random_state=42, shuffle=True)
m = build_cnn_lstm(); fit_keras(m, Xtr, ytr, Xte, yte)
res.append(('A mélangé', 'CNN-LSTM', metrics(yte, m.predict(Xte, verbose=0).ravel())))
# Contrôle : un RF qui ne voit QUE le numéro d'acquisition (aucune vibration)
Iw, _ = sliding_windows(idx[:, None], rul)
Itr, Ite, _, _ = train_test_split(Iw[:, -1], yw, test_size=0.2, random_state=42, shuffle=True)
rf = RandomForestRegressor(200, random_state=0).fit(Itr, ytr)
res.append(('A mélangé', 'RF sur le n° d\'acquisition seul', metrics(yte, rf.predict(Ite))))

# --- B : chronologique, 70 % train / 10 % validation / 20 % test
n = len(Xw); a, c = int(0.7 * n), int(0.8 * n)
for label, target in [('linéaire', rul), ('par morceaux (cap 3 j)', piecewise_rul(rul, 3.0))]:
    sc = MinMaxScaler().fit(X_raw[:a + 29])  # scaler ajusté sur la partie train seulement
    Xw, yw = sliding_windows(sc.transform(X_raw), target)
    m = build_cnn_lstm(); fit_keras(m, Xw[:a], yw[:a], Xw[a:c], yw[a:c])
    res.append((f'B chrono, RUL {label}', 'CNN-LSTM',
                metrics(yw[c:], m.predict(Xw[c:], verbose=0).ravel())))
    print(f'  plage RUL train {yw[:a].min():.2f}-{yw[:a].max():.2f} j | test {yw[c:].min():.2f}-{yw[c:].max():.2f} j')

for p, mdl, r in res:
    print(f'{p:32s} {mdl:34s} R2={r["R2"]:7.3f}  MAE={r["MAE"]:.3f} j  RMSE={r["RMSE"]:.3f} j')
