import pandas as pd

# Charger les fichiers CSV
selection_villes = pd.read_csv('villes_complet_binaire_with_quarries.csv')
toutes_villes = pd.read_csv('listes_villes_geomorph_intensextra_discours_nbrquarries.csv')

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
selection_villes['nom'] = selection_villes['nom'].apply(normaliser_noms)
toutes_villes['name'] = toutes_villes['name'].apply(normaliser_noms)

# Enregistrer les résultats dans de nouveaux fichiers CSV
selection_villes.to_csv('selection_binaire_intensextra_quarries_final.csv', index=False)
toutes_villes.to_csv('selection_intensextra_discours.csv', index=False)

print("Normalisation des noms terminée. Les fichiers ont été enregistrés sous 'selection_villes_normalise.csv' et 'corpus_normalise.csv'.")
