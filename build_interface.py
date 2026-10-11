"""Génère les interfaces à partir des poids exportés.
- rul_4feat.html        : version simple (twin_weights.json, produit par le notebook section 7.6)
- jumeau_numerique.html : tableau de bord complet (+ twin_replay.json, produit par make_twin_data.py)"""
import json


def embed(obj):
    return json.dumps(obj, separators=(',', ':')).replace('</', r'<\/')


model = json.load(open('twin_weights.json', encoding='utf-8'))
head = open('interface_head.html', encoding='utf-8').read()
body = open('interface_body.html', encoding='utf-8').read()
open('rul_4feat.html', 'w', encoding='utf-8', newline='\n').write(head + body.replace('__MODEL_DATA__', embed(model)))
print('rul_4feat.html généré')

replay = json.load(open('twin_replay.json', encoding='utf-8'))
tpl = open('twin_template.html', encoding='utf-8').read()
html = tpl.replace('__MODEL_DATA__', embed(model)).replace('__REPLAY_DATA__', embed(replay))
open('jumeau_numerique.html', 'w', encoding='utf-8', newline='\n').write(html)
print(f'jumeau_numerique.html généré ({len(html) / 1e6:.1f} Mo)')
