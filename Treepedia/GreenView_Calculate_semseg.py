# This program is used to calculate the green view index based on the collecte metadata. The
# Object based images classification algorithm is used to classify the greenery from the GSV imgs
# in this code, the meanshift algorithm implemented by pymeanshift was used to segment image
# first, based on the segmented image, we further use the Otsu's method to find threshold from
# ExG image to extract the greenery pixels.

# For more details about the object based image classification algorithm
# check: Li et al., 2016, Who lives in greener neighborhoods? the distribution of street greenery and it association with residents' socioeconomic conditions in Hartford, Connectictu, USA

# This program implementing OTSU algorithm to chose the threshold automatically
# For more details about the OTSU algorithm and python implmentation
# cite: http://docs.opencv.org/trunk/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html


# Copyright(C) Xiaojiang Li, Ian Seiferling, Marwa Abdulhai, Senseable City Lab, MIT 
# First version June 18, 2014

import time
from PIL import Image
import numpy as np
import requests
import sys
from urllib.parse import urlencode

import os, csv, torch, scipy.io, torchvision.transforms
from mit_semseg.models import ModelBuilder, SegmentationModule
from mit_semseg.utils import colorEncode

    



def VegetationClassification(Img, segmentation_module):

    '''
    This function is used to classify the green vegetation from GSV image.
    This is based on semantic segmentation method.
    The season of GSV images were also considered in this function
        Img: the numpy array image, eg. Img = np.array(Image.open(response.raw))
        segmentation_module: the pre-configured model for semantic segmentation, eg. segmentation_module = SegmentationModule(net_encoder, net_decoder, crit)
        return the percentage of the green vegetation pixels in the GSV image
    
    By Yuki Minami
    '''
    

    # Load and normalize one image as a singleton tensor batch
    pil_to_tensor = torchvision.transforms.Compose([
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(
            mean=[0.485, 0.456, 0.406], # These are RGB mean+std values
            std=[0.229, 0.224, 0.225])  # across a large photo dataset.
    ])

    img_data = pil_to_tensor(Img)
    singleton_batch = {'img_data': img_data[None].cuda()}
    output_size = img_data.shape[1:]



    # Run the segmentation
    with torch.no_grad():
        scores = segmentation_module(singleton_batch, segSize=output_size)
        
    # Get the predicted scores for each pixel
    _, pred = torch.max(scores, dim=1)
    pred = pred.cpu()[0].numpy()

    greenIndex = {
        'treeIndex' : 4,
        'grassIndex' : 9,
        'palmIndex' : 72
    }
    greenPxlNum = 0
    
    for i in greenIndex.values():
        greenPxlNum += len(np.where(pred == i)[0])

    greenPercent = greenPxlNum/(400.0*400)*100

    return greenPercent
    

# using 18 directions is too time consuming, therefore, here I only use 6 horizontal directions
# Each time the function will read a text, with 1000 records, and save the result as a single TXT
def GreenViewComputing_ogr_6Horizon(GSVinfoFolder, outTXTRoot, greenmonth, key_file, semsegPath):
    

    '''
    This function is used to download the GSV from the information provide
    by the gsv info txt, and save the result to a shapefile

    Required modules: numpy, requests, and PIL

        GSVinfoTxt: the input folder name of GSV info txt
        outTXTRoot: the output folder to store result green result in txt files
        greenmonth: a list of the green season, for example in Boston, greenmonth = ['05','06','07','08','09']
        key_file: the API keys in txt file, each key is one row, I prepared five keys, you can replace by your owne keys if you have Google Account
        semsegPath: the path to the cloned repository from GitHub https://github.com/CSAILVision/semantic-segmentation-pytorch.git

    last modified by Yuki Minami, 23 October 2020

    '''


    
    # read the Google Street View API key files, you can also replace these keys by your own
    lines = open(key_file,"r")
    keylist = []
    for line in lines:
        key = line.rstrip()
        keylist.append(key)
    lines.close()
    
    print ('The key list is:=============', keylist)
    
    # set a series of heading angle
    headingArr = 360/6*np.array([0,1,2,3,4,5])
    
    # number of GSV images for Green View calculation, in my original Green View View paper, I used 18 images, in this case, 6 images at different horizontal directions should be good.
    numGSVImg = len(headingArr)*1.0
    pitch = 0
    
    # load model from URL
    model = load_model_from_url(semsegPath)
    print('Trained models have been successfully downloaded')
    
    # create a folder for GSV images and grenView Info
    if not os.path.exists(outTXTRoot):
        os.makedirs(outTXTRoot)
    
    
    
    # the input GSV info should be in a folder
    if not os.path.isdir(GSVinfoFolder):
        print('You should input a folder for GSV metadata')
        return
    else:
        allTxtFiles = os.listdir(GSVinfoFolder)
        for txtfile in allTxtFiles:
            if not txtfile.endswith('.txt'):
                continue
            
            txtfilename = os.path.join(GSVinfoFolder,txtfile)
            panoIDLst, panoDateLst, panoLonLst, panoLatLst = get_pano_lists_from_file(txtfilename, greenmonth)
            
            # the output text file to store the green view and pano info
            gvTxt = 'GV_'+os.path.basename(txtfile)
            GreenViewTxtFile = os.path.join(outTXTRoot,gvTxt)
            
            
            # check whether the file already generated, if yes, skip. Therefore, you can run several process at same time using this code.
            print("Processing", GreenViewTxtFile)
            if os.path.exists(GreenViewTxtFile):
                print("File already exists")
                continue
            
            # write the green view and pano info to txt            
            with open(GreenViewTxtFile,"w") as gvResTxt:
                for i in range(len(panoIDLst)):
                    panoDate = panoDateLst[i]
                    panoID = panoIDLst[i]
                    lat = panoLatLst[i]
                    lon = panoLonLst[i]
                    
                    # get a different key from the key list each time
                    idx = i % len(keylist)
                    key = keylist[idx]
                    
                    # calculate the green view index
                    greenPercent = 0.0

                    

                    for heading in headingArr:
                        print("Heading is: ",heading)
                        
                        # using different keys for different process, each key can only request 25,000 imgs every 24 hours
                        URL = get_api_url(panoID, heading, pitch, key)
                        # let the code to pause by 1s, in order to not go over data limitation of Google quota
                        time.sleep(1)
                        
                        # classify the GSV images and calcuate the GVI
                        try:
                            im = get_api_image(URL)
                            percent= VegetationClassification(im, model)
                            greenPercent = greenPercent + percent


                        # if the GSV images are not download successfully or failed to run, then return a null value
                        except:
                            print("Unexpected error:", sys.exc_info())
                            greenPercent = -1000
                            break

                    # calculate the green view index by averaging six percents from six images
                    greenViewVal = greenPercent/numGSVImg
                    print('The greenview: %s, pano: %s, (%s, %s)'%(greenViewVal, panoID, lat, lon))

                    # write the result and the pano info to the result txt file
                    lineTxt = 'panoID: %s panoDate: %s longitude: %s latitude: %s, greenview: %s\n'%(panoID, panoDate, lon, lat, greenViewVal)
                    gvResTxt.write(lineTxt)


