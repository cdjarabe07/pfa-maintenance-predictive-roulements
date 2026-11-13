# PFA — Maintenance prédictive des roulements (NASA IMS)

| Fichier | Rôle |
|---|---|
| `IMS_Bearing_Analysis_corrige.ipynb` | Notebook corrigé et exécuté (toutes les sorties sont enregistrées) |
| `IMS_Bearing_Analysis.ipynb` | Notebook d'origine, conservé pour comparaison |
| `jumeau_numerique.html` | **Poste de surveillance vibratoire** : supervision des 4 paliers (rejeu), diagnostic instantané sur un fichier, pronostic RUL sur historique, alarmes à acquitter, rapport PDF, visite guidée |
| `rul_4feat.html` | Interface opérateur simple (version précédente) |
| `rul_lib.py` | Fonctions RUL partagées (trajectoires, RUL par morceaux, fenêtres, modèles) |
| `extract_features.py` | Calcule les features à partir des fichiers bruts IMS → `cache/` |
| `cache/` | Features des 3 tests + quelques signaux bruts (le notebook tourne sans les 6 Go de données) |
| `exp1_protocoles.py`, `exp2_cross_tests.py` | Expériences préliminaires (fuite de données, validation par panne) |
| `build_interface.py`, `twin_template.html`, `interface_*.html` | Génèrent les deux interfaces à partir de `twin_weights.json` et `twin_replay.json` |
| `make_twin_data.py` | Entraîne le CNN-LSTM **sans le 2nd test** pour le rejeu (prédiction honnête) → `twin_replay.json` |
| `envelope_validation.py`, `make_twin_extras.py` | Valident le détecteur par spectre d'enveloppe sur les 984 acquisitions du 2nd test et préparent ses données pour l'interface → `twin_extras.json` |
| `tests/` | Vérifie que le JavaScript de l'interface donne les mêmes résultats que Python/Keras |
| `classification/` | **Interface unique** (supervision, prédictions, modèles, voir plus bas) : CSV de Salma, préparation des données, gabarit et assemblage de `site/jumeau_roulements.html` |

## Interface unique `site/jumeau_roulements.html`

Poste de supervision en une seule page, style atelier (menu à gauche), qui regroupe toutes les fonctions du projet :

| Page | Entrée | Résultat |
|---|---|---|
| Supervision | rejeu des 984 acquisitions du 2nd test IMS | synoptique des 4 paliers, état, bon de travail suggéré, historique des alertes, journal |
| Durée de vie restante | un dossier de **≥ 230 fichiers** consécutifs d'un roulement (ou un exemple) | durée restante en jours (CNN-LSTM exact, calculé dans le navigateur) |
| État d'un roulement | **un seul fichier** (20 480 lignes, 4 colonnes) | normal / anormal pour chacun des 4 roulements, au choix règle des seuils, arbre, régression logistique ou Bayes naïf |
| Comparer les modèles | – | validation croisée, roulement jamais vu, matrices de confusion |
| Simulateur de seuils | curseurs | verdict de la règle IQR |
| Limites de l'étude | – | ce que les scores montrent et ne montrent pas |

La durée restante ne peut pas être estimée avec un seul fichier : le modèle lit une trajectoire de 30 relevés comparée à l'état neuf
(200 premiers relevés). La page « État d'un roulement » n'est valable que pour les quatre roulements de cet essai (seuils propres à
chaque roulement).

```
python classification/prep_twin_data.py classification/bearing_features_labels_2nd_test.csv classification/twin_data.json   # ≈ 30 s
python classification/build_jumeau.py                                                                                      # écrit site/jumeau_roulements.html
python tests/make_jumeau_cases.py /tmp/cases && node tests/check_jumeau.js /tmp/cases                                       # vérifications
```

`prep_twin_data.py` vérifie que les seuils IQR redonnent exactement les labels du CSV, reproduit la validation croisée 5 plis
(un modèle par roulement, graine 42), ajoute l'évaluation sur roulement jamais vu et exporte l'arbre, la régression logistique et le
Bayes naïf de chaque roulement. `tests/check_jumeau.js` vérifie que les quatre mesures calculées depuis un fichier brut égalent le CSV,
que les prédictions JavaScript égalent scikit-learn sur les 3 936 lignes, que la durée restante égale l'ancienne interface, et
déroule le parcours (fichiers valides, erreurs, mobile).

