# PFA — Maintenance prédictive des roulements (NASA IMS)

| Fichier | Rôle |
|---|---|
| `IMS_Bearing_Analysis_corrige.ipynb` | Notebook corrigé et exécuté (toutes les sorties sont enregistrées) |
| `IMS_Bearing_Analysis.ipynb` | Notebook d'origine, conservé pour comparaison |
| `jumeau_numerique.html` | **Tableau de bord BearingTwin** : rejeu animé du 2nd test, vue machine, jauge RUL, spectre d'enveloppe, journal d'alertes, analyse de vos fichiers |
| `rul_4feat.html` | Interface opérateur simple (version précédente) |
| `rul_lib.py` | Fonctions RUL partagées (trajectoires, RUL par morceaux, fenêtres, modèles) |
| `extract_features.py` | Calcule les features à partir des fichiers bruts IMS → `cache/` |
| `cache/` | Features des 3 tests + quelques signaux bruts (le notebook tourne sans les 6 Go de données) |
| `exp1_protocoles.py`, `exp2_cross_tests.py` | Expériences préliminaires (fuite de données, validation par panne) |
| `build_interface.py`, `twin_template.html`, `interface_*.html` | Génèrent les deux interfaces à partir de `twin_weights.json` et `twin_replay.json` |
| `make_twin_data.py` | Entraîne le CNN-LSTM **sans le 2nd test** pour le rejeu (prédiction honnête) → `twin_replay.json` |
| `tests/` | Vérifie que le JavaScript de l'interface donne les mêmes résultats que Python/Keras |

## Lancer le notebook

```
pip install pandas numpy scipy matplotlib seaborn scikit-learn PyWavelets xgboost tensorflow
jupyter notebook IMS_Bearing_Analysis_corrige.ipynb
```
`rul_lib.py` et `cache/` doivent rester à côté du notebook.

## Régénérer les interfaces après réentraînement

Le notebook (section 7.6) écrit `twin_weights.json`, puis :
```
python make_twin_data.py      # modèle du rejeu (≈ 5 min)
python build_interface.py
```

## Tableau de bord `jumeau_numerique.html`

S'ouvre par double-clic (fonctionne hors ligne). Deux modes :
- **Rejeu du 2nd test** : ▶ lance la lecture (×1, ×4, ×16), le curseur permet de se déplacer dans les 7 jours
  d'essai, un clic sur un roulement l'inspecte. Raccourcis : `Espace` lecture/pause, `←` `→` (± 10 min),
  `Maj` + flèches (± 5 h). Lien direct vers un instant : `jumeau_numerique.html#t=950&b=1` (`#play` pour lancer).
- **Analyser mes fichiers** : glisser-déposer le dossier d'acquisitions d'un roulement.

Pour la soutenance : ouvrir `#t=500` (sain), lancer en ×16 et commenter la bascule SURVEILLANCE → ARRÊT,
puis le spectre d'enveloppe à la fin (signature BPFO).

## Interface simple `rul_4feat.html`

Ouvrir `rul_4feat.html`, choisir la colonne du roulement, puis « Charger le dossier d'acquisitions »
(au moins 230 fichiers : les 200 premiers servent de référence « roulement neuf », les 30 derniers sont analysés).
Les boutons « Démo » fonctionnent sans données.
