#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:58:34 2019

@author: plume
"""

import numpy as np
import pandas as pd
import datetime
import glob
import sys
import station_data_reading as sD



def find_first_row(data):
    for i in range(len(data))[:4]:
        row_val = data.iloc[i]
        for j in range(len(row_val)):
            if 'altitude départ' == row_val.iloc[j]:
                return i


def find_row_to_del(data):
    row_to_del = []
    for j in range(len(data)):
        row_val = data.iloc[j].values.astype(str)
        # row with remarks have almost all their columns to nan, hence checking if number of nan is superior that nb_columns - 3 
        if len(np.where(row_val == 'nan')[0]) > data.shape[1] - 3:
            row_to_del.append(j)
    
    return row_to_del


### READ XLSX AND EXTRACT INFORMATION FROM IT ###


all_data = pd.DataFrame()
for xlsx_file in glob.glob('data/epa_reports/xlsx/*'):
    xl = pd.ExcelFile(xlsx_file)
    for page in xl.sheet_names:
        print(page)
        data = xl.parse(page) 
        # Header is different from page to page so we check where the columns are located (he check the column altitude départ)
        first_row = find_first_row(data)
        if first_row is None:
            continue
        data = xl.parse(page, skiprows=first_row + 1)
        # we delete here not usefull rows (most of the time it is row that are created for remarks)
        row_to_del = find_row_to_del(data)
        data = data[~data.index.isin(row_to_del)]
        try:
            data['site_id'] = data['numro id'].apply(lambda x: x.split('\n')[0])
            data['numero_id'] = data['numro id'].apply(lambda x: x.split('\n')[1])
        except IndexError:
            data['site_id'] = data['numro id'].apply(lambda x: x.split(' ')[0])
            data['numero_id'] = data['numro id'].apply(lambda x: x.split(' ')[1])
        data = data.drop('numro id', axis=1)
        data = data.dropna(subset=['date1', 'date2', 'site_id', 'numero_id'])
        data['site_id'] = data['site_id'].apply(lambda x: x[2:] if 'n°' in x else x)
        data['numero_id'] = data['numero_id'].apply(lambda x: x[3:] if 'id' in x else x)
        data['date1'] = data['date1'].apply(lambda x: x.split('\n')[0])
        data['date2'] = data['date2'].apply(lambda x: x.split('\n')[0])
        data['city'] = xlsx_file.split('_')[-1].split('.')[0]
        all_data = pd.concat([all_data, data[['city', 'date1', 'date2', 'site_id', 'numero_id', 'altitude départ', 'altitude arrivée', 'longeur (m)', 'largeur (m)', 'hauteur (m)']]])

all_data.to_csv('data/epa_reports/all_epa_reports_data.csv', index=False)

#### SELECT EVENT THAT TOOK PLACE AFTER 2010 (we do not have snow / weather information older than that)

dataset['year'] =  dataset['date1'].apply(lambda x: int(x.split('/')[2]))


after_which_year = 10

good_data = pd.DataFrame()
dataset['good'] = False

# An observations from 2015 or 1915 will have year information as 15, so we need to discriminate between these two,
# To do so, we check the first event with year > 20, it will be for sure a year 19xx and we select only observations older than that (we can do that because informations are in the chronological order)
for city in dataset['city'].unique():
    print(city)
    data = dataset[dataset['city'] == city]
    for id_ in data['site_id'].unique():
        data_site = data[data['site_id']==id_].reset_index()
        try:
            first_19_century_event = data_site[data_site['year'] > 20].index[0]
        except IndexError:
            first_19_century_event = len(data_site)
        recent_data = data_site.loc[0: first_19_century_event - 1]
        good_events = recent_data[recent_data['year'] >= after_which_year]['index']
        dataset.loc[good_events, 'good'] = True


dataset = dataset[dataset['good']]

dataset.to_csv('data/epa_reports/all_recent_epa_reports_data.csv')



## SELECT ONLY OBSERVATION FOR PATH WITH AT LEAST 10 EVENTS AND FOR VANOISE CITY

dataset = pd.read_csv('data/epa_reports/all_recent_epa_reports_data.csv')
dataset = dataset.rename(columns={'hauteur (m)': 'hauteur', 'longeur (m)': 'longueur', 'largeur (m)': 'largeur'})


### Find path with more than minimun_events_per_path
#### Here we select only path where quite a lot of avalanche have been observed
minimun_events_per_site = 10

final_data = pd.DataFrame()
good_site_id = []
for city in dataset['city'].unique():
    data = dataset[dataset['city'] == city]
    for site_id in data['site_id'].unique():
        data_site = data[data['site_id'] == site_id]
        if len(data_site[data_site['good']]) >= minimun_events_per_site:
            print(city, site_id, len(data_site[data_site['good']]))
            good_site_id.append([city, site_id])    
            if city in ['BESSANS', 'BONNEVAL-SUR-ARC', 'PRALOGNAN-LA-VANOISE', "VAL-D'ISERE", 'TIGNES']:
                final_data = pd.concat([final_data, data_site[data_site['good']]])

data = final_data.copy()

data[['date1', 'date2']] = data[['date1', 'date2']].applymap(lambda x: datetime.datetime.strptime(x, '%d/%m/%y'))
data = data[-data['altitude départ'].isnull()]
data = data[-data['altitude arrivée'].isnull()]


for type in ['départ', 'arrivée']:    
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.split('\n')[0])
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace(' ', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('A', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('B', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('X', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('Y', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('Z', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace('?', ''))
    data[f'altitude {type}'] = data[f'altitude {type}'].apply(lambda x: x.replace(' ?', ''))

data = data[(data['altitude départ'] != '') | (data['altitude départ'] != '')]

data['altitude départ'] = data['altitude départ'].astype(float)
data['altitude arrivée'] = data['altitude arrivée'].astype(float)
data = data[data['altitude départ'] != -1]

data.to_csv('data/epa_reports/epa_reports_vanoise.csv', index=False)



### WE ARE FIRST GOING TO WORK ON VANOISE DATASETS WHERE THERE IS A LOT OF AVALANCHE EVENTS

data = pd.read_csv('data/epa_reports/epa_reports_vanoise.csv')
data = data[data['city'] == 'BESSANS']
data.to_csv('data/epa_reports/epa_reports_bessans.csv', index=False)

#### FIRST WE CONCENTRATE ON BESSANS CITY ####
data = pd.read_csv('data/epa_reports/epa_reports_bessans.csv')
data[['date1', 'date2']] = data[['date1', 'date2']].applymap(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))


## stat about altitude de depart des avalanches
data.groupby('site_id')['altitude départ'].describe()

# number of occurences per site id
data.groupby('site_id')['good'].count()

# keep only observations where avalanche elevation is present
data = data[~data['altitude départ'].isnull()]




# ESSAYER DE RECUPERER L'HEURE DU CONSTAT LORS DE LA LECTURE DES XLSX ?? 

# data1 and date2 are the time interval when the avalanche occured
# keep only observations where we have at most 1 days of uncertainty
data = data[(data['date2'] - data['date1']) <= '1 days']





### donnée dispo à Bessans (les autres donnees non mentionnees ne sont pas assez présente ou inutile)
## ht_neige (ht neige totale): 100%
## ssfrai (hauteur neige fraiche): 100%
## phenspe1 (phenomène spéciale 1): 100%
## td: point de rosée: 99%
## rr24 (précicipation dernière 24h en mm): 96%
## t (temperature): 100%
## tx24 (temp max 24h): 95%
## tn24 (temp min 24h): 95%
## dd (direction du vent), probablement moyen sur 24h (bcp de 0): 100%
## u (humidité): 100%
## ff (force vent), probablement moyen sur 24h (bcp de 0): 100%
## n (nebulisté totale, en %): 100%
## aval_risque (risque avalanche): 75%




### ML Dataset on Bessans
    
avalanche_dataset = pd.read_csv('../data/epa_reports/epa_reports_bessans.csv')
avalanche_dataset = avalanche_dataset[~avalanche_dataset['altitude départ'].isnull()]
avalanche_dataset[['date1', 'date2']] = avalanche_dataset[['date1', 'date2']].applymap(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
avalanche_dataset = avalanche_dataset[(avalanche_dataset['date2'] - avalanche_dataset['date1']) <= '1 days']

## we will consider avalanche date as data2 in avalanche_dataset
avalanche_dataset = avalanche_dataset.rename(columns={'date2': 'date'})
avalanche_dataset['date'] = pd.to_datetime(avalanche_dataset['date'])


## load weather data 
all_month = ['0'+str(i) for i in range(1,10)] + [str(i) for i in range(10,13)]
weather_data = sD.create_dataset(list_year=[str(i) for i in range(2010,2019)],
                                          list_month=all_month)
weather_data = weather_data[weather_data['Nom']=='Bessans']
weather_data['date'] = weather_data['date'].apply(lambda x: x.round('D'))

## keep only columns where at least 80% of observations 
weather_data = sD.select_cols(weather_data, 0.8)
weather_data = weather_data[['date', 'Nom', 'ht_neige', 'ssfrai', 'td', 'rr24', 't', 'tx24', 'tn24', 'dd', 'u', 'ff', 'n', 'aval_risque']]
for col in list(set(weather_data.columns) - set(['date', 'Nom'])):
    weather_data[col] = weather_data[col].astype(float)

weather_data = weather_data.groupby(['date', 'Nom']).mean().reset_index()
weather_data.to_csv('weather_bessans.csv', index=False)





weather_data = pd.read_csv('weather_bessans.csv')
weather_data['date'] = weather_data['date'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))


dataset = avalanche_dataset.merge(weather_data, on='date')
#dataset.groupby('site_id').size()


## Quand on join avalanche_data avec weather data, on passe de 438 observations
## à 185. On pert enormement de données a cause du manque de donnees meteo.
## Ce serait interessant de regarder si avec les stations météo autour, on a pas plus 
## de données.
## Etrange d'avoir autant de trou de données dans les données météo, regardez ça de plus près



#### we will work with several path id but considering it is the same one to exclude the spatial
#### but have enough data with avalanche observations

site_ids = [17, 46, 16, 18, 15, 14, 13, 12, 11, 20]
dataset[dataset['site_id'].isin(site_ids)]













### SELECTIONNER LES COLONNES CI DESSUS ET REGARDER CE QUE CELA DONNE SUR LES STATIONS PROCHES
### REGARDER AUSSI SUR LES STATIONS PROCHES, LES DONNEES DE TYPE PROFONDEUR DE SONDE, TEMP DE NEIGE ETC (QUI SONT TRES UTILES)




# Beaucoup d'observations de vitesse du vent à 0 probablement car moyenne sur 24h. 
# Donnees plus precise pour vent / direction du vent pour chaque station ?? https://www.infoclimat.fr/observations-meteo/archives/5/decembre/2012/bessans/000N1.html






















# Info from article.


n_year = 2005 - 1991 
n_months = 4
n_days = 30
n_gullies = 49



82320 = n_year* n_months * n_days * n_gullies

# They say to have 89335 no avalanche events. It is near my estimation so I guess that they are considering only one point per avalanche path











