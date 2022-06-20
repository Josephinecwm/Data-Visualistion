#!/usr/bin/env python
# coding: utf-8

# In[20]:


#libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.patches import Patch
from collections import Counter
import geopandas as gp
from geopy.geocoders import Nominatim
import statsmodels.api as sm
import contextily as cx
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib import rc
from matplotlib.lines import Line2D
import geojson


# In[2]:


#read file
df = pd.read_csv("BasicCompanyDataAsOneFile-2021-11-01.csv")
df.set_index("CompanyName", inplace=True)


# In[3]:


# set the context of analysis
#SIC code
df = df.loc[df["SICCode.SicText_1"].notnull()]

#2 digit sic codes
df.loc[:, "Sic1_twod"] = df["SICCode.SicText_1"].str[0:2]
df.loc[:, "Sic2_twod"] = df["SICCode.SicText_2"].str[0:2]
df.loc[:, "Sic3_twod"] = df["SICCode.SicText_3"].str[0:2]
df.loc[:, "Sic4_twod"] = df["SICCode.SicText_4"].str[0:2]

#filter out companies that operate in hospitality sector - SIC code first two digit: 55 and 56
df = df.loc[(df["Sic1_twod"] == "55") | (df["Sic1_twod"] == "56") | 
            (df["Sic2_twod"] == "55") | (df["Sic2_twod"] == "56")| 
            (df["Sic3_twod"] == "55") | (df["Sic3_twod"] == "56") | 
            (df["Sic4_twod"] == "55") | (df["Sic4_twod"] == "56"), : ]
#filer out the companies in London
df = df.loc[(df['RegAddress.PostTown'] == 'LONDON'), :]


# In[4]:


#change the date in the df to datetime
df["IncorporationDate"] = pd.to_datetime(df["IncorporationDate"])
df1 = df.copy()


# In[5]:


#matplotlib viz set-up
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
titlefont = {'fontname':'Lucida Grande', 'fontsize':'45'}


# In[6]:


#Graph 1 - the status of hospitality business across London boroughs
# group the status into 3 main categories :
#'Active', 'In Administration/Liquidation', 'Proposal to strike off'
df['CompanyStatus'].unique()
df['status'] = 0
df.loc[(df['CompanyStatus'] == 'Active'), 'status'] = 'Active'
df.loc[(df['CompanyStatus'] == 'Active - Proposal to Strike off'), 'status'] = 'Proposal to strike off'
df.loc[(df['CompanyStatus'] == 'In Administration/Receiver Manager') | 
       (df['CompanyStatus'] == 'Voluntary Arrangement') |
       (df['CompanyStatus'] == 'In Administration/Administrative Receiver') |
       (df['CompanyStatus'] == 'In Administration') |
       (df['CompanyStatus'] == 'Liquidation') |
       (df['CompanyStatus'] == 'Live but Receiver Manager on at least one charge'),
       'status'] = 'In Administration/Liquidation'


# In[7]:


#find the location of the compaies
geolocator = Nominatim(user_agent = "my_user_agent")

#get locations
companies = df.index
addresses = df.loc[:, "RegAddress.PostCode"].to_list()

coords = {}
for i, j in zip(companies, addresses):
    try:
        location = geolocator.geocode(j)
        if (location.latitude is not None) & (location.longitude is not None):
            coords[i] = {
                "Lat": location.latitude,
                "Long": location.longitude,
            }
        else:
            pass
    except:
        print("Not finding a match!?")


# In[8]:


df_coords = pd.DataFrame(coords)
#put the coordiates back to the original df
df2 = pd.merge(df, df_coords.T, left_index=True, right_index=True, how="inner")


# In[14]:


#filter the coordinates to fit the London map
df3 = df2.loc[(df2["Long"] <0.8) & (df2["Long"] >-0.8),:]
df3 = df3.loc[(df2["Lat"] <52) & (df2["Lat"] >51),:]
#filter to only include companies that are not in 'Active' status
df_scatter = df3.loc[(df3['status'] =='In Administration/Liquidation') |
                     (df3['status'] =='Proposal to strike off') , :]


# In[15]:


