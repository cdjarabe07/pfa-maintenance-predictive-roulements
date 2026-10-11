# PFA — Maintenance prédictive des roulements (NASA IMS)

| Fichier | Rôle |
|---|---|
| `IMS_Bearing_Analysis_corrige.ipynb` | Notebook corrigé et exécuté (toutes les sorties sont enregistrées) |
| `IMS_Bearing_Analysis.ipynb` | Notebook d'origine, conservé pour comparaison |
| `rul_4feat.html` | Interface opérateur (jumeau numérique), s'ouvre dans un navigateur |
| `rul_lib.py` | Fonctions RUL partagées (trajectoires, RUL par morceaux, fenêtres, modèles) |
| `extract_features.py` | Calcule les features à partir des fichiers bruts IMS → `cache/` |
| `cache/` | Features des 3 tests + quelques signaux bruts (le notebook tourne sans les 6 Go de données) |
| `exp1_protocoles.py`, `exp2_cross_tests.py` | Expériences préliminaires (fuite de données, validation par panne) |
| `build_interface.py`, `interface_*.html` | Génèrent `rul_4feat.html` à partir de `twin_weights.json` |
| `tests/` | Vérifie que le JavaScript de l'interface donne les mêmes résultats que Python/Keras |

## Lancer le notebook

```
pip install pandas numpy scipy matplotlib seaborn scikit-learn PyWavelets xgboost tensorflow
jupyter notebook IMS_Bearing_Analysis_corrige.ipynb
```
`rul_lib.py` et `cache/` doivent rester à côté du notebook.

## Régénérer l'interface après réentraînement

Le notebook (section 7.6) écrit `twin_weights.json`, puis :
```
python build_interface.py
```

## Utiliser l'interface

Ouvrir `rul_4feat.html`, choisir la colonne du roulement, puis « Charger le dossier d'acquisitions »
(au moins 230 fichiers : les 200 premiers servent de référence « roulement neuf », les 30 derniers sont analysés).
Les boutons « Démo » fonctionnent sans données.
