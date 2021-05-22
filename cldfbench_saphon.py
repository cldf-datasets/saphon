from collections import OrderedDict, defaultdict
from pathlib import Path
from unidecode import unidecode
import unicodedata

from cldfbench import CLDFSpec
from cldfbench import Dataset as BaseDataset
from clldutils.misc import slug
from clldutils.path import git_describe

from cldfbench.datadir import get_url

from pyglottolog import Glottolog
from pyclts import CLTS, models
from pycldf.sources import Sources
from pycldf.terms import Terms

from cldfcatalog.config import Config
from collections import defaultdict
from tqdm import tqdm as progressbar
from clldutils.text import split_text_with_context, strip_brackets

import re
import html


URL = "http://linguistics.berkeley.edu/~saphon/en/inv/{0}.html"



def compute_id(text):
    """
    Returns a codepoint representation to an Unicode string.
    """

    unicode_repr = "".join(["u{0:0{1}X}".format(ord(char), 4) for char in text])

    label = slug(unidecode(text))

    return "%s_%s" % (label, unicode_repr)


def normalize_grapheme(text):
    """
    Apply simple, non-CLTS, normalization.
    """

    new_text = unicodedata.normalize("NFD", text)

    if new_text[0] == "(" and new_text[-1] == ")":
        new_text = new_text[1:-1]

    new_text = strip_brackets(new_text)
    if new_text:
        return new_text

def parse_inventories(data):
    
    inv = []
    tables = re.findall('<table class=inv>(.*?)</table>', data, re.DOTALL)

    for table in tables:
        cells = re.findall("<td>(.*?)</td>", table)
        for cell in cells:
            sounds = cell.split('&nbsp')
            for sound in sounds:
                if sound:
                    inv += [sound]
    bib = re.findall("<div class=key>Bibliography</div>.*?<div class=value>"
            ".*?<p>(.*?)</p>", data, re.DOTALL)
    return inv, html.unescape(" ".join(bib))

class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "saphon"

    def cldf_specs(self):
        return CLDFSpec(
                module='StructureDataset',
                dir=self.cldf_dir,
                data_fnames={'ParameterTable': 'features.csv'}
            )
        
    def cmd_download(self, args):
        invs, bibs = [], []
        clts_path = Path.home() / ".config" / "cldf" / "clts"
        clts = CLTS(clts_path)
        for language in self.etc_dir.read_csv("languages.tsv", delimiter="\t", dicts=True):
            args.log.info("parsing language data for {0}".format(language["Name"]))
            data = open(self.raw_dir.joinpath("languages", language["ID"]+".html"
                ).as_posix()).read()
            #data = get_url(URL.format(language["ID"])).text
            #with open("raw/languages/{0}.html".format(language["ID"]), "w") as f:
            #    f.write(data)
            inv, bib = parse_inventories(data)
            for sound in inv:
                invs += [[language, sound]]
                features[sound] += 1
            bibs += [bib]
            args.log.info("found {0} sounds".format(len(inv)))
            args.log.info("bibliography: {0}".format(bib))
        with open(self.raw_dir.joinpath("inventories.tsv").as_posix(), "w") as f:
            for language, sound in invs:
                f.write("\t".join([language["ID"], sound])+"\n")
        with open(self.raw_dir.joinpath("bibliography.txt").as_posix(), "w") as f:
            for bib in bibs:
                f.write(bib.replace("\n", " ")+"\n")

    def cmd_makecldf(self, args):

        # Add sources
        sources = Sources.from_file(self.raw_dir / "sources.bib")
        args.writer.cldf.add_sources(*sources)

        glottolog = Glottolog(args.glottolog.dir)
        clts = CLTS(Config.from_file().get_clone('clts'))
        bipa = clts.bipa
        clts_saphon = clts.transcriptiondata_dict['saphon']

        # Add components
        args.writer.cldf.add_columns(
            "ValueTable",
            {"name": "Value_in_Source", "datatype": "string"})
        
        cltstable = Terms()["cltsReference"].to_column().asdict()
        cltstable["datatype"]["format"] = "[a-z_-]+|NA"
        args.writer.cldf.add_columns(
                    'ParameterTable',
                    cltstable,
                    {'name': 'CLTS_BIPA', 'datatype': 'string'},
                    {'name': 'CLTS_Name', 'datatype': 'string'})
        args.writer.cldf.add_component(
            "LanguageTable", "Family", "Glottolog_Name")

        languages = []
        #all_glottolog = {lng.id: lng for lng in glottolog.languoids()}
        #iso2glot = {lng.iso: lng.glottocode for lng in all_glottolog.values()}
        #args.log.info("loaded glottolog")
        for row in progressbar(
                self.etc_dir.read_csv("languages.csv", dicts=True)):
            #if row["SAPHON_Code"] in iso2glot:
            #    glottocode = iso2glot[row["SAPHON_Code"]]
            #elif row["SAPHON_Code"][:3] in iso2glot:
            #    glottocode = iso2glot[row["SAPHON_Code"][:3]]
            #else:
            #    glottocode = ""

            #if glottocode and glottocode in all_glottolog:
            #    lang = all_glottolog[glottocode]
            #    update = {
            #        "Family": lang.family.name if lang.family else '',
            #        "Glottocode": glottocode,
            #        "Latitude": lang.latitude,
            #        "Longitude": lang.longitude,
            #        "Macroarea": lang.macroareas[0].name if lang.macroareas else None,
            #        "Glottolog_Name": lang.name,
            #    }
            #    row.update(update)
            languages.append(row)

        # Build source map from language
        source_map = {k: v for k, v in self.raw_dir.read_csv("references.tsv",
            delimiter="\t")}

        # Parse sources
        segments = []
        values = []
        counter = 1
        unknowns = defaultdict(list)
        for lid, segment in self.raw_dir.read_csv('inventories.tsv', 
                delimiter="\t"):
            normalized = normalize_grapheme(segment)
            if normalized in clts_saphon.grapheme_map:
                sound = bipa[clts_saphon.grapheme_map[normalized]]
            else:
                sound = bipa['<NA>']
                unknowns[normalized] += [(lang_key, segment)]
            par_id = compute_id(normalized)
            if sound.type == 'unknownsound':
                bipa_grapheme = ''
                desc = ''
            else:
                bipa_grapheme = str(sound)
                desc = sound.name

            segments.append((par_id, normalized, bipa_grapheme, desc))

            values.append(
                {
                    "ID": str(counter),
                    "Language_ID": lid,
                    "Parameter_ID": par_id,
                    "Value_in_Source": segment,
                    "Value": normalized,
                    "Source": [source_map[lid]]
                }
            )
            counter += 1

        # Build segment data
        parameters = [
            {
                "ID": ID, 
                "Name": normalized,
                "Description": '',
                "CLTS_ID": desc.replace(' ', '_') if desc.strip() else "NA",
                "CLTS_BIPA": bipa_grapheme,
                "CLTS_Name": desc}
            for ID, normalized, bipa_grapheme, desc in set(segments)
        ]

        # Write data and validate
        args.writer.write(**{
                "ValueTable": values,
                "LanguageTable": languages,
                "ParameterTable": parameters,})
        for g, rest in unknowns.items():
            print('\t'.join(
                [
                    repr(g), str(len(rest)), g]))



