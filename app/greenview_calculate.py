import os, os.path
import json
import time
from PIL import Image
import numpy as np
import requests
from io import BytesIO, StringIO
import datetime
from osgeo import ogr, osr

from utils import VegetationClassification

def GreenViewComputing_ogr_6Horizon(GSVinfoFolder, outTXTRoot, greenmonth, key):
    image_path = os.path.join(os.getcwd(), 'data/img')
    headingArr = 360/6*np.array([0,1,2,3,4,5])
    
    # Liczba zdjęć GSV do obliczenia GV
    numGSVImg = len(headingArr)*1.0
    pitch = 0
    
    # Folder dla zdjęć GSV i informacjach o GV
    if not os.path.exists(outTXTRoot):
        os.makedirs(outTXTRoot)
    

    # Sprawdza czy folder z plikami istnieje
    GSVinfoFolder = os.path.join(os.getcwd(), GSVinfoFolder)
    print(GSVinfoFolder)
    if not os.path.isdir(GSVinfoFolder):
        print('Należy wprowadzić folder dla metadanych GSV')
    else: # Jeśli folder istnieje to wczytuje pliki json z folderu
        all_json = os.listdir(GSVinfoFolder)
        for jsonfile in all_json:
            if not jsonfile.endswith('.json'):
                continue
            
            jsonfilename = os.path.join(GSVinfoFolder,jsonfile)
            lines = open(jsonfilename,"r")
            print("A")            
            # Tworzenie pustych list w celu zapisu danych
            panoIDLst = []
            panoDateLst = []
            panoLonLst = []
            panoLatLst = []
            
            # Zbiera wszystkie dane z pliku json
            for line in lines:
                data = json.loads(line)
                panoID = data.get('panoId')
                panoDate = data.get('panoDate')
                month = panoDate[5:7]
                lon = data.get('panoLon')
                lat = data.get('panoLat')
                
                print (lon, lat, month, panoID, panoDate)
                
                if month not in greenmonth:
                    continue
                else:
                    panoIDLst.append(panoID)
                    panoDateLst.append(panoDate)
                    panoLonLst.append(lon)
                    panoLatLst.append(lat)
            
            # Stworzenie pliku wyjściowego, który będzie zawierał GV
            gvJSON = 'GV_'+os.path.basename(jsonfile)
            GreenViewJSONFile = os.path.join(outTXTRoot,gvJSON)
            
            if os.path.exists(GreenViewJSONFile):
                continue
            
            # zapis pano i greenview do txt            
            with open(GreenViewJSONFile,"w") as res_text:
                for i in range(len(panoIDLst)):
                    panoDate = panoDateLst[i]
                    panoID = panoIDLst[i]
                    lat = panoLatLst[i]
                    lon = panoLonLst[i]
                    
                    # Obliczenie GVI
                    greenPercent = 0.0

                    for heading in headingArr:
                        print(heading)
                        r_json = {}
                        
                        URL = "http://maps.googleapis.com/maps/api/streetview?size=400x400&pano=%s&fov=60&heading=%d&pitch=%d&sensor=false&key=%s"%(panoID,heading,pitch, key)
                        
                        # Wstrzymanie kodu o 1s, aby nie przekroczyć limitu zapytań Google
                        time.sleep(1)
                        print(image_path+'/'+panoID+'.jpg')
                        # Klasyfikacja zdjęć GSV i obliczenie GVI
                        try:
                            
                            if os.path.isfile(image_path+'/'+panoID+'_'+str(heading)+'.jpg'):
                                img_gm = Image.open(image_path+'/'+panoID+'_'+str(heading)+'.jpg')
                            else:
                                response = requests.get(URL)
                                img_gm = Image.open(BytesIO(response.content))
                                im = np.array(img_gm)
                                img_gm.save(image_path+'/'+panoID+'_'+str(heading)+'.jpg')
                                try:
                                    percent = VegetationClassification(im)
                                    greenPercent = greenPercent + percent
                                except:
                                    greenPercent = -1000
                                    break

                        except:
                            print("COŚ NIE PRZECHODZI")
                            greenPercent = -1000
                            break

                    # Obliczenie GVI przez uśrednienie sześciu wartości procentowych z szcześciu zdjęć
                    greenViewVal = greenPercent/numGSVImg
                    r_json["greenViewVal"] = greenViewVal
                    r_json["panoID"] = panoID
                    r_json["lat"] = lat
                    r_json["lon"] = lon

                    # zapisz wynik i informacje o pano do pliku txt z wynikami
                    json.dump(r_json, res_text)
            res_text.close()


if __name__ == "__main__":
    
    import os,os.path
    import itertools
    
    GSVinfoRoot = 'data/json_files'
    outputTextPath = r'data/spatial-data/greenViewRes'
    greenmonth = ['03','04','05','06','07','08','09','10']
    key = 'HIDDEN'
    GreenViewComputing_ogr_6Horizon(GSVinfoRoot,outputTextPath, greenmonth, key)
