"""Assemble le jumeau numérique (classification d'anomalies) : gabarit + données -> site/jumeau_roulements.html

Les données (twin_data.json) viennent de prep_twin_data.py :
    python classification/prep_twin_data.py classification/bearing_features_labels_2nd_test.csv classification/twin_data.json
Puis :
    python classification/build_jumeau.py
"""
import pathlib

here = pathlib.Path(__file__).resolve().parent
tpl = (here / 'jumeau_template.html').read_text(encoding='utf-8')
data = (here / 'twin_data.json').read_text(encoding='utf-8').replace('</', r'<\/')

tpl = tpl.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
cut = tpl.index('</style>') + len('</style>')
head, body = tpl[:cut], tpl[cut:]
body = body.replace('__DATA__', data)
body = body.replace('<h1>Jumeau numérique des roulements</h1>',
                    '<a class="home" href="./">← Accueil</a>\n      <h1>Jumeau numérique des roulements</h1>')

reset = '<style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>'
extra = '<style>.home{display:inline-block;margin-bottom:6px;color:var(--ink-2);font-size:13px;text-decoration:none}.home:hover{color:var(--ink)}</style>'
doc = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       '<meta name="robots" content="noindex, nofollow">\n' + reset + '\n' + head + '\n' + extra + '\n</head>\n<body>' + body + '\n</body>\n</html>\n')

out = here.parent / 'site' / 'jumeau_roulements.html'
out.write_text(doc, encoding='utf-8', newline='\n')
print(f'{out.relative_to(here.parent)} généré ({len(doc) / 1e3:.0f} Ko)')
