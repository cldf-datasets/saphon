import pycldf

saphon = pycldf.Dataset.from_metadata('../cldf/StructureDataset-metadata.json')

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
    for language in saphon.objects("LanguageTable"):
        print("language {0}".format(language.name))
        sounds = [(
            val.parameter.data["CLTS_BIPA"],
            val.parameter.data["CLTS_Name"]
            ) for val in language.values if val.parameter.data["CLTS_BIPA"]]
        if sounds:
            consonants = [sound for sound, name in sounds if
                    name.endswith("consonant")]
            vowels = [sound for sound, name in sounds if name.endswith("vowel")]
            diphthongs = [sound for sound, name in sounds if
                    name.endswith('diphthong')]
            nasals = [sound for sound, name in sounds if "nasal" in name and
                    (name.endswith("vowel") or name.endswith("diphthong"))]
            longs = [sound for sound, name in sounds if "long" in name and
                    (name.endswith("vowel") or name.endswith("diphthong"))]        

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

