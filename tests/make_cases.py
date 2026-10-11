"""Prépare les cas de test pour check_js.js (signaux bruts + features Python + prédictions Keras)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extract_features import signal_features
from rul_lib import FEATS, relative_features

s = np.load('cache/samples_test2.npz')
signals = []
for k in [k for k in s.files if k != 'names']:
    for ch in range(4):
        x = s[k][:, ch].astype(float)
        f = signal_features(x)
        signals.append({'signal': x.tolist(), 'features': [f[n] for n in FEATS]})
out = {'signals': signals}
if os.path.exists('twin_weights.json') and os.path.exists('cnn_lstm_rul.keras'):
    import keras
    tw = json.load(open('twin_weights.json'))
    m = keras.models.load_model('cnn_lstm_rul.keras')
    ref = tw['demo']['ref']
    out['model'] = tw
    out['predictions'] = []
    for name in ('healthy', 'degraded'):
        X = np.log(relative_features(np.array(tw['demo'][name]), np.median(ref, axis=0)))
        out['predictions'].append({'name': name, 'seq': tw['demo'][name], 'ref': ref,
                                   'keras': float(m.predict(X[None], verbose=0)[0, 0])})
json.dump(out, open(sys.argv[1], 'w'))
print('cas écrits :', sys.argv[1])
