"""Assemble le jumeau numérique : gabarit + données -> site/jumeau_roulements.html

Les données (twin_data.json) viennent de prep_twin_data.py :
    python classification/prep_twin_data.py classification/bearing_features_labels_2nd_test.csv classification/twin_data.json
Le modèle de durée de vie restante (CNN-LSTM, twin_weights.json) vient du notebook, section 7.6.
Puis :
    python classification/build_jumeau.py
"""
import json
import pathlib

here = pathlib.Path(__file__).resolve().parent
root = here.parent
tpl = (here / 'jumeau_template.html').read_text(encoding='utf-8')
data = (here / 'twin_data.json').read_text(encoding='utf-8').replace('</', r'<\/')
model = json.dumps(json.load(open(root / 'twin_weights.json', encoding='utf-8')), separators=(',', ':')).replace('</', r'<\/')

tpl = tpl.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
cut = tpl.index('</style>') + len('</style>')
head, body = tpl[:cut], tpl[cut:]
body = body.replace('__DATA__', data).replace('__MODEL__', model)

reset = '<style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>'
doc = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n' + reset + '\n' + head + '\n</head>\n<body>' + body + '\n</body>\n</html>\n')

out = root / 'site' / 'jumeau_roulements.html'
out.write_text(doc, encoding='utf-8', newline='\n')
print(f'{out.relative_to(root)} généré ({len(doc) / 1e6:.2f} Mo)')
