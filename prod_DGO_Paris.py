import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Polygon, Point
from shapely.affinity import rotate, translate
from shapely.ops import split, nearest_points, substring
import os

# === PARAMÈTRES ===
transect_spacing = 20  # en mètres
transect_length = 10000  # longueur totale des transects (10000 m de chaque côté)
output_path = "dgo_output.shp"

# === CHARGEMENT DES DONNÉES ===
centerline = gpd.read_file("centerline_paris.shp")
plaine_amont_aval = gpd.read_file("study_area_amont_aval_paris.shp")
plaine_complete = gpd.read_file("study_area_global_reach_paris_grouped.shp")

print("CRS centerline :", centerline.crs)
print("CRS plaine amont-aval :", plaine_amont_aval.crs)
print("CRS plaine complète :", plaine_complete.crs)




# Harmonisation des CRS
# On choisit un CRS projeté en mètres 
target_crs = "EPSG:2154" 
centerline = centerline.to_crs(target_crs)
plaine_amont_aval = plaine_amont_aval.to_crs(target_crs)
plaine_complete = plaine_complete.to_crs(target_crs)

# Fusion en une seule géométrie
centerline_geom = centerline.geometry.union_all()
plaine_amont_aval_geom = plaine_amont_aval.geometry.union_all()
plaine_complete_geom = plaine_complete.geometry.union_all()

print("Distance centerline <-> plaine_amont_aval :", centerline_geom.distance(plaine_amont_aval_geom))

# === ÉTAPE 1 : Créer des transects perpendiculaires ===
line = centerline_geom
distances = np.arange(0, line.length, transect_spacing)
points = [line.interpolate(d) for d in distances]

def get_transect(pt_idx):
    if pt_idx <= 0 or pt_idx >= len(points) - 1:
        return None
    p1, p2 = points[pt_idx - 1], points[pt_idx + 1]
    dx, dy = p2.x - p1.x, p2.y - p1.y
    perp = (-dy, dx)
    norm = np.hypot(perp[0], perp[1])
    ux, uy = (perp[0] / norm, perp[1] / norm)
    half = transect_length / 2
    return LineString([
        (points[pt_idx].x - ux * half, points[pt_idx].y - uy * half),
        (points[pt_idx].x + ux * half, points[pt_idx].y + uy * half)
    ])

transects = [get_transect(i) for i in range(1, len(points) - 1)]
transects = [t for t in transects if t is not None]

# Export de quelques transects pour vérification
debug_transects = gpd.GeoDataFrame(geometry=transects[:50], crs=centerline.crs)
debug_transects.to_file("debug_transects.shp")

# === ÉTAPE 2 : Calcul des largeurs locales ===
largeurs = []
positions = []
for i, t in enumerate(transects):
    inter = t.intersection(plaine_amont_aval_geom)
    if not inter.is_empty:
        largeur = inter.length
        largeurs.append(largeur)
        positions.append(distances[i+1])  # +1 car décalage de l’indice

largeur_moyenne = np.mean(largeurs)
surface_ideale = largeur_moyenne ** 2

if not largeurs:
    raise ValueError("Aucune largeur mesurée : vérifier les CRS ou l'emplacement des transects.")

print(f"{len(transects)} transects générés")
print(f"{len(largeurs)} transects intersectent la plaine amont-aval")

# === Interpolation des largeurs le long de la centerline ===
def interp_largeur(d):
    return np.interp(d, positions, largeurs, left=largeurs[0], right=largeurs[-1])

print(f"Largeur moyenne estimée : {largeur_moyenne:.2f} m")
print(f"Surface idéale : {surface_ideale:.2f} m²")

# === ÉTAPE 3 : découpe progressive de la plaine selon l’aire ===
step = 5  # m
current_distance = 0
dgo_polygons = []
dgo_id = 1

while current_distance < line.length:
    found = False
    for l in np.arange(50, 10000, step):  # testons des longueurs croissantes
        if current_distance + l >= line.length:
            l = line.length - current_distance
        sub = substring(line, current_distance, current_distance + l)
        local_largeur = interp_largeur(current_distance + l/2)
        buffer_zone = sub.buffer(local_largeur / 2, cap_style=2) # rectangle autour du segment
        clipped = buffer_zone.intersection(plaine_complete_geom)
        if not clipped.is_empty:
            area = clipped.area
            if surface_ideale * 0.85 <= area <= surface_ideale * 1.15:
                dgo_polygons.append(clipped)
                current_distance += l
                found = True
                dgo_id += 1
                break
    if not found:
        print(f"Arrêt à {current_distance:.2f} m : aucun DGO acceptable trouvé.")
        break
            

# === EXPORT ===
dgo_gdf = gpd.GeoDataFrame({"id": range(1, len(dgo_polygons)+1)}, geometry=dgo_polygons, crs=centerline.crs)
dgo_gdf["surface_m2"] = dgo_gdf.geometry.area
dgo_gdf["longueur_m"] = [poly.length for poly in dgo_gdf.geometry]
dgo_gdf.to_file(output_path)
