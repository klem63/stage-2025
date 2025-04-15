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
   'gravel pit', 'sand pit', 'clay pit', 'aggregate pit', 'sand mining', 'gravel mining', 'clay mining', 'aggregate mining', 'gravel mine', 'sand mine', 'clay mine', 'aggregate mine',
    'quarries', 'quarrying', 'quarry',
    'sand dredging', 'gravel dredging', 'clay dredging', 'aggregate dredging', 'sand extraction', 'aggregate extraction', 'sand quarry', 'aggregate quarry', 'gravel extraction',
    'gravel quarry',   'clay extraction', 'clay quarry']

def compter_mentions_extraction(text):
    if pd.isna(text):
        return 0
    text = text.lower()
    return sum(len(re.findall(r'\b' + re.escape(mot) + r'\b', text)) for mot in mots_cles)

corpus['total_mentions'] = corpus['text_en'].apply(compter_mentions_extraction)

mentions_par_ville = corpus.groupby('urban_aggl')['total_mentions'].sum().reset_index()
mentions_par_ville.columns = ['urban_aggl', 'total_occurrencesv2']

# ----------------------------- #
# 4. FUSION ET EXPORT FINAL    #
# ----------------------------- #

# Fusionner les deux types d’occurrences
df_final = pd.merge(occurrences, mentions_par_ville, on='urban_aggl', how='outer').fillna(0)

# Convertir en int
df_final['occurrencesv2'] = df_final['occurrencesv2'].astype(int)
df_final['total_occurrencesv2'] = df_final['total_occurrencesv2'].astype(int)

# Sauvegarder
df_final.to_csv("occurrences_total_Liolia.csv", index=False, encoding='utf-8')

print("✅ Fichier 'occurrences_total_Liolia.csv' généré avec succès.")
print(df_final.head())
