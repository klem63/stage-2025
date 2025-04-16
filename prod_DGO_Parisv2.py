import numpy as np
import shapely
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import linemerge
import geopandas as gpd
import os

# === PARAMÈTRES ===
transect_spacing = 20  # m
surface_tolerance = 0.10  # ±10% tolérance
output_path = "dgo_output_partition.shp"

# === CHARGEMENT DES DONNÉES ===
centerline = gpd.read_file("centerline_paris.shp")
plaine_amont_aval = gpd.read_file("study_area_amont_aval_paris.shp")
plaine_complete = gpd.read_file("study_area_global_reach_paris_grouped.shp")

# === HARMONISATION DU CRS ===
target_crs = "EPSG:2154"
centerline = centerline.to_crs(target_crs)
plaine_amont_aval = plaine_amont_aval.to_crs(target_crs)
plaine_complete = plaine_complete.to_crs(target_crs)

# === PRÉPARATION GÉOMÉTRIQUE ===
merged_geom = centerline.geometry.union_all()
if merged_geom.geom_type == 'LineString':
    line = merged_geom
elif merged_geom.geom_type == 'MultiLineString':
    line = linemerge(merged_geom)
    if line.geom_type == 'MultiLineString':
        line = max(line.geoms, key=lambda g: g.length)
else:
    raise ValueError(f"Type inattendu de géométrie : {merged_geom.geom_type}")

plaine_geom = plaine_complete.geometry.union_all()
plaine_amont_aval_geom = plaine_amont_aval.geometry.union_all()

# === POINTS SUR LA CENTERLINE ===
distances = np.arange(0, line.length, transect_spacing)
points = [line.interpolate(d) for d in distances]

# === FONCTION POUR LES TRANSECTS ===
def make_transect(i):
    if i <= 0 or i >= len(points) - 1:
        return None
    p1, p2 = points[i - 1], points[i + 1]
    dx, dy = p2.x - p1.x, p2.y - p1.y
    perp = (-dy, dx)
    norm = np.hypot(perp[0], perp[1])
    ux, uy = perp[0] / norm, perp[1] / norm
    half_length = 1000
    return LineString([
        (points[i].x - ux * half_length, points[i].y - uy * half_length),
        (points[i].x + ux * half_length, points[i].y + uy * half_length)
    ])

transects = [make_transect(i) for i in range(1, len(points) - 1)]
transects = [t for t in transects if t is not None]

# === CRÉATION DES CELLULES ENTRE TRANSECTS SUCCESSIFS ===
cellules = []
for i in range(len(transects) - 1):
    cutter = Polygon([
        *transects[i].coords[::-1],
        *transects[i + 1].coords
    ])

    # Nettoyage des géométries pour éviter les erreurs topologiques
    if not cutter.is_valid:
        cutter = cutter.buffer(0)
    if not plaine_geom.is_valid:
        plaine_geom = plaine_geom.buffer(0)

    # Intersection sécurisée
    clipped = plaine_geom.intersection(cutter)

    if not clipped.is_empty:
        if isinstance(clipped, (Polygon, MultiPolygon)):
            cellules.append(clipped)
        elif isinstance(clipped, GeometryCollection):
            polys = [g for g in clipped.geoms if isinstance(g, (Polygon, MultiPolygon))]
            if polys:
                cellules.append(shapely.union_all(polys))
                
# === CALCUL DE LA SURFACE IDÉALE ===
transects_amont_aval = [t for t in transects if not t.intersection(plaine_amont_aval_geom).is_empty]
largeurs = [t.intersection(plaine_amont_aval_geom).length for t in transects_amont_aval]
surface_ideale = np.mean(largeurs) ** 2

# === AGGRÉGATION DES CELLULES EN DGO ===
dgo_polygons = []
temp_group = []
accum_area = 0
for cell in cellules:
    temp_group.append(cell)
    accum_area += cell.area
    if surface_ideale * (1 - surface_tolerance) <= accum_area <= surface_ideale * (1 + surface_tolerance):
        dgo_polygons.append(shapely.union_all(temp_group))
        temp_group = []
        accum_area = 0

# === EXPORT FINAL ===
dgo_gdf = gpd.GeoDataFrame({
    "id": range(1, len(dgo_polygons) + 1),
    "surface_m2": [p.area for p in dgo_polygons],
    "longueur_m": [p.length for p in dgo_polygons]
}, geometry=dgo_polygons, crs=target_crs)

dgo_gdf.to_file(output_path)
print("Export terminé.")