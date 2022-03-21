import urllib.request
from osgeo import ogr, osr
import time
import json
import os,os.path

def GSVMetadataCollector(input_shapefile, num, output_text_folder, api_key):
    
    if not os.path.exists(output_text_folder): #Stworzenie folderu jeśli nie istnieje
        os.makedirs(output_text_folder)

    # Warstwa wyciągnięta z pliku shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(input_shapefile)
    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(sourceProj, targetProj)

    feature = layer.GetNextFeature()
    feature_num = layer.GetFeatureCount()
    batch = int(feature_num/num)
    print(batch)
    for b in range(batch):
        start = b*num
        end = (b+1)*num
        if end > feature_num:
            end = feature_num

        output_text_file = 'Pnt_start%s_end%s.json'%(start,end)
        output_GSV_file = os.path.join(output_text_folder,output_text_file)

        # pomija istniejące pliki txt
        if os.path.exists(output_GSV_file):
            continue

        time.sleep(1) # Opóźnienie co 1 sekundę

        with open(output_GSV_file, 'w') as pano_info_text:
            for i in range(start, end):
                r_json = {}
                feature = layer.GetFeature(i)
                geom = feature.GetGeometryRef()
                geom.Transform(transform)
                x = geom.GetX()
                y = geom.GetY()

                # Wyszukiwanie w Google Street View
                url = 'https://maps.googleapis.com/maps/api/streetview/metadata?location=%s,%s&key=%s'%(x,y,api_key)
                print(url)
                # Pobieranie danych z Google Street View
                response = urllib.request.urlopen(url).read()
                response = json.loads(response)

                r_json["panoDate"] = response.get('date')
                r_json["panoId"] = response.get('pano_id')
                r_json["panoLat"] = response.get('location').get('lat')
                r_json["panoLon"] = response.get('location').get('lng')

                print(r_json)
                json.dump(r_json, pano_info_text)
        
        pano_info_text.close()


if __name__ == "__main__":
    import os, os.path
    
    root = 'data'
    inputShp = os.path.join(root,'poznan_ulice_pts.shp')
    outputTxt = root+'/json_files'
    api_key = 'hidden'
    
    GSVMetadataCollector(inputShp, 1,outputTxt, api_key)
