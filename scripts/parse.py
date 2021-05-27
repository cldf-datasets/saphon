import pycldf
import json

saphon = pycldf.Dataset.from_metadata('../cldf/StructureDataset-metadata.json')

D = {}

with open("data.tsv", "w") as f:
    f.write("\t".join([
        "Language",
        "Glottocode",
        "Latitude",
        "Longitude",
        "Sounds",
        "Consonants",
        "Vowels",
        "Diphthongs",
        "NasalVowels",
        "LongVowels",
        "AllConsonants",
        "AllVowels",
        "AllDiphthongs"])+"\n")
    for sound in saphon.objects("ParameterTable"):
        try:
            D["bipa-"+sound.data["CLTS_BIPA"]] = sound.data["CLTS_Name"]
        except:
            pass
    for language in saphon.objects("LanguageTable"):
        print("language {0}".format(language.name))
        sounds = [(
            val.parameter.data["Name"],
            val.parameter.data["CLTS_BIPA"] or "",
            val.parameter.data["CLTS_Name"] or ""
            ) for val in language.values]
        if sounds:
            if language.data["Glottocode"]:
                if language.data["Glottocode"] not in D:
                    D[language.data["Glottocode"]] = []
                D[language.data["Glottocode"]] += [{
                        "ID": language.id,
                        "Dataset": "saphon",
                        "Name": language.name,
                        "Source": "",
                        "CLTS": {n: k or '?' for n, k, x in sounds},
                        "Sounds": [n for n, k, x in sounds]
                        }]

            consonants = [sound for n, sound, name in sounds if
                (name and name.endswith("consonant"))]
            vowels = [sound for n, sound, name in sounds if (
                name and name.endswith("vowel"))]
            diphthongs = [sound for n, sound, name in sounds if
                    (name and name.endswith('diphthong'))]
            nasals = [sound for n, sound, name in sounds if "nasal" in name and
                    ((name and name.endswith("vowel")) or (name and
                        name.endswith("diphthong")))]
            longs = [sound for n, sound, name in sounds if "long" in name and
                    ((name and name.endswith("vowel")) or (name and
                        name.endswith("diphthong")))]        

            f.write("\t".join(
                [
                    language.name,
                    language.data['Glottocode'] or '',
                    str(language.data['Latitude'] or ''),
                    str(language.data['Longitude'] or ''),
                    str(len(consonants+vowels+diphthongs)),
                    str(len(consonants)),
                    str(len(vowels)),
                    str(len(diphthongs)),
                    str(len(nasals)),
                    str(len(longs)),
                    " ".join(consonants),
                    " ".join(vowels),
                    " ".join(diphthongs)
                    ])+"\n")
        else:
            print('[!] no values for language {0}'.format(language.name))

with open("data.js", "w") as f:
    f.write("var DATA = "+json.dumps(D, indent=2)+";")
