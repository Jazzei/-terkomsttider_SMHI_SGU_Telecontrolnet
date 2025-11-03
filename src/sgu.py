import os
import pandas as pd
import json
import io
import requests
import datetime
from time import sleep

'''

Hämta stationsuppgifter om alla stationer i ett visst län
https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/stationer/{länskod}?format=[json,csv]

Hämta alla mätningar som är gjorda i ett visst län
https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/nivaer/lan/{länskod}?format=[json,csv]

Hämta alla mätningar som är gjorda vid en viss station
https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/nivaer/station/{stations-id}?format=[json,csv]

'''
class Datetime:
    def __init__(self, current_date=None) -> None:
        
        self.cwd = os.path.abspath(os.path.dirname(__file__))
        if current_date == None:
            current_date = datetime.datetime.now().date()
        
        self.today = str(current_date)
        self.yesterday = str(current_date - datetime.timedelta(days=1))

class fetch_sgu_data:

    def __init__(self) -> None:

        path = os.path.join('..', 'metadata', 'sgu.json')

        with open(path, 'r',  encoding='utf-8') as f:
            lanskoder = json.load(f)

        self.lanskod = lanskoder['länskoder']

        # print("SGU Länskoder:")  
        # for key, value in self.lanskod.items():
        #     print(f"Län: {key}, {value}")

        datetime = Datetime()
        self.cwd = datetime.cwd
        
    def fetch_stations(self, lanskod=None):

        dFrames = []

        if lanskod is not None:
            url = f"https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/stationer/{lanskod}?format=csv"
            response = requests.get(url)
            sgu = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False, delimiter=';')
            dFrames.append(sgu)
            print(f"Fetched data for lanskod: {lanskod}")

        else:

            for key, value in self.lanskod.items():
                url = f"https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/stationer/{value}?format=csv"
                response = requests.get(url)
                sgu = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False, delimiter=';')
                dFrames.append(sgu)
                print(key)
            
        df = pd.concat(dFrames)

        return df

    def fetch_measurements(self, df, is_active=None, is_not_active=None):

        # kommunkod = 1480
        # df = df.loc[df['Kommunkod'] == kommunkod]

        df_active = df.loc[df['Slutdatum för mätning'].isna()]
        df_not_active = df.dropna(subset = 'Slutdatum för mätning')


        dict_ids_not_active = dict(zip(df_not_active['Område- och stationsnummer'], df_not_active['Stationens namn']))
        dict_ids_active = dict(zip(df_active['Område- och stationsnummer'], df_active['Stationens namn']))
        dict_ids_all = dict(zip(df['Område- och stationsnummer'], df['Stationens namn']))

        if is_active == True:
            dict_ids = dict_ids_active
            # station_ids = list(dict_ids_active.keys())
        elif is_not_active == True:
            dict_ids = dict_ids_not_active
            # station_ids = list(dict_ids_not_active.keys())
        else:
            dict_ids = dict_ids_all
            # stations_ids = list(dict_ids_all.keys())

        dFrames = []
        
        for key, value in dict_ids.items():
                
            url = f"https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/nivaer/station/{key}?format=csv"

            response = requests.get(url)

            sgu = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False, delimiter=';')

            dFrames.append(sgu)
            # print(value)
        df = pd.concat(dFrames)
        print("Success connecting to SGU!")

        return df
    

    def fetch_all_measurements_lan(self):

        dFrames = []

        for key, value in self.lanskod.items():

            url = f"https://resource.sgu.se/oppnadata/grundvatten/api/grundvattennivaer/nivaer/lan/{value}?format=csv"

            response = requests.get(url)

            sgu = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False, delimiter=';')

            dFrames.append(sgu)
            # print(key)
        df = pd.concat(dFrames)

        return df


    def convert_columns_to_standard(self, df):
        df.rename(
        columns={
            'Område- och stationsnummer': 'station_id',
            'Datum för mätning': 'datetime',
            'Stationens namn': 'id',
            'Grundvattennivå (m ö.h.)': 'value',
            'Referensnivå för röröverkant (m ö.h.)': 'top_of_casing (m asl)',
            'Jordart': 'soil_type',
            'Akvifertyp': 'aquifer_type',
            'Topografiskt läge': 'topographic_location',
            'Nivåmätningskvalitet': 'quality',
        },
        inplace=True
        )

        df = df.loc[:, ['id', 'station_id', 'datetime', 'value', 'top_of_casing (m asl)', 'soil_type', 'aquifer_type', 'topographic_location', 'latitude', 'longitude', 'quality']].copy()

        return df