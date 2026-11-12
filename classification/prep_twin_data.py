"""Prépare les données du jumeau numérique à partir du CSV de Salma.

Usage : python3 -I prep_twin_data.py <csv> <sortie.json>

- Reproduit son protocole (CV 5 plis par roulement, graine 42) pour obtenir des prédictions hors-échantillon.
- Recalcule les seuils IQR et vérifie qu'ils redonnent exactement ses labels.
- Ajoute des évaluations plus exigeantes : roulement jamais vu (leave-one-bearing-out) et avance à la détection.
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

csv_path, out_path = sys.argv[1], sys.argv[2]
FEATS = ['rms', 'energy', 'entropy', 'kurtosis']
BEARINGS = ['Bearing 1', 'Bearing 2', 'Bearing 3', 'Bearing 4']

d = pd.read_csv(csv_path, parse_dates=['timestamp'])
d = d.sort_values(['bearing', 'timestamp']).reset_index(drop=True)
assert len(d) == 3936 and set(d.bearing) == set(BEARINGS)
ts = d[d.bearing == 'Bearing 1'].timestamp.tolist()
for b in BEARINGS:
    assert d[d.bearing == b].timestamp.tolist() == ts, 'horodatages différents'
N = len(ts)

# ---- 1. seuils IQR recalculés + vérification des labels
thr = {}
for b in BEARINGS:
    g = d[d.bearing == b]
    thr[b] = {}
    for f in FEATS:
        q1, q3 = g[f].quantile([0.25, 0.75])
        iqr = q3 - q1
        thr[b][f] = {'q1': q1, 'q3': q3, 'lo': q1 - 1.5 * iqr, 'hi': q3 + 1.5 * iqr}
recomputed = np.zeros(len(d), dtype=int)
for b in BEARINGS:
    m = (d.bearing == b).values
    out = np.zeros(m.sum(), dtype=bool)
    for f in FEATS:
        v = d.loc[m, f].values
        out |= (v < thr[b][f]['lo']) | (v > thr[b][f]['hi'])
    recomputed[m] = out.astype(int)
assert (recomputed == d.label.values).all(), 'les labels ne se reproduisent pas'
print('OK : seuils IQR recalculés = labels du CSV (3936/3936)')

# ---- 2. modèles (définitions identiques à son notebook)
def models():
    return {
        'Decision Tree': DecisionTreeClassifier(class_weight='balanced', random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1),
        'KNN': Pipeline([('s', StandardScaler()), ('m', KNeighborsClassifier(n_neighbors=5))]),
        'SVM (RBF)': Pipeline([('s', StandardScaler()), ('m', SVC(kernel='rbf', class_weight='balanced', random_state=42))]),
        'Logistic Regression': Pipeline([('s', StandardScaler()), ('m', LogisticRegression(class_weight='balanced', max_iter=5000, random_state=42))]),
        'Gaussian Naive Bayes': GaussianNB(),
    }

NAMES = list(models().keys())


def cm(y, p):
    tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp),
            'acc': (tn + tp) / (tn + fp + fn + tp), 'prec': prec, 'rec': rec, 'f1': f1}


# 2a. protocole de Salma : CV 5 plis par roulement, prédictions hors-échantillon
oof = {n: {} for n in NAMES}
for b in BEARINGS:
    g = d[d.bearing == b]
    X, y = g[FEATS], g.label
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for n, mdl in models().items():
        oof[n][b] = cross_val_predict(mdl, X, y, cv=cv, method='predict', n_jobs=1).astype(int)
y_all = {b: d[d.bearing == b].label.values for b in BEARINGS}
cv_metrics = {}
for n in NAMES:
    yt = np.concatenate([y_all[b] for b in BEARINGS])
    yp = np.concatenate([oof[n][b] for b in BEARINGS])
    cv_metrics[n] = {'overall': cm(yt, yp), **{b: cm(y_all[b], oof[n][b]) for b in BEARINGS}}
    print(f"{n:22s} CV  F1={cv_metrics[n]['overall']['f1']:.4f}  tn/fp/fn/tp={[cv_metrics[n]['overall'][k] for k in ('tn','fp','fn','tp')]}")

# garde-fou : on doit retrouver les matrices de son notebook
expected = {'Decision Tree': (3324, 6, 6, 600), 'KNN': (3327, 3, 18, 588),
            'Gaussian Naive Bayes': (3302, 28, 33, 573), 'Logistic Regression': (3274, 56, 28, 578)}
for n, e in expected.items():
    got = tuple(cv_metrics[n]['overall'][k] for k in ('tn', 'fp', 'fn', 'tp'))
    print('  vérif', n, 'OK' if got == e else f'ÉCART {got} vs {e}')

# 2b. roulement jamais vu : entraînement sur 3 roulements, test sur le 4e (variables brutes)
lobo = {n: {} for n in NAMES}
for hold in BEARINGS:
    tr, te = d[d.bearing != hold], d[d.bearing == hold]
    for n, mdl in models().items():
        mdl.fit(tr[FEATS], tr.label)
        lobo[n][hold] = cm(te.label.values, mdl.predict(te[FEATS]))
lobo_summary = {}
for n in NAMES:
    lobo_summary[n] = {b: lobo[n][b] for b in BEARINGS}
    lobo_summary[n]['mean_f1'] = float(np.mean([lobo[n][b]['f1'] for b in BEARINGS]))
    print(f"{n:22s} LOBO F1 par roulement={[round(lobo[n][b]['f1'], 3) for b in BEARINGS]}  moy={lobo_summary[n]['mean_f1']:.3f}")

# 2c. idem, mais chaque roulement est d'abord centré-réduit sur ses 20 % premiers instants (calibration « neuf »)
dn = d.copy()
for b in BEARINGS:
    m = (d.bearing == b)
    g = d[m]
    ref = g.iloc[: int(0.2 * len(g))][FEATS]
    dn.loc[m, FEATS] = ((g[FEATS] - ref.mean()) / (ref.std() + 1e-12)).values
lobo_norm = {n: {} for n in NAMES}
for hold in BEARINGS:
    tr_m, te_m = (d.bearing != hold).values, (d.bearing == hold).values
    for n, mdl in models().items():
        mdl.fit(dn.loc[tr_m, FEATS], d.label[tr_m])
        lobo_norm[n][hold] = cm(d.label[te_m].values, mdl.predict(dn.loc[te_m, FEATS]))
lobo_norm_summary = {}
for n in NAMES:
    lobo_norm_summary[n] = {b: lobo_norm[n][b] for b in BEARINGS}
    lobo_norm_summary[n]['mean_f1'] = float(np.mean([lobo_norm[n][b]['f1'] for b in BEARINGS]))
    print(f"{n:22s} LOBO normalisé moy F1={lobo_norm_summary[n]['mean_f1']:.3f}")

# ---- 3. alertes : 3 anomalies de suite => alerte, retour après 6 normaux
def episodes(series, k_on=3, k_off=6):
    """Renvoie (états 0/1 par instant, liste des débuts d'alerte)."""
    state, run1, run0, starts, states = 0, 0, 0, [], []
    for i, v in enumerate(series):
        if v:
            run1 += 1; run0 = 0
        else:
            run0 += 1; run1 = 0
        if not state and run1 >= k_on:
            state = 1; starts.append(i - k_on + 1)
        elif state and run0 >= k_off:
            state = 0
        states.append(state)
    return states, starts


# instant de rupture de référence : dernier snapshot où la machine tourne encore (RMS du roulement 1 > 0,01)
b1 = d[d.bearing == 'Bearing 1'].reset_index(drop=True)
fail_idx = int(np.where(b1.rms.values > 0.01)[0].max())
t_fail = ts[fail_idx]
hours_before = lambda i: (t_fail - ts[i]).total_seconds() / 3600.0
print('Rupture de référence (dernier snapshot en marche) :', t_fail, 'indice', fail_idx)

lead = {}
for n in ['Règle IQR'] + NAMES:
    lead[n] = {}
    for b in BEARINGS:
        ser = y_all[b] if n == 'Règle IQR' else oof[n][b]
        st, starts = episodes(ser)
        pre = [s for s in starts if s <= fail_idx]
        first = starts[0] if starts else None
        early_mask = np.array([hours_before(i) > 72 for i in range(N)])
        lead[n][b] = {
            'first_alert_h_before': None if first is None else round(hours_before(first), 1),
            'episodes': len(starts),
            'early_false_snapshots': int(np.sum(np.array(ser)[early_mask])),
            'early_snapshots': int(early_mask.sum()),
        }
    print(f"{n:22s} avance B1 = {lead[n]['Bearing 1']['first_alert_h_before']} h ; épisodes B1..B4 = {[lead[n][b]['episodes'] for b in BEARINGS]}")

# ---- 4. export compact
r = lambda v: [float(f'{x:.5g}') for x in v]
data = {
    'n': N,
    'timestamps': [t.strftime('%Y-%m-%dT%H:%M:%S') for t in ts],
    'fail_idx': fail_idx,
    'bearings': BEARINGS,
    'feats': FEATS,
    'series': {b: {f: r(d[(d.bearing == b)][f].values) for f in FEATS} for b in BEARINGS},
    'thr': {b: {f: {k: float(f'{v:.6g}') for k, v in thr[b][f].items()} for f in FEATS} for b in BEARINGS},
    'rule': {b: ''.join(map(str, y_all[b])) for b in BEARINGS},
    'models': NAMES,
    'oof': {n: {b: ''.join(map(str, oof[n][b])) for b in BEARINGS} for n in NAMES},
    'cv': cv_metrics,
    'lobo': lobo_summary,
    'lobo_norm': lobo_norm_summary,
    'lead': lead,
}
json.dump(data, open(out_path, 'w'), separators=(',', ':'))
import os
print('écrit', out_path, round(os.path.getsize(out_path) / 1024, 1), 'Ko')
