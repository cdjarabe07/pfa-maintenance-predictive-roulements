"""Assemble rul_4feat.html : en-tête/CSS + corps + poids du modèle (twin_weights.json, produit par le notebook)."""
import json

head = open('interface_head.html', encoding='utf-8').read()
body = open('interface_body.html', encoding='utf-8').read()
model = json.load(open('twin_weights.json', encoding='utf-8'))
data = json.dumps(model, separators=(',', ':')).replace('</', r'<\/')
open('rul_4feat.html', 'w', encoding='utf-8', newline='\n').write(head + body.replace('__MODEL_DATA__', data))
print('rul_4feat.html généré')
