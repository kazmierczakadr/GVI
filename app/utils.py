import json
import os,os.path
import pymeanshift as pms
import numpy as np

def graythresh(array,level):
    '''array: is the numpy array waiting for processing
    return thresh: is the result got by OTSU algorithm
    if the threshold is less than level, then set the level as the threshold
    by Xiaojiang Li
    '''
    
    import numpy as np
    
    maxVal = np.max(array)
    minVal = np.min(array)
    
#   if the inputImage is a float of double dataset then we transform the data 
#   in to byte and range from [0 255]
    if maxVal <= 1:
        array = array*255
        # print "New max value is %s" %(np.max(array))
    elif maxVal >= 256:
        array = np.int((array - minVal)/(maxVal - minVal))
        # print "New min value is %s" %(np.min(array))
    
    # turn the negative to natural number
    negIdx = np.where(array < 0)
    array[negIdx] = 0
    
    # calculate the hist of 'array'
    dims = np.shape(array)
    hist = np.histogram(array,range(257))
    P_hist = hist[0]*1.0/np.sum(hist[0])
    
    omega = P_hist.cumsum()
    
    temp = np.arange(256)
    mu = P_hist*(temp+1)
    mu = mu.cumsum()
    
    n = len(mu)
    mu_t = mu[n-1]
    
    sigma_b_squared = (mu_t*omega - mu)**2/(omega*(1-omega))
    
    # try to found if all sigma_b squrered are NaN or Infinity
    indInf = np.where(sigma_b_squared == np.inf)
    
    CIN = 0
    if len(indInf[0])>0:
        CIN = len(indInf[0])
    
    maxval = np.max(sigma_b_squared)
    
    IsAllInf = CIN == 256
    if IsAllInf !=1:
        index = np.where(sigma_b_squared==maxval)
        idx = np.mean(index)
        threshold = (idx - 1)/255.0
    else:
        threshold = level
    
    if np.isnan(threshold):
        threshold = level
    
    return threshold

def VegetationClassification(image):
    
    # use the meanshift segmentation algorithm to segment the original GSV image
    (segmented_image, labels_image, number_regions) = pms.segment(image,spatial_radius=6,
                                                     range_radius=7, min_density=40)
    
    I = segmented_image/255.0
    
    red = I[:,:,0]
    green = I[:,:,1]
    blue = I[:,:,2]
    
    # calculate the difference between green band with other two bands
    green_red_Diff = green - red
    green_blue_Diff = green - blue
    
    ExG = green_red_Diff + green_blue_Diff
    diffImg = green_red_Diff*green_blue_Diff
    
    redThreImgU = red < 0.6
    greenThreImgU = green < 0.9
    blueThreImgU = blue < 0.6
    
    shadowRedU = red < 0.3
    shadowGreenU = green < 0.3
    shadowBlueU = blue < 0.3
    del red, blue, green, I
    
    greenImg1 = redThreImgU * blueThreImgU*greenThreImgU
    greenImgShadow1 = shadowRedU*shadowGreenU*shadowBlueU
    del redThreImgU, greenThreImgU, blueThreImgU
    del shadowRedU, shadowGreenU, shadowBlueU
    
    greenImg3 = diffImg > 0.0
    greenImg4 = green_red_Diff > 0
    threshold = graythresh(ExG, 0.1)
    
    if threshold > 0.1:
        threshold = 0.1
    elif threshold < 0.05:
        threshold = 0.05
    
    greenImg2 = ExG > threshold
    greenImgShadow2 = ExG > 0.05
    greenImg = greenImg1*greenImg2 + greenImgShadow2*greenImgShadow1
    del ExG,green_blue_Diff,green_red_Diff
    del greenImgShadow1,greenImgShadow2
    
    # calculate the percentage of the green vegetation
    greenPxlNum = len(np.where(greenImg != 0)[0])
    greenPercent = greenPxlNum/(400.0*400)*100
    del greenImg1,greenImg2
    del greenImg3,greenImg4
    
    return greenPercent

def Read_GSVinfo_Text(gvi_json):

    # empty list to save the GVI result and GSV metadata
    panoIDLst = []
    panoLonLst = []
    panoLatLst = []
    greenViewLst = []
    
    # read the green view index result json files
    lines = open(gvi_json,"r")
    print(gvi_json)
    print(lines)
    for line in lines:
        line = json.loads(line)
        
        panoID = line.get("panoID")
        lon = line.get("lon")
        lat = line.get("lat")
        greenView = line.get("greenViewVal")
        
        # remove the duplicated panorama id
        if panoID not in panoIDLst:
            panoIDLst.append(panoID)
            panoLonLst.append(lon)
            panoLatLst.append(lat)
            greenViewLst.append(greenView)

    return panoIDLst,panoLonLst,panoLatLst,greenViewLst

# read the green view index files into list, the input can be file or folder
def Read_GVI_res(GVI_Res):
    
    # empty list to save the GVI result and GSV metadata
    panoIDLst = []
    panoLonLst = []
    panoLatLst = []
    greenViewLst = []
    
    # if the input gvi result is a folder
    if os.path.isdir(GVI_Res):
        all_json_files = os.listdir(GVI_Res)
        print(GVI_Res)
        for json_file in all_json_files:
            # only read the text file
            if not json_file.endswith('.json'):
                continue
            
            jsonfile_e = os.path.join(GVI_Res,json_file)

            [panoIDLst_tem,panoLonLst_tem,panoLatLst_tem,greenViewLst_tem] = Read_GSVinfo_Text(jsonfile_e)
            
            panoIDLst = panoIDLst + panoIDLst_tem
            panoLonLst = panoLonLst + panoLonLst_tem
            panoLatLst = panoLatLst + panoLatLst_tem
            greenViewLst = greenViewLst + greenViewLst_tem

    else: #for single txt file
        [panoIDLst_tem,panoDateLst_tem,panoLonLst_tem,panoLatLst_tem,greenViewLst_tem] = Read_GSVinfo_Text(jsonfile_e)


    return panoIDLst,panoLonLst,panoLatLst,greenViewLst

