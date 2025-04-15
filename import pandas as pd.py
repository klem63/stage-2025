import pandas as pd
import re

# ----------------------------- #
# 1. FONCTION DE NORMALISATION #
# ----------------------------- #
def normaliser_noms(nom):
    if pd.isna(nom):
        return nom
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a', 'ă': 'a', 'ã': 'a', 'å': 'a', 'á': 'a',
        'î': 'i', 'ï': 'i', 'ì': 'i', 'í': 'i',
        'ô': 'o', 'ö': 'o', 'ò': 'o', 'õ': 'o', 'ø': 'o', 'ó': 'o', 'ố': 'o', 'ồ': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u', 'ú': 'u',
        'ç': 'c',
        'ñ': 'n',
        'ý': 'y', 'ÿ': 'y',
        'š': 's', 'ś': 's', 'ş': 's', 'ș': 's',
        'ž': 'z', 'ź': 'z',
        'č': 'c',
        'ř': 'r',
        'ď': 'd', 'đ': 'd',
        'ť': 't',
        'ľ': 'l',
        'ń': 'n',
        'ă': 'a', 'ą': 'a',
        'ğ': 'g',
        'ł': 'l',
        'ő': 'o', 'œ': 'oe',
        'ŕ': 'r',
        'ů': 'u',
        'ż': 'z'
    }
    for char, repl in replacements.items():
        nom = nom.replace(char, repl)
    return nom

# ----------------------------- #
# 2. CHARGEMENT ET NETTOYAGE   #
# ----------------------------- #
# Lire le corpus
corpus = pd.read_csv("corpus_gravieresv2.csv")

# Normaliser les noms de villes
corpus['urban_aggl'] = corpus['urban_aggl'].astype(str).apply(normaliser_noms)

# ----------------------------- #
# 3. COMPTER LES OCCURRENCES   #
# ----------------------------- #

# 3.1 Nombre de lignes (documents) par ville
occurrences = corpus['urban_aggl'].value_counts().reset_index()
occurrences.columns = ['urban_aggl', 'occurrencesv2']

# 3.2 Nombre de mentions de mots-clés d’extraction dans la colonne text_en
mots_cles = [
    'quarry', 'gravel pit', 'sand pit', 'sand mining', 'gravel mining', 'gravel mine', 'sand mine', 'quarries', 'quarrying',
    'sand', 'gravel', 'clay', 'sand dredging', 'gravel dredging', 'sand extraction', 'sand quarry', 'gravel extraction', 'gravel quarry', 'clay mining', 'clay mine', 'clay extraction', 'clay quarry', 'clay pit'
]

# Isoler les textes liés à Oujda
texts_oujda = corpus[corpus['urban_aggl'] == 'Oujda']['text_en'].dropna().str.lower()

# Compter les occurrences de chaque mot-clé
from collections import Counter

counter = Counter()
for text in texts_oujda:
    for mot in mots_cles:
        counter[mot] += len(re.findall(r'\b' + re.escape(mot) + r'\b', text))

print("Mots-clés les plus fréquents pour Oujda :")
print(counter.most_common())

texts_oujda.to_csv("texts_oujda.csv", index=False)