#change the df into a gdf
gdf = gp.GeoDataFrame(df_scatter, geometry=gp.points_from_xy(df_scatter.Long, df_scatter.Lat))
gdf_geo = gdf.set_crs(epsg=4326)
gdf_wm = gdf_geo.to_crs(epsg=3857)


# In[16]:


# file that map the boundaries of london boroughs
data = gp.read_file("london_boroughs.json")
#information of Covid deaths in different London boroughs
data['Covid death rate'] = 0
data.loc[(data['name'] == 'Newham'), 'Covid death rate'] = 31
data.loc[(data['name'] == 'Tower Hamlets'), 'Covid death rate'] = 29
data.loc[(data['name'] == 'Redbridge') | (data['name'] == 'Brent') , 'Covid death rate'] = 28
data.loc[(data['name'] == 'Barking and Dagenham') , 'Covid death rate'] = 27
data.loc[(data['name'] == 'Harrow') | (data['name'] == 'Hackney'), 'Covid death rate'] = 26
data.loc[(data['name'] == 'Waltham Forest'), 'Covid death rate'] = 25
data.loc[(data['name'] == 'Croydon') | (data['name'] == 'Lambeth') |(data['name'] == 'Haringey') | 
         (data['name'] == 'Hounslow') | (data['name'] == 'Havering'), 'Covid death rate'] = 24
data.loc[(data['name'] == 'Merton') | (data['name'] == 'Ealing') | 
         (data['name'] == 'Lewisham') | (data['name'] == 'Hillingdon')| (data['name'] == 'Barnet')|
         (data['name'] == 'Enfield'), 'Covid death rate'] = 23
data.loc[(data['name'] == 'Kensington and Chelsea'), 'Covid death rate'] = 22
data.loc[(data['name'] == 'Southwark') | (data['name'] == 'Westminster') , 'Covid death rate'] = 21
data.loc[(data['name'] == 'Greenwich') | (data['name'] == 'Bexley') | (data['name'] == 'Islington')|
         (data['name'] == 'Wandsworth') | (data['name'] == 'Kingston upon Thames')| 
         (data['name'] == 'Sutton'), 'Covid death rate'] = 20
data.loc[(data['name'] == 'Hammersmith and Fulham') | (data['name'] == 'Camden') | 
         (data['name'] == 'City of London'),'Covid death rate'] = 19
data.loc[(data['name'] == 'Bromley') |(data['name'] == 'Richmond upon Thames'), 'Covid death rate'] = 18


# In[21]:


#plot the figure
fig = plt.figure(figsize=(25, 25))
ax = fig.add_subplot(1, 1, 1)
#plot London borough boundaries and the death rate
data.plot(column='Covid death rate', cmap='BuPu', ax=ax, edgecolor='0.8')

#plot scatter graph of company status
#set color
colorlist=[]
for i in range(len(df_scatter)):
    if df_scatter["status"][i] == 'Proposal to strike off': #if the company is proposing to strike off, color = blue
        colorlist.append('orange')
    elif df_scatter["status"][i] == "In Administration/Liquidation": #if the company is proposing to strike off, color = blue
        colorlist.append('slategray')
        
#set legend 
legend_elements = [Line2D([0], [0], marker='^', color='k',label='Proposal to strike off',
                         markerfacecolor='orange', markersize=20),
                   Line2D([0], [0], marker='^', color='k',label='In Administration/Liquidation',
                         markerfacecolor='slategray', markersize=20)]
ax.scatter(gdf_wm.Long, gdf_wm.Lat, 
           color=colorlist, 
           marker='^',
           alpha=0.7, 
           s=26)
ax.legend(handles = legend_elements, loc = 'upper right', fontsize=15)
#format axes
ax.set_title("Status of Hospitality Business vs COVID-19 death rate \n in different London Boroughs", 
               **titlefont, pad = 60, color = "k")
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.set_yticks([])
ax.set_xticks([])
ax.set_ylabel('Covid deaths as a % of total deaths \n  (March 2020 - April 2021)', fontsize=25, color='dimgray')
#add colorbar
sm = plt.cm.ScalarMappable(cmap='BuPu', 
                           norm=plt.Normalize(vmin=data['Covid death rate'].min(), 
                                              vmax=31))
sm._A = []
cbar_axis = inset_axes(ax, width='2.5%', height='95%', loc=2)
cbar = plt.colorbar(sm, orientation='vertical', cax=cbar_axis)

