
from osgeo import ogr, osr
import os, os.path

from utils import Read_GVI_res

def CreatePointFeature_ogr(outputShapefile,LonLst,LatLst,panoIDlist,greenViewList,lyrname):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)

    data_source = driver.CreateDataSource(outputShapefile)
    targetSpatialRef = osr.SpatialReference()
    targetSpatialRef.ImportFromEPSG(4326)
    outLayer = data_source.CreateLayer(lyrname, targetSpatialRef, ogr.wkbPoint)
    numPnt = len(LonLst)
    if numPnt > 0:
        idField = ogr.FieldDefn('PntNum', ogr.OFTInteger)
        panoID_Field = ogr.FieldDefn('panoID', ogr.OFTString)
        greenView_Field = ogr.FieldDefn('greenView',ogr.OFTReal)
        outLayer.CreateField(idField)
        outLayer.CreateField(panoID_Field)
        outLayer.CreateField(greenView_Field)
        
        for idx in range(numPnt):
            point = ogr.Geometry(ogr.wkbPoint)

            point.AddPoint(float(LonLst[idx]),float(LatLst[idx]))
            
            featureDefn = outLayer.GetLayerDefn()
            outFeature = ogr.Feature(featureDefn)
            outFeature.SetGeometry(point)
            outFeature.SetField('PntNum', idx)
            outFeature.SetField('panoID', panoIDlist[idx])

            if len(greenViewList) == 0:
                outFeature.SetField('greenView',-999)
            else:
                outFeature.SetField('greenView',float(greenViewList[idx]))

            outLayer.CreateFeature(outFeature)
            outFeature.Destroy()

        data_source.Destroy()

    else:
        print("Nie udało się poprawnie stworzyć pliku ESRI Shapefile")

# ------------------------------Main function-------------------------------
if __name__ == "__main__":
    
    inputGVIres = r'data/spatial-data/greenViewRes'
    outputShapefile = 'data/spatial-data/shp/GreenViewRes.shp'
    lyrname = 'greenView'
    [panoIDlist,LonLst,LatLst,greenViewList] = Read_GVI_res(inputGVIres)
    CreatePointFeature_ogr(outputShapefile,LonLst,LatLst,panoIDlist,greenViewList,lyrname)
