# PFA — Maintenance prédictive des roulements (NASA IMS)

| Fichier | Rôle |
|---|---|
| `IMS_Bearing_Analysis_corrige.ipynb` | Notebook corrigé et exécuté (toutes les sorties sont enregistrées) |
| `IMS_Bearing_Analysis.ipynb` | Notebook d'origine, conservé pour comparaison |
| `jumeau_numerique.html` | **Poste de surveillance vibratoire** : supervision des 4 paliers, pronostic RUL, tendances avec seuils, spectre d'enveloppe et diagnostic, journal d'alarmes à acquitter, rapport PDF, import de mesures brutes |
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

## Poste de surveillance `jumeau_numerique.html`

S'ouvre par double-clic (fonctionne hors ligne). Deux onglets :
- **Supervision** (mode démonstration) : rejeu des mesures du 2nd test IMS. Lecture / pause, vitesse ×1 à ×16,
  curseur temporel. Sélection d'un palier dans l'arborescence ou sur le synoptique. Raccourcis : `Espace`,
  `←` `→` (± 10 min), `Maj` + flèches (± 5 h). Lien direct : `jumeau_numerique.html#t=950&b=1` (`#play` pour lancer).
- **Import de mesures** : glisser-déposer le dossier d'acquisitions brutes d'un roulement (≥ 230 fichiers).

Logique de décision : état = le plus sévère entre le pronostic RUL (alerte < 2,5 j, alarme < 1 j) et le niveau
vibratoire RMS par rapport à la référence (alerte +6 dB, alarme +12 dB), mesures lissées sur 1 h, hystérésis
de retour à la normale (0,25 j / 1 dB). Le bouton « Rapport PDF » imprime un rapport de diagnostic.

Scénario de soutenance : ouvrir `#t=500` (état normal), lancer en ×16, commenter l'apparition des alertes puis
des alarmes dans le journal, acquitter une alarme, puis montrer le spectre d'enveloppe en fin d'essai
(défaut de bague extérieure identifié) et exporter le rapport PDF.

## Interface simple `rul_4feat.html`

Ouvrir `rul_4feat.html`, choisir la colonne du roulement, puis « Charger le dossier d'acquisitions »
(au moins 230 fichiers : les 200 premiers servent de référence « roulement neuf », les 30 derniers sont analysés).
Les boutons « Démo » fonctionnent sans données.
