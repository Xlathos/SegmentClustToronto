#!/usr/bin/env python
# coding: utf-8

# <h1 align=center><font size = 5>Segmenting and Clustering Neighborhoods in Toronto </font></h1>

# <h2 ><font size = 3>1. Preparation of the data set</h2>

# 1a. Download all the dependencies that we will need.

# In[8]:


import requests
from bs4 import BeautifulSoup
import csv

import pandas as pd
import numpy as np


# 1b. Download the data from the Wikipedia site

# In[9]:


import requests #import the data 
postal_codes = requests.get('https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M').text
print('Data downloaded!')


# In[10]:


ps_soup = BeautifulSoup(postal_codes, 'lxml')#get the html


# In[29]:


table = ps_soup.find('table')#get the table in the html

table_rows = table.find_all('tr')
table_rows = table_rows[1:len(table_rows)]

l = []

for tr in table_rows:    
    td = tr.find_all('td')    
    rows = [tr.text for tr in td]
    for i,row in enumerate(rows): rows[i] = str(rows[i]).replace("\n","")
    l.append(rows)
    
df_initial = pd.DataFrame(l, columns=["Postalcode", "Borough", "Neighborhood"])
df_initial.head()


# 1b. Clean the data and create the table

# In[30]:


df_initial = df_initial.drop(df[df.Borough == "Not assigned"].index)

df_temp=df_initial.groupby('Postalcode')['Neighborhood'].apply(lambda x: "%s" % ', '.join(x))
df_temp=df_temp.reset_index(drop=False)
df_temp.rename(columns={'Neighborhood':'Neighborhood_joined'},inplace=True)

df_toronto = pd.merge(df, df_temp, on='Postalcode')
df_toronto.drop(['Neighborhood'],axis=1,inplace=True)
df_toronto.drop_duplicates(inplace=True)

df_toronto.rename(columns={'Neighborhood_joined':'Neighborhood'},inplace=True)

df_toronto.head()


# In[31]:


df_toronto.shape


# <h2 ><font size = 3>2. Get the latitude and the longitude coordinates of each neighborhood</h2>

# In[32]:


#The use of geocoder didn't produce any results thus the coordinates of each neighborhood will be taken from the csv file
df_coo=pd.read_csv('http://cocl.us/Geospatial_data')


# In[33]:


df_coo.head()


# In[34]:


df_coo.shape


# In[35]:


#append the coordinates table into the neighborhood table (part 1)
df_complete = df_merge.join(df_coo.set_index('Postal Code'), on='Postalcode')
df_complete.head()


# <h2 ><font size = 3>3. Explore and cluster the neighborhoods in Toronto</h2>

# 3a. Download dependences

# In[4]:


import json # library to handle JSON files
get_ipython().system("conda install -c conda-forge geopy --yes # uncomment this line if you haven't completed the Foursquare API lab")
from geopy.geocoders import Nominatim # convert an address into latitude and longitude values
import requests # library to handle requests
from pandas.io.json import json_normalize # tranform JSON file into a pandas dataframe
# Matplotlib and associated plotting modules
import matplotlib.cm as cm
import matplotlib.colors as colors
# import k-means from clustering stage
from sklearn.cluster import KMeans
from sklearn.datasets.samples_generator import make_blobs
get_ipython().system("conda install -c conda-forge folium=0.5.0 --yes # uncomment this line if you haven't completed the Foursquare API lab")
import folium # map rendering library


# 3b. Get the geographical coordinates of Toronto

# In[5]:


address = 'Toronto, ON, Canada'

geolocator = Nominatim(user_agent="to_explorer")
location = geolocator.geocode(address)
latitude = location.latitude
longitude = location.longitude
print('The geograpical coordinate of Toronto, ON, Canada are {}, {}.'.format(latitude, longitude))


# 3c.Create a map of Toronto with neighborhoods superimposed on top

# In[37]:


# create map of Toronto using latitude and longitude values
map_toronto = folium.Map(location=[latitude, longitude], zoom_start=10)

