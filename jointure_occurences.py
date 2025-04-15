import pandas as pd

# Liste des encodages à essayer
encodings = ['utf-8', 'latin1', 'windows-1252']

# Liste des séparateurs à essayer
separators = [",", ";", "\t"]

# Fonction pour lire un fichier CSV avec différents encodages et séparateurs
def read_csv_with_encoding_and_sep(file_path):
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=sep, on_bad_lines='skip', quoting=3)
                print(f"Fichier {file_path} chargé avec succès en utilisant l'encodage : {encoding} et le séparateur : '{sep}'")
                return df
            except UnicodeDecodeError:
                print(f"Erreur avec l'encodage : {encoding} pour le fichier {file_path}")
            except pd.errors.ParserError:
                print(f"Erreur de parsing avec le séparateur : '{sep}' pour le fichier {file_path}")

# Charger les fichiers CSV avec la fonction améliorée
occurrences_total = read_csv_with_encoding_and_sep('occurrences_total_Liolia.csv')
selection_villes = pd.read_csv("selection_intensextra_quarries_GSW_discourse_V6.csv", sep=",", encoding="utf-8")


# Supprimer les guillemets autour des valeurs dans les colonnes
occurrences_total.columns = occurrences_total.columns.str.replace('"', '').str.strip()
occurrences_total['urban_aggl'] = occurrences_total['urban_aggl'].str.replace('"', '').str.strip()
selection_villes.columns = selection_villes.columns.str.replace('"', '').str.strip()

# Fonction pour remplacer les caractères spéciaux
def normaliser_noms(nom):
    if pd.isna(nom):  # Vérifie si la valeur est NaN
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

# Appliquer la normalisation
occurrences_total['urban_aggl'] = occurrences_total['urban_aggl'].apply(normaliser_noms)
try:
    selection_villes['Urban.Aggl'] = selection_villes['Urban.Aggl'].apply(normaliser_noms)
except KeyError:
    print("La colonne 'Urban.Aggl' est introuvable dans selection_villes. Voici les colonnes disponibles :")
    print(selection_villes.columns.tolist())
    exit(1)
# Dictionnaire de correspondance
correspondance_noms = {
    "Ahmadabad": "Ahmedabad",
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
    "Phnom Penh": "Phnum Penh (Phnom Penh)",
    "Cuenca": "Cuenca (Santa Ana de los Rios de)"
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

# Fusionner les données avec une jointure gauche (left join) pour conserver toutes les lignes du premier CSV
merged_data = expanded_rows.merge(occurrences_total, left_on='Urban.Aggl', right_on='urban_aggl', how='left')

# Remplir les valeurs manquantes
merged_data['total_occurrencesv2'] = merged_data['total_occurrencesv2'].fillna(0)
merged_data['occurrencesv2'] = merged_data['occurrencesv2'].fillna(0)

# Sommer les occurrences pour chaque agglomération avant de regrouper
merged_data['total_occurrencesv2'] = merged_data.groupby('Urban.Aggl')['total_occurrencesv2'].transform('sum')

# Conserver uniquement la première ligne de chaque agglomération
selection_villes_final = merged_data.drop_duplicates(subset='Urban.Aggl')

# Réorganiser les colonnes pour placer celles de occurrences_total à la fin
columns_order = [col for col in selection_villes.columns if col != 'Urban.Aggl'] + ['Urban.Aggl'] + ['occurrencesv2', 'total_occurrencesv2']
selection_villes_final = selection_villes_final[columns_order]

# Afficher le résultat
print(selection_villes_final)

# Enregistrer le résultat en CSV avec encodage UTF-8
selection_villes_final.to_csv('selection_intensextra_quarries_GSW_discourse_V7.csv', index=False, encoding='utf-8')

# Relire le fichier enregistré
selection_villes_final = pd.read_csv('selection_intensextra_quarries_GSW_discourse_V7.csv', encoding='utf-8')

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

# Fonction pour sommer les occurrences et réunir les agglomérations
def reunir_agglomerations(df, agglomerations):
    # Sommer les occurrences pour chaque agglomération
    for agglom, villes in agglomerations.items():
        for ville in villes[1:]:  # Commencer à partir de la deuxième ville
            if ville in df['Urban.Aggl'].values:
                # Sommer les occurrences dans la première ligne de l'agglomération
                df.loc[df['Urban.Aggl'] == villes[0], 'total_occurrencesv2'] += df.loc[df['Urban.Aggl'] == ville, 'total_occurrencesv2'].values[0]
                # Supprimer la ligne de la ville
                df = df[df['Urban.Aggl'] != ville]

    # Réunir les agglomérations
    for agglom, villes in agglomerations.items():
        df.loc[df['Urban.Aggl'] == villes[0], 'Urban.Aggl'] = agglom

    return df

# Appliquer la fonction pour réunir les agglomérations
selection_villes_final = reunir_agglomerations(selection_villes_final, agglomerations)

# Afficher le résultat final
print(selection_villes_final)

# Enregistrer le résultat final en CSV avec encodage UTF-8
selection_villes_final.to_csv('selection_intensextra_quarries_GSW_discourse_V7.csv', index=False, encoding='utf-8')

# Log des villes du corpus sans correspondance dans la sélection
villes_sans_correspondance = occurrences_total[~occurrences_total['urban_aggl'].isin(selection_villes['Urban.Aggl'])]
if not villes_sans_correspondance.empty:
    print("Villes du corpus sans correspondance dans la sélection :")
    print(villes_sans_correspondance)
else:
    print("Toutes les villes du corpus ont une correspondance dans la sélection.")
