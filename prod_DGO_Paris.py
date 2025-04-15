import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Polygon, Point
from shapely.affinity import rotate, translate
from shapely.ops import split, nearest_points
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

def get_perpendicular_transect(pt_idx):
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

transects = [get_perpendicular_transect(i) for i in range(1, len(points) - 1)]
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

# === ÉTAPE 3 : Création des DGO ===
dgo_polygons = []

for d in np.arange(0, line.length, 1):
    largeur_local = interp_largeur(d)
    longueur_local = surface_ideale / largeur_local

    pt = line.interpolate(d)
    tangent = line.interpolate(d + 1).coords[0] if d + 1 < line.length else line.interpolate(d - 1).coords[0]
    dx = tangent[0] - pt.x
    dy = tangent[1] - pt.y
    angle = np.degrees(np.arctan2(dy, dx))

    # Rectangle centré sur (0,0)
    half_l, half_w = longueur_local / 2, largeur_local / 2
    base = Polygon([
        (-half_l, -half_w),
        (-half_l, half_w),
        (half_l, half_w),
        (half_l, -half_w)
    ])
    # Rotation et déplacement
    rotated = rotate(base, angle, origin=(0, 0), use_radians=False)
    moved = translate(rotated, pt.x, pt.y)

    # Intersection avec la plaine complète
    dgo_final = moved.intersection(plaine_complete_geom)
    if not dgo_final.is_empty:
        dgo_polygons.append(dgo_final)

# === SAUVEGARDE DES DGO EN SHAPEFILE ===
dgo_gdf = gpd.GeoDataFrame(geometry=dgo_polygons, crs=centerline.crs)
dgo_gdf["id"] = range(1, len(dgo_gdf) + 1)
dgo_gdf.to_file(output_path)




