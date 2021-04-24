import re
from collections import defaultdict

with open("anystyle.bib") as f:
    refs = re.findall("@.*?\n}", f.read(), re.DOTALL)
with open("bibliography.txt") as f:
    data = [ref.strip() for ref in f]
with open("../etc/languages.tsv") as f:
    langs = []
    for row in f:
        lang = row.split("\t")[0]
        langs += [lang]

B = {}
doubles = {}
for i, (lang, bib, ref) in enumerate(zip(langs[1:], refs, data)):
    key = re.findall("{.*?,", bib)[0][1:-1]
    if key in doubles:
        bib = re.sub(key, key+str(i+1), bib)
    else:
        doubles[key] = ''

    if ref in B:
        B[ref][1] += [lang]
    else:
        B[ref] = [bib, [lang]]


with open("references.tsv", "w") as f:
    for k, v in B.items():
        for lang in v[1]:
            key = re.findall("{.*?,", v[0])[0][1:-1]
            f.write(lang+"\t"+key+"\n")

with open("sources.bib", "w") as f:
    for k, v in B.items():
        f.write(v[0]+"\n\n")
    
