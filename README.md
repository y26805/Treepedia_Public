# Treepedia
Developed by the MIT [Senseable City Lab](https://senseable.mit.edu/), *Treepedia* aims to raise a proactive awareness of urban vegetation improvement, using computer vision techniques applied to Google Street View images. Our focus is on street trees: Treepedia doesn't map parks, as GSV doesn't venture into them as it does on average streets.

*Treepedia* measures and maps the amount of vegetation cover along a city's streets by computing the Green View Index (GVI) on Google Street View (GSV) panoramas. This method considers the obstruction of tree canopies and classifies the images accordingly. The GVI presented here is on a scale of 0-100, showing the percentage of canopy coverage of a particular location. Explore the maps on the [*Treepedia*](http://senseable.mit.edu/treepedia/) website to see how the GVI changes across a city, and how it compares across cities and continents.

The following repo provides a <a href="https://github.mit.edu/abdulhai/Treepedia/wiki/Analyze-Your-City"> library to implement the GVI computation</a> for a city or region defined by a boundary shapefile, given that GSV imagery is available for the street network within it. It also includes documentation of the workflow of the project so that stakeholders, municipalities, researchers or public alike may run the analysis for their cities. We will continue to grow the *Treepedia* database to span cities all over the globe. What does your green canopy look like? If you'd like to answer this question please install this python library and run the analysis for your area. 

If you are a government, researcher or stakeholder that has used this library to compute the GVI for your city and would like us to include a mapping of it on the *Treepedia* website, please contact us at: senseable-trees@mit.edu

<br />

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/img.jpg">
</p>

# Pre-requisites
- Python 3.
You can check your python version by running the following in the Terminal.
```
python3 --version
```

- Homebrew, for Mac users. Installation guide [here](https://brew.sh)

- Google Maps API key(s)


# Workflow 

The project has the following workflow:

## Step 0: Clone and install dependencies
- Clone the repository by running the following.
```
git clone https://github.com/y26805/Treepedia_Public.git
```
- Create a virtual environment and activate it.
```
python3 -m venv ~/.Treepedia_Public
source ~/.Treepedia_Public/bin/activate
```
- Install dependencies.
```
# required for Matplotlib
brew install pkg-config freetype 

# required for Fiona
brew install gdal 
pip3 install GDAL==$(gdal-config --version | awk -F'[.]' '{print $1"."$2}')

# move into repository and install remaining dependencies using pip
cd Treepedia_Public
pip3 install -r requirements.txt
```

## Step 1: Point Sampling on Street Network of City 
With the street network and boundary shapefile for your city as input, a shapefile containing points every 20m (which can be changed depending on the size of the city) will be generated to be fed into the Google API to retrieve Google Street View Images. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img2.jpg">
</p>

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img1.jpg">
</p>

Note that spatial files must be in the projected WGS84 system.

```
python3 Treepedia/createPoints.py
```

This function accepts three parameters: input shapefile name (`inoutShp`), output shapefile name (`outputShp`) and minimum distance (`mini_dist`).

In the [example code](https://github.com/y26805/Treepedia_Public/blob/cb806860ca85cf0a8db0805191153d4e3a93d446/Treepedia/createPoints.py#L109-L114), input shape file is the `CambridgeStreet_wgs84.shp` file in the `sample-spatialdata` folder. Output file is named `Cambridge20m.shp` and the minimum distance for sampling is set to `20` meters. 


## Step 2: Metadata containing GSV panoID's

With the shapefile as input, metadata containing the panoID, panoDate, latitude, longitude and tilt specifications for the image will be stored in textfiles to be later used to calculate the Green View Index. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img3.jpg">
</p>

```
python3 Treepedia/metadataCollector.py
```

This function accepts three parameters: input shapefile name (`inputShp`), metadata output folder (`outputTxtFolder`) and batch size (`batchNum`).

In the [example code](https://github.com/y26805/Treepedia_Public/blob/cb806860ca85cf0a8db0805191153d4e3a93d446/Treepedia/metadataCollector.py#L104-L111), input shape file is the `CambridgeStreet_wgs84.shp` file in the `sample-spatialdata` folder. Output folder is named `metadata` and the batch size is set to `1000`, which means the code will save metadata of every 1000 point to a txt file.

You can generate your own sample sites based on the `createPoints.py` (Step 1) and specify a different sample site file. 



## Step 3: GVI Calculation of points with final shapefile display 
Using Otsu's method and the pymeanshift package, the Green View Index is computed for all 6 images at each sampling point; for each sampling point the GVI values are then averaged to provide a single GVI value for every point along the street network. Finally, a shapefile will be generated containing all attributes, including the GVI, of the points on the street network. 

<p align="center">
  <img width="460" height="300" src="https://github.com/ianseifs/Treepedia_Public/blob/master/images/img4.jpg">
</p>

```
python3 Treepedia/GreenView_Calculate.py
```

This function accepts four parameters: input folder containing metadata (`GSVinfoRoot`), output folder path (`outputTxtPath`), `greenmonth` and key file (`key_file`).

The [example code](https://github.com/y26805/Treepedia_Public/blob/cb806860ca85cf0a8db0805191153d4e3a93d446/Treepedia/GreenView_Calculate.py#L297-L310) is the collected metadata of GSV. By reading the metadata, this code will collect GSV images and segment the greenery, and calculate the green view index. Considering those GSV images captured in winter are leafless, which are not suitable for the analysis. You also need to specify the green season, for example, in Cambridge, the green months are May, June, July, August, and September.

You can open several process to run this code simutaniously, because the output will be saved as txt files in folder. If the output txt file is already there, then the code will move to the next metadata txt file and generate the GVI for next 1000 points.

## Step 4: Convert output to shapefile (Optional)

After finishing the computing, you can run the code of "Greenview2Shp.py" [here](https://github.com/ianseifs/Treepedia_Public/blob/master/Treepedia/Greenview2Shp.py), and save the result as shapefile, if you are more comfortable with shapefile.

```
python3 Treepedia/Greenview2Shp.py
```


# Contributors
Project Co-Leads: Xiaojiang Li and Ian Seiferling

Researchers: Bill Cai, Marwa Abdulhai

Website and Visualization: Wonyoung So