## Site public

**https://pfa-maintenance-roulements.vercel.app** — page d'accueil (fond : spectrogramme réel du palier 1, généré par
`make_background.py`) et interface unique (`/jumeau_roulements.html`). Site non indexé par les moteurs de recherche.
Le dossier `site/` est publié tel quel depuis Git (dépôt GitHub, branche `jumeau-numerique-classification`, dossier racine `site`).
L'ancien poste de surveillance (`jumeau_numerique.html`), `rul_4feat.html` et l'archive du projet sont générés et ignorés par Git :
`bash deploy_site.sh` les régénère et republie le site complet depuis un ordinateur connecté à Vercel.

## Lancer le notebook

```
pip install pandas numpy scipy matplotlib seaborn scikit-learn PyWavelets xgboost tensorflow
jupyter notebook IMS_Bearing_Analysis_corrige.ipynb
```
`rul_lib.py` et `cache/` doivent rester à côté du notebook.

## Régénérer les interfaces après réentraînement

Le notebook (section 7.6) écrit `twin_weights.json`, puis :
```
python make_twin_data.py                       # modèle du rejeu (≈ 5 min)
python envelope_validation.py <dossier 2nd_test>  # émergences des fréquences de défaut (≈ 2 min)
python make_twin_extras.py <dossier 2nd_test>     # spectres horaires + exemples
python build_interface.py
```

## Poste de surveillance `jumeau_numerique.html`

S'ouvre par double-clic (fonctionne hors ligne). Une **visite guidée** se lance à la première ouverture
(bouton « Visite guidée » ensuite). Trois onglets :

| Onglet | Entrée | Résultat |
|---|---|---|
| **Supervision** (mode démonstration) | rejeu des 984 acquisitions du 2nd test IMS | état des 4 paliers, RUL, tendances, spectre, journal d'alarmes |
| **Diagnostic instantané** | **1 seul fichier** (toutes les voies) | défaut détecté, pièce concernée (BPFO / BPFI / BSF), voie en cause, propagation |
| **Pronostic sur historique** | **≥ 230 fichiers consécutifs** d'un roulement | RUL + tendances + alarmes |

Pourquoi 230 fichiers pour la RUL : le modèle lit une trajectoire de 30 acquisitions (5 h), pas un état isolé,
et les 200 premières acquisitions servent de référence de l'état neuf. Sur un seul fichier, on ne peut pas
estimer la RUL, mais le spectre d'enveloppe identifie le défaut (validé : détection 74 h avant la rupture,
aucune fausse détection en phase saine, notebook section 9). Un classifieur healthy/faulty sur fichier unique
a été testé et écarté (F1 ≈ 0,36 sur un essai jamais vu).

Logique d'état : le plus sévère de trois critères, mesures lissées sur 1 h et hystérésis de retour à la normale :
pronostic RUL (alerte < 2,5 j, alarme < 1 j), niveau RMS / référence (alerte +6 dB, alarme +12 dB),
signature spectrale (alerte si émergence ≥ ×8).

Liens directs : `#t=950&b=1` (instant et palier du rejeu), `#play` (lecture), `#inst=0` / `#inst=1`
(exemples sain / dégradé du diagnostic instantané), `#tour` (visite guidée). Raccourcis : `Espace`, `←` `→`, `Maj` + flèches.

Scénario de soutenance : visite guidée → Supervision à `#t=500`, lecture ×16 : l'alerte spectrale apparaît le 16/02
(74 h avant la rupture), puis les alertes RUL et vibratoires → acquitter une alarme → Diagnostic instantané sur
l'exemple dégradé (localisation voie 1) → Rapport PDF.

## Interface simple `rul_4feat.html`

Ouvrir `rul_4feat.html`, choisir la colonne du roulement, puis « Charger le dossier d'acquisitions »
(au moins 230 fichiers : les 200 premiers servent de référence « roulement neuf », les 30 derniers sont analysés).
Les boutons « Démo » fonctionnent sans données.