# add markers to map
for lat, lng, borough, neighborhood in zip(df_complete['Latitude'], df_complete['Longitude'], df_complete['Borough'], df_complete['Neighborhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [lat, lng],
        radius=5,
        popup=label,
        color='blue',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(map_toronto)  
    
map_toronto


# 3d.Start utilizing the Foursquare API to explore the neighborhoods and segment them.

# In[38]:


#Define Foursquare Credentials and Version

CLIENT_ID = '0SXB510C22CMORUTMZTNPCRSZ455UFVKXHUFVYQLAO0BR4I1' # your Foursquare ID
CLIENT_SECRET = '1AZ4J4XVVXCLSZK5DJ4IN2TJJCTD03L3HNRX5QEMKW1L2MDW' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# In[40]:


#Get the neighborhood's name
df_complete.loc[0, 'Neighborhood']
#Get the neighborhood's latitude and longitude values.
neighborhood_latitude = df_complete.loc[0, 'Latitude'] # neighborhood latitude value
neighborhood_longitude = df_complete.loc[0, 'Longitude'] # neighborhood longitude value

neighborhood_name = df_complete.loc[0, 'Neighborhood'] # neighborhood name

print('Latitude and longitude values of {} are {}, {}.'.format(neighborhood_name, 
                                                               neighborhood_latitude, 
                                                               neighborhood_longitude))


# 3e. Get the top 100 venues that are in Parkwoods within a radius of 500 meters

# In[41]:


#create the GET request URL. Name your URL url.


LIMIT = 100 # limit of number of venues returned by Foursquare API
radius = 500 # define radius
url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
    CLIENT_ID, 
    CLIENT_SECRET, 
    VERSION, 
    neighborhood_latitude, 
    neighborhood_longitude, 
    radius, 
    LIMIT)
url # display URL


# In[43]:


#Send the GET request and examine the resutls
results = requests.get(url).json()
results


# In[45]:


#Borrow the get_category_type function from the Foursquare lab.
# function that extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']


# 3f.Clean the json and structure it into a pandas dataframe.

# In[46]:


venues = results['response']['groups'][0]['items']
    
nearby_venues = json_normalize(venues) # flatten JSON

# filter columns
filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
nearby_venues =nearby_venues.loc[:, filtered_columns]

# filter the category for each row
nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)

# clean columns
nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]

nearby_venues.head()


# In[47]:


#Number of venues returned by Foursquare?
print('{} venues were returned by Foursquare.'.format(nearby_venues.shape[0]))


# 3g.Explore Neighborhoods in Toronto

# In[48]:


#create a function to repeat the same process to all the neighborhoods
def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# In[50]:


#run the above function on each neighborhood and create a new dataframe called toronto_venues.
toronto_venues = getNearbyVenues(names=df_complete['Neighborhood'],
                                   latitudes=df_complete['Latitude'],
                                   longitudes=df_complete['Longitude']
                                  )


# In[51]:


#get the size of the resulting dataframe
print(toronto_venues.shape)
toronto_venues.head()


# In[52]:


#how many venues were returned for each neighborhood
toronto_venues.groupby('Neighborhood').count()


# In[54]:


#how many unique categories can be curated from all the returned venues
print('There are {} uniques categories.'.format(len(toronto_venues['Venue Category'].unique())))


# 3h.Analyze Each Neighborhood

# In[56]:


# one hot encoding
toronto_onehot = pd.get_dummies(toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
toronto_onehot['Neighborhood'] = toronto_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [toronto_onehot.columns[-1]] + list(toronto_onehot.columns[:-1])
toronto_onehot = toronto_onehot[fixed_columns]

toronto_onehot.head()


# In[57]:


#Size of the new dataframe
toronto_onehot.shape


# In[58]:


#group rows by neighborhood and by taking the mean of the frequency of occurrence of each category
   
toronto_grouped = toronto_onehot.groupby('Neighborhood').mean().reset_index()
toronto_grouped


# In[59]:


#confirm the new size
toronto_grouped.shape


# In[60]:


#print each neighborhood along with the top 5 most common venues


num_top_venues = 5

for hood in toronto_grouped['Neighborhood']:
    print("----"+hood+"----")
    temp = toronto_grouped[toronto_grouped['Neighborhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# 3j.put analysis into a pandas dataframe

# In[61]:


#sort the venues in descending order
def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# In[62]:


#create the new dataframe and display the top 10 venues for each neighborhood
num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = toronto_grouped['Neighborhood']

for ind in np.arange(toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# <h2><font size = 3>4. Cluster Neighborhoods</h2>

# 4.1 Run k-means to cluster the neighborhood into 5 clusters

# In[75]:


# set number of clusters
kclusters = 4

toronto_grouped_clustering = toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_[0:10]


# In[76]:


#Create a new dataframe that includes the cluster as well as the top 10 venues for each neighborhood
# add clustering labels
#neighborhoods_venues_sorted.insert(0, 'Cluster Labels', kmeans.labels_)

toronto_merged = df_complete

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')



# check the last columns!
toronto_merged.head()


# In[77]:


#visualize the resulting clusters
# create map
map_clusters = folium.Map(location=[latitude, longitude], zoom_start=11)

# set color scheme for the clusters
x = np.arange(kclusters)
ys = [i + x + (i*x)**2 for i in range(kclusters)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(toronto_merged['Latitude'], toronto_merged['Longitude'], toronto_merged['Neighborhood'], toronto_merged['Cluster Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        #color=rainbow[cluster-1],
        fill=True,
        #fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# <h2><font size = 3>5.Examine Clusters</h2>

# 
# Cluster 1

# In[80]:


toronto_merged.loc[toronto_merged['Cluster Labels'] == 0, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# Cluster 2

# In[82]:


toronto_merged.loc[toronto_merged['Cluster Labels'] == 1, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# Cluster 3

# In[83]:


toronto_merged.loc[toronto_merged['Cluster Labels'] == 2, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# Cluster 4

# In[84]:


toronto_merged.loc[toronto_merged['Cluster Labels'] == 3, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# Cluster 5

# In[85]:


toronto_merged.loc[toronto_merged['Cluster Labels'] == 4, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# In[ ]:




