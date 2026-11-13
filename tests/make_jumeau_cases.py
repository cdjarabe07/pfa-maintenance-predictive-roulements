"""Prépare les cas de test de check_jumeau.js : relevés bruts en texte (3 instants de l'essai n°2), valeurs du CSV, prédictions scikit-learn.
Usage : python tests/make_jumeau_cases.py <dossier_sortie>"""
import json, os, sys
import numpy as np, pandas as pd

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
z = np.load(os.path.join(root, 'cache', 'samples_test2.npz'))
d = pd.read_csv(os.path.join(root, 'classification', 'bearing_features_labels_2nd_test.csv'))
cases = []
for name, i in (('idx0', 0), ('idx492', 492), ('idx974', 974)):
    a = z[name]
    np.savetxt(os.path.join(out, f'{name}.txt'), a, fmt='%.6f', delimiter='\t')
    rows = [d[d.bearing == f'Bearing {k + 1}'].reset_index(drop=True).loc[i, ['rms', 'energy', 'entropy', 'kurtosis']].astype(float).tolist() for k in range(4)]
    cases.append({'file': f'{name}.txt', 'csv': rows})
feats = {f'Bearing {k + 1}': d[d.bearing == f'Bearing {k + 1}'].sort_values('timestamp')[['rms', 'energy', 'entropy', 'kurtosis']].values.tolist() for k in range(4)}
labels = {f'Bearing {k + 1}': d[d.bearing == f'Bearing {k + 1}'].sort_values('timestamp').label.astype(int).tolist() for k in range(4)}
exp = json.load(open(os.path.join(root, 'classification', 'twin_data_clf_expected.json')))
json.dump({'cases': cases, 'feats': feats, 'labels': labels, 'expected': exp}, open(os.path.join(out, 'cases.json'), 'w'))
# fichier à 8 colonnes et fichier court, pour les messages d'erreur
np.savetxt(os.path.join(out, 'huit.txt'), np.hstack([z['idx0'], z['idx0']]), fmt='%.4f', delimiter='\t')
np.savetxt(os.path.join(out, 'court.txt'), z['idx0'][:5000], fmt='%.4f', delimiter='\t')
print('ok', out)