#insert stacked bar chart
#create a df for active vs administration vs proposal to strike off
df_count = df2.groupby(by="status").size().reset_index()
df_count["percentage"] = round(((df_count[0]/41366)*100), 1)

#plot stacked bar chart
pal=['slateblue', 'darkslategray', 'orange']
axins = inset_axes(ax,
                   width=2.5, 
                   height=6, 
                   loc=4)
df_count[["percentage"]].T.plot(kind="bar",
                     ax=axins,
                     stacked=True,
                     color=pal,
                     legend=None,
                     alpha=0.5)
#format axes
axins.spines['top'].set_visible(False)
axins.spines['right'].set_visible(False)
axins.spines['left'].set_visible(False)
axins.spines['bottom'].set_visible(False)
axins.set_xticklabels([])
axins.set_yticklabels([])
axins.set_yticks([])
axins.set_xticks([])
axins.set_xlabel('The status of current\n hospitality companies', 
                 fontsize=22, 
                 color='black', 
                 fontweight='bold')    
axins.xaxis.set_label_position('top')
axins.set_facecolor(color='white')
#add annotation
axins.annotate('Active \n89.3%',
            xy=(-0.1, 50),
            xytext=(-0.1, 50),
            size=15,
            color='black',
            annotation_clip = False,
            fontweight='bold')
axins.annotate(' \n In Administration/\n    Liquidation \n         2.4%',
            xy=(-0.05, 90),
            xytext=(0.4, 84),
            size=15,
            color='black',
            arrowprops=dict(arrowstyle='<|-',
            fc='gray', ec="gray"),
            annotation_clip = False,
            fontweight='bold') 
axins.annotate('Proposal to strike off \n            8.3%',
            xy=(-0.35, 93),
            xytext=(-0.35, 93),
            size=15,
            color='black',
            annotation_clip = False,
            fontweight='bold')
plt.show()


# In[18]:


#Graph 2 - compare the number of new company registered before and after covid 
df1_before = df1.loc[(df1["IncorporationDate"] >= datetime.strptime('01/05/18', '%d/%m/%y')) &
                     (df1["IncorporationDate"] < datetime.strptime('30/01/20', '%d/%m/%y')) , :]
df1_after = df1.loc[(df1["IncorporationDate"] >= datetime.strptime('30/01/20', '%d/%m/%y')), :]

#set the time of different covid rules
#start of pandemic
cov_st = datetime.strptime('30/01/20', '%d/%m/%y')
#first lockdown phase
lockdown1_start = datetime.strptime('26/03/20', '%d/%m/%y')
lockdown1_relaxed = datetime.strptime('23/06/20', '%d/%m/%y')

#reopening date
opening = datetime.strptime('04/07/20', '%d/%m/%y')

#eat out to help out phase
eotho_start = datetime.strptime('03/08/20', '%d/%m/%y')
eotho_end = datetime.strptime('31/08/20', '%d/%m/%y')

#second lockdown phase
lockdown2_start = datetime.strptime('05/11/20', '%d/%m/%y')
lockdown2_end = datetime.strptime('15/12/20', '%d/%m/%y')

#third lockdown phase
lockdown3_start = datetime.strptime('06/01/21', '%d/%m/%y')
lockdown3_end = datetime.strptime('08/03/21', '%d/%m/%y')

date_op = [opening, eotho_start]
date_eotho = [eotho_start, eotho_end]
#date_ld = [lockdown1_start, lockdown1_relaxed]
date_ld1_end = [lockdown1_start,opening ]
date_ld2_end = [lockdown2_start, lockdown2_end]
date_ld3_end = [lockdown3_start, lockdown3_end]
degree = [1250, 1250]


# In[22]:


#plot the graph
fig = plt.figure(figsize=(30,25))
ax2 = fig.add_subplot(1, 1, 1)
#plot the different periods
ax2.plot(date_op, degree)
ax2.plot(date_eotho, degree)
ax2.plot(date_ld1_end, degree)
ax2.plot(date_ld2_end, degree)
ax2.plot(date_ld3_end, degree)
ax2.fill_between(date_ld1_end, degree, alpha=0.2, color='red')
ax2.fill_between(date_ld2_end, degree, alpha=0.2, color='red')
ax2.fill_between(date_ld3_end, degree, alpha=0.2, color='red')
ax2.fill_between(date_op, degree, alpha=0.2, color='lightgreen')
ax2.fill_between(date_eotho, degree, alpha=0.9, color='lightyellow')

