import fiona
import os, os.path
from shapely.geometry import shape, mapping
from shapely.ops import transform
from functools import partial
import pyproj
from fiona.crs import from_epsg
import warnings

def create_points(input_shapefile, output_shapefile: str = "output.shp", distance: int = 1000):
    type_highway = {
        'trunk_link','tertiary',
        'motorway','motorway_link',
        'steps', None, ' ',
        'pedestrian','primary', 
        'primary_link','footway',
        'tertiary_link', 'trunk',
        'secondary','secondary_link',
        'tertiary_link','bridleway','service'}
    
    # Tymczasowy plik z danymi
    root = os.path.dirname(input_shapefile)
    basename = 'base_' + os.path.basename(input_shapefile)
    temp_streets = os.path.join(root, basename)
    #Jeżeli tymczasowy plik istnieje to usuń go
    if os.path.exists(temp_streets):
        fiona.remove(temp_streets, 'ESRI Shapefile')

    # Czyszczenie pliku usuwając drogi
    with fiona.open(input_shapefile, 'r') as source, fiona.open(temp_streets, 'w', driver='ESRI Shapefile', crs=source.crs, schema=source.schema) as dest:
        
        # Przepisanie danych z pliku wejściowego do pliku tymczasowego. Usunięcie zbędnych danych.
        for feat in source:
            try:
                highway_type = feat['properties'].get('highway', '')
                if highway_type is None:
                    key = dest.schema['properties'].keys()[0]
                    highway_type = feat['properties'][key]
                if highway_type in type_highway:
                    continue
            except:
                raise Exception('Błąd przy przetwarzaniu danych - upewnij się czy plik jest poprawny')
            
            dest.write(feat)
    schema = {
        'geometry': 'Point',
        'properties': {'id': 'int'}
    }

    # Utworzenie pliku z punktami
    with fiona.drivers():
        with fiona.open(output_shapefile, 'w', crs=from_epsg(4326), driver = 'ESRI Shapefile', schema=schema) as output:
            # Wykonuję poniższe operacje dla każdej linii (ulicy)
            for street_line in fiona.open(temp_streets):
                warnings.filterwarnings('ignore')
                print(f'Przetwarzam każdą ulicę')
                first_shape = shape(street_line['geometry'])
                
                project = partial(pyproj.transform, pyproj.Proj(init='epsg:4326'), pyproj.Proj(init='epsg:3857'))
                line = transform(project, first_shape)
                # Tworzy punkt co 1000 m na odcinku od początku linii (ulicy) do końca
                for calculated_distance in range(0, int(line.length), distance): 
                    point = line.interpolate(calculated_distance)
                    project_4326 = partial(pyproj.transform, pyproj.Proj(init='epsg:3857'), pyproj.Proj(init='epsg:4326'))
                    point = transform(project_4326, point)
                    print(f'Tworzę punkt co {distance} metrów na odcinku od początku linii (ulicy) do końca. Jestem na {calculated_distance} metrze')
                    output.write(
                        {
                            'geometry': mapping(point),
                            'properties': {'id': 1}
                        }
                    )

    fiona.remove(temp_streets, 'ESRI Shapefile')
    if os.path.exists(temp_streets):
        fiona.remove(temp_streets, 'ESRI Shapefile')

if __name__ == "__main__":
    import os,os.path
    
    root = 'data'
    inshp = os.path.join(root,'poznan_ulice.shp')
    outshp = os.path.join(root,'poznan_ulice_pts.shp')
    distance = 1000
    create_points(inshp, outshp, distance)