def get_api_url(panoID, heading, pitch, key):
    params = {
        "size": "400x400",
        "pano": panoID,
        "fov": 60,
        "heading": heading,
        "pitch": pitch,
        "sensor": "false",
        "key": key,
        "source": "outdoor"
    }
    URL = "http://maps.googleapis.com/maps/api/streetview?" + urlencode(params)
    return URL


def get_api_image(url):
    response = requests.get(url, stream=True)
    im = np.array(Image.open(response.raw))
    return im


def get_pano_lists_from_file(txtfilename, greenmonth):
    lines = open(txtfilename,"r")

    # create empty lists, to store the information of panos,and remove duplicates
    panoIDLst = []
    panoDateLst = []
    panoLonLst = []
    panoLatLst = []
    
    # loop all lines in the txt files
    for line in lines:
        metadata = line.split(" ")
        panoID = metadata[1]
        panoDate = metadata[3]
        month = panoDate[-2:]
        lon = metadata[5]
        lat = metadata[7][:-1]

        # in case, the longitude and latitude are invalide
        if len(lon)<3:
            continue
        
        # only use the months of green seasons
        if month not in greenmonth:
            continue
        if panoID in panoIDLst:
            continue
        else:
            panoIDLst.append(panoID)
            panoDateLst.append(panoDate)
            panoLonLst.append(lon)
            panoLatLst.append(lat)

    lines.close()

    return panoIDLst, panoDateLst, panoLonLst, panoLatLst

    

def load_model_from_url(semsegPath):
    
    model_urls = {
        'encoder' : 'http://sceneparsing.csail.mit.edu/model/pytorch/ade20k-resnet50dilated-ppm_deepsup/encoder_epoch_20.pth',
        'decoder' : 'http://sceneparsing.csail.mit.edu/model/pytorch/ade20k-resnet50dilated-ppm_deepsup/decoder_epoch_20.pth'
    }

    if not os.path.exists(os.path.join(semsegPath, 'ckpt')):
        os.makedirs(os.path.join(semsegPath, 'ckpt'))

    r = requests.get(model_urls['encoder'])
    with open(os.path.join(semsegPath, 'ckpt/encoder.pth'), 'wb') as f:
        f.write(r.content)
    r = requests.get(model_urls['decoder'])  
    with open(os.path.join(semsegPath, 'ckpt/decoder.pth'), 'wb') as f:
        f.write(r.content)
    

    net_encoder = ModelBuilder.build_encoder(
        arch='resnet50dilated',
        fc_dim=2048,
        weights=os.path.join(semsegPath, 'ckpt/encoder.pth'))
    net_decoder = ModelBuilder.build_decoder(
        arch='ppm_deepsup',
        fc_dim=2048,
        num_class=150,
        weights=os.path.join(semsegPath, 'ckpt/decoder.pth'),
        use_softmax=True)

    crit = torch.nn.NLLLoss(ignore_index=-1)
    segmentation_module = SegmentationModule(net_encoder, net_decoder, crit)
    segmentation_module.eval()
    segmentation_module.cuda()

    return segmentation_module

    


# ------------------------------Main function-------------------------------
if __name__ == "__main__":
    
    import os,os.path
    
    os.chdir("sample-spatialdata")
    root = os.getcwd()
    GSVinfoRoot = os.path.join(root, "metadata")
    outputTextPath = os.path.join(root, "greenViewRes")
    greenmonth = ['01','02','03','04','05','06','07','08','09','10','11','12']

    os.chdir("../")
    key_file = os.path.join(os.getcwd(), 'keys.txt')

    os.chdir('../')
    semsegPath = os.path.join(os.getcwd(), 'semantic-segmentation-pytorch')
    os.chdir(os.path.join(os.getcwd(), 'Treepedia_Public'))


    
    GreenViewComputing_ogr_6Horizon(GSVinfoRoot,outputTextPath, greenmonth, key_file, semsegPath)