#plot our data
ax2.hist(df1_before["IncorporationDate"], 
        bins=25, 
        alpha=1, 
        histtype = 'bar',
        label='new companies', 
        color='gold',
        edgecolor='white')
ax2.hist(df1_after["IncorporationDate"], 
        bins=25, 
        alpha=1, 
        histtype = 'bar',
        label='new companies', 
        color='grey',
        edgecolor='white')


#set legend 
legend_elements2 = [Patch(facecolor='red', edgecolor='red',
                         label='Lockdowns', alpha=0.2),
                   Patch(facecolor='lightgreen', edgecolor='lightgreen',
                         label='Reopening of restaurants and pubs', alpha=0.2),
                   Patch(facecolor='yellow', edgecolor='yellow',
                         label='Eat Out to Help Out Scheme', alpha=0.2)]

#format axes
#ax2.axvline(x=cov_st, color='grey',ls="-", alpha=0.7)
ax2.axhline(y= 200, color="black", ls=":", alpha=0.7)
ax2.axhline(y= 400, color="black", ls=":", alpha=0.7)
ax2.axhline(y= 600, color="black", ls=":", alpha=0.7)
ax2.axhline(y= 800, color="black", ls=":", alpha=0.7)
#ax2.axhline(y= 750, color="black", ls=":", alpha=0.7)
ax2.set_facecolor('white')
ax2.set_ylabel('Counts', fontsize=30, color='black')
ax2.set_xlabel('Date', fontsize=35, color='black', loc='right')
ax2.set_title("Number of New Hospitality Business registered \n through COVID-19 in London", 
               **titlefont, pad = 60, color = "k")
ax2.legend(handles = legend_elements2, loc = 'upper left', fontsize = 27, frameon = False)
ax2.set_yticks([200, 400, 600, 800])
ax2.tick_params(labelsize=25, colors = 'black')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.spines['bottom'].set_visible(False)

#add annotation
x1 = datetime.strptime('25/09/19', '%d/%m/%y')
x2 = datetime.strptime('29/03/20', '%d/%m/%y')
x3 = datetime.strptime('08/11/20', '%d/%m/%y')
x4 = datetime.strptime('09/01/21', '%d/%m/%y')
x5 = datetime.strptime('20/07/19', '%d/%m/%y')
x6 = datetime.strptime('01/02/19', '%d/%m/%y')
x7 = datetime.strptime('15/07/20', '%d/%m/%y')

ax2.annotate('After COVID-19',
            xy=(cov_st, -90),
            xytext=(x7, -95),
            size=30,
            color = 'black',
            arrowprops=dict(arrowstyle='<|-',
            fc="gray", ec="gray"),
            annotation_clip = False,
            fontweight='bold')
ax2.annotate('1st Lockdown',
            xy=(lockdown1_start, 1100),
            xytext=(x2, 1100),
            size=25,
            color = 'dimgrey',
            annotation_clip = False,
            rotation=90)
ax2.annotate('2nd Lockdown',
            xy=(lockdown2_start, 1095),
            xytext=(x3, 1095),
            size=25,
            color = 'dimgrey',
            annotation_clip = False,
            rotation=90)
ax2.annotate('3rd Lockdown',
            xy=(lockdown3_start, 1100),
            xytext=(x4, 1100),
            size=25,
            color = 'dimgrey',
            annotation_clip = False,
            rotation=90)
ax2.annotate('Before COVID-19',
            xy=(cov_st, -90),
            xytext=(x6, -95),
            size=30,
            color = 'black',
            arrowprops=dict(arrowstyle='<|-',
            fc="gray", ec="gray"), 
            annotation_clip = False,
            fontweight='bold')
ax2.annotate('Start of COVID: \n    31-01-2020',
            xy=(x1, 680),
            xytext=(x1, 680),
            size=30,
            color='black',
            annotation_clip = False,
            fontweight='bold')
         

plt.show()

