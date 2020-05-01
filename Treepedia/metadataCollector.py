
# This function is used to collect the metadata of the GSV panoramas based on the sample point shapefile

# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT 

def GSVpanoMetadataCollector(samplesFeatureClass, ouputTextFolder, batchNum):
    '''
    This function is used to call the Google API url to collect the metadata of
    Google Street View Panoramas. The input of the function is the shpfile of the create sample site, the output
    is the generate panoinfo matrics stored in the text file
    
    Parameters: 
        samplesFeatureClass: the shapefile of the create sample sites
        batchNum: the number of sites proced every time. If batch size is 1000, the code will save metadata of every 1000 point to a txt file.
        ouputTextFolder: the output folder for the panoinfo
        
    '''
    
    import urllib
    import xmltodict
    from osgeo import ogr, osr, gdal
    import time
    import os,os.path
    import math
    
    if not os.path.exists(ouputTextFolder):
        os.makedirs(ouputTextFolder)
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if driver is None:
        print('Driver is not available.')
    
    dataset = driver.Open(samplesFeatureClass)
    if dataset is None:
        print('Could not open %s' % (samplesFeatureClass))

    layer = dataset.GetLayer()
    sourceProj = layer.GetSpatialRef()
    targetProj = osr.SpatialReference()
    targetProj.ImportFromEPSG(4326) # change the projection of shapefile to the WGS84

    # if GDAL version is 3.0 or above
    if gdal.__version__.startswith('2.') is False:
        targetProj.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        
    transform = osr.CoordinateTransformation(sourceProj, targetProj)
    
    # loop all the features in the featureclass
    feature = layer.GetNextFeature()
    featureNum = layer.GetFeatureCount()
    batch = math.ceil(featureNum/batchNum)
    
    for b in range(batch):
        # for each batch process num GSV site
        start = b*batchNum
        end = (b+1)*batchNum
        if end > featureNum:
            end = featureNum
        
        ouputTextFile = 'Pnt_start%s_end%s.txt'%(start,end)
        ouputGSVinfoFile = os.path.join(ouputTextFolder,ouputTextFile)
        
        # skip over those existing txt files
        if os.path.exists(ouputGSVinfoFile):
            continue
        
        time.sleep(1)
        
        with open(ouputGSVinfoFile, 'w') as panoInfoText:
            # process num feature each time
            for i in range(start, end):
                feature = layer.GetFeature(i)        
                geom = feature.GetGeometryRef()
                
                # trasform the current projection of input shapefile to WGS84
                #WGS84 is Earth centered, earth fixed terrestrial ref system
                geom.Transform(transform)
                lon = geom.GetX()
                lat = geom.GetY()
                
                # get the meta data of panoramas 
                urlAddress = r'http://maps.google.com/cbk?output=xml&ll=%s,%s'%(lat,lon)
                
                time.sleep(0.05)
                # the output result of the meta data is a xml object
                metaDataxml = urllib.request.urlopen(urlAddress)
                metaData = metaDataxml.read()    
                
                data = xmltodict.parse(metaData)
                
                # in case there is not panorama in the site, therefore, continue
                if data['panorama']==None:
                    continue
                else:
                    panoInfo = data['panorama']['data_properties']
                                        
                    # get the meta data of the panorama
                    panoDate = list(panoInfo.items())[4][1]
                    panoId = list(panoInfo.items())[5][1]
                    panoLat = list(panoInfo.items())[8][1]
                    panoLon = list(panoInfo.items())[9][1]
                    
                    print('The coordinate (%s,%s), panoId is: %s, panoDate is: %s'%(panoLon,panoLat,panoId, panoDate))
                    lineTxt = 'panoID: %s panoDate: %s longitude: %s latitude: %s\n'%(panoId, panoDate, panoLon, panoLat)
                    panoInfoText.write(lineTxt)
                    
        panoInfoText.close()


# ------------Main Function -------------------    
if __name__ == "__main__":
    import os, os.path
    
    os.chdir("sample-spatialdata")
    root = os.getcwd()
    inputShp = os.path.join(root,'Cambridge20m.shp')
    outputTxtFolder = os.path.join(root, "metadata_test")
    batchNum = 1000
    
    GSVpanoMetadataCollector(inputShp, outputTxtFolder, batchNum)

