#!/usr/bin/env bash
# Republie le site public https://pfa-maintenance-roulements.vercel.app
# (page d'accueil + interfaces + archive du projet à jour). Nécessite le CLI Vercel connecté.
set -e
cd "$(dirname "$0")"
python build_interface.py
python classification/build_jumeau.py
cp jumeau_numerique.html rul_4feat.html site/
git archive --format=zip --prefix=pfa_maintenance_roulements/ -o site/projet_pfa_roulements.zip HEAD
cd site && npx -y vercel@latest deploy --prod --yes
