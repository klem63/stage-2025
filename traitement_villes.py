import pandas as pd

# Charger les fichiers CSV
selection_villes = pd.read_csv('GloUrb_global_table_discourse.csv')
corpus = pd.read_csv('corpus_gravieres_1.csv')

# Fonction pour remplacer les caractères spéciaux
def normaliser_noms(nom):
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

# Appliquer la normalisation
selection_villes['Urban.Aggl'] = selection_villes['Urban.Aggl'].apply(normaliser_noms)
corpus['urban_aggl'] = corpus['urban_aggl'].apply(normaliser_noms)

# Dictionnaire de correspondance
correspondance_noms = {
    "Beograd (Belgrade)": "Belgrade",
    "Bur Sa'id": "Bur Sa'id (Port Said)",
    "Puerto Alegre": "Porto Alegre",
    "Praha (Prague)": "Praha",
    "Roma (Rome)": "Roma",
    "Ho Chi Minh City": "Thanh Pho Ho Chi Minh (Ho Chi Minh City)",
    "Torino (Turin)": "Torino",
    "Warszawa (Warsaw)": "Warsaw",
    "Koln (Cologne)": "Koln",
    "Chi?in?u": "Chisinau",
}

# Remplacer les noms dans la sélection
selection_villes['Urban.Aggl'] = selection_villes['Urban.Aggl'].replace(correspondance_noms)

# Dictionnaire des agglomérations
agglomerations = {
    "Allentown-Bethlehem": ["Allentown", "Bethlehem"],
    "Dallas-Fort Worth": ["Dallas", "Fort Worth"],
    "Denver-Aurora": ["Denver", "Aurora"],
    "La Serena-Coquimbo": ["La Serena", "Coquimbo"],
    "Neuquen-Plottier-Cipolletti": ["Neuquen", "Plottier", "Cipolletti"],
    "Ottawa-Gatineau": ["Ottawa", "Gatineau"],
    "Reading-Wokingham": ["Reading", "Wokingham"],
    "Round Lake Beach-McHenry-Grayslake": ["Round Lake Beach", "McHenry", "Grayslake"]
}

# Fonction pour séparer les agglomérations
def separer_agglomerations(row):
    if row in agglomerations:
        return agglomerations[row]
    return [row]

# Appliquer la séparation et répéter les lignes
expanded_rows = selection_villes.loc[selection_villes.index.repeat(selection_villes['Urban.Aggl'].apply(separer_agglomerations).str.len())]

# Réassigner les valeurs correctement
expanded_rows['Urban.Aggl'] = [item for sublist in selection_villes['Urban.Aggl'].apply(separer_agglomerations) for item in sublist]

# Compter les occurrences dans le corpus
occurrences = corpus['urban_aggl'].value_counts().reset_index()
occurrences.columns = ['urban_aggl', 'occurrences']

# Fusionner avec la sélection
expanded_rows = expanded_rows.merge(occurrences, left_on='Urban.Aggl', right_on='urban_aggl', how='left')
expanded_rows['occurrences'] = expanded_rows['occurrences'].fillna(0)

# Réunir les agglomérations sans dupliquer les autres colonnes
expanded_rows['Urban.Aggl'] = expanded_rows['Urban.Aggl'].replace({v: k for k, vals in agglomerations.items() for v in vals})

# Sommer les occurrences
selection_villes_final = expanded_rows.groupby('Urban.Aggl').agg({
    'occurrences': 'sum',
    'name': 'first',  # Remplacez 'name' par le nom de vos autres colonnes
    'cluster': 'first',  # Ajoutez toutes les colonnes que vous souhaitez conserver
    'ID': 'first',
    'Country.or': 'first',
    'Continent': 'first',
    'clim': 'first',
    'clco': 'first',
    'biom': 'first',
}).reset_index()

# Renommer les villes pour retrouver leurs noms originaux
selection_villes_final['Urban.Aggl'] = selection_villes_final['Urban.Aggl'].replace({v: k for k, v in correspondance_noms.items()})

# Afficher le résultat
print(selection_villes_final)

# Enregistrer le résultat en CSV avec encodage UTF-8
selection_villes_final.to_csv('selection_villes_final.csv', index=False, encoding='utf-8')

# Log des villes du corpus sans correspondance dans la sélection
villes_sans_correspondance = corpus[~corpus['urban_aggl'].isin(selection_villes['Urban.Aggl'])]
if not villes_sans_correspondance.empty:
    print("Villes du corpus sans correspondance dans la sélection :")
    print(villes_sans_correspondance)
else:
    print("Toutes les villes du corpus ont une correspondance dans la sélection.")
