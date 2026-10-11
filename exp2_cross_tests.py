"""Expérience 2 : validation croisée par trajectoire (leave-one-failure-out).
On entraîne sur toutes les pannes sauf une et on prédit la panne mise de côté
(roulement et test jamais vus). Usage : python exp2_cross_tests.py [test2_B1 test1_B3 ...]"""
import sys

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from rul_lib import (FAILURES, FEATS, build_cnn_lstm, build_lstm, failure_trajectory, fit_keras,
                     healthy_reference, metrics, piecewise_rul, relative_features,
                     sliding_windows)

CAP = 3.0
names = sys.argv[1:] or list(FAILURES)

data = {}
for k in names:
    b = failure_trajectory(*FAILURES[k])
    Xr = np.log(relative_features(b[FEATS].to_numpy(), healthy_reference(b)))  # 0 = sain
    data[k] = sliding_windows(Xr, piecewise_rul(b['RUL'].to_numpy(), CAP)) + (b['RUL'].to_numpy()[29:],)


def flat(Xw):  # features résumées de la fenêtre pour le modèle classique
    return np.concatenate([Xw[:, -1], Xw.mean(1), Xw.max(1)], axis=1)


rows = []
for test in names:
    tr = [k for k in names if k != test]
    Xtr = np.concatenate([data[k][0] for k in tr]); ytr = np.concatenate([data[k][1] for k in tr])
    Xte, yte, rul_true = data[test]
    rng = np.random.default_rng(0); perm = rng.permutation(len(Xtr)); nv = int(0.15 * len(Xtr))
    va, trn = perm[:nv], perm[nv:]
    preds = {'Constante (toujours CAP)': np.full(len(yte), CAP),
             'Random Forest': RandomForestRegressor(300, min_samples_leaf=5, random_state=0)
             .fit(flat(Xtr), ytr).predict(flat(Xte))}
    for name, build in [('LSTM', build_lstm), ('CNN-LSTM', build_cnn_lstm)]:
        m = build(); fit_keras(m, Xtr[trn], ytr[trn], Xtr[va], ytr[va])
        preds[name] = m.predict(Xte, verbose=0).ravel()
    deg = yte < CAP  # phase de dégradation (là où la RUL compte vraiment)
    for name, yp in preds.items():
        yp = np.clip(yp, 0, None)
        r_all, r_deg = metrics(yte, yp), metrics(yte[deg], yp[deg])
        rows.append((test, name, r_all['MAE'], r_deg['MAE'], r_deg['RMSE']))
        print(f'{test:9s} {name:26s} MAE tout={r_all["MAE"]:.3f} j | dégradation : '
              f'MAE={r_deg["MAE"]:.3f} j RMSE={r_deg["RMSE"]:.3f} j', flush=True)
    np.savez(f'cache/pred_{test}.npz', y=yte, rul=rul_true, **{k.split()[0]: v for k, v in preds.items()})

print('\nMoyenne sur les pannes testées (phase de dégradation) :')
for name in dict.fromkeys(r[1] for r in rows):
    sel = [r for r in rows if r[1] == name]
    print(f'  {name:26s} MAE={np.mean([r[3] for r in sel]):.3f} j  RMSE={np.mean([r[4] for r in sel]):.3f} j')
