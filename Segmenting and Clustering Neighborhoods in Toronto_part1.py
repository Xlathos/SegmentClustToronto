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


# In[ ]:




