import os
import requests
import pandas as pd
import numpy as np
import datetime
import io

from dotenv import load_dotenv
load_dotenv("C:/Users/serojans/hydro_SGU_SMHI_return_periods/.env")


class DateTime:
    def __init__(self, current_date=None) -> None:
        
        self.cwd = os.path.abspath(os.path.dirname(__file__))
        if current_date == None:
            current_date = datetime.datetime.now().date()
        
        self.today = str(current_date)
        self.yesterday = str(current_date - datetime.timedelta(days=7))
 

class fetch_projektnavet_data:

    def __init__(self) -> None:
        self.projektnav_APISECRET_projektpin = os.environ.get('projektnav_APISECRET_projektpin')
        self.projektnav_APISECRET_userpin = os.environ.get('projektnav_APISECRET_userpin')
        datetime = DateTime()
        self.cwd = datetime.cwd
        self.today = datetime.today
        self.yesterday = datetime.yesterday


    def extract_metadata(self):
    # Set parameters for API call
        params = {'proj': '299',
            'projpin': self.projektnav_APISECRET_projektpin,
            'user': '3552',
            'userpin': self.projektnav_APISECRET_userpin
            }
        try:
            # Call API and get and encode data
            response = requests.get("http://projektnav.net/pub/mpkldefs-csv.dh", params=params)
            if response:
                print(f'Success connecting to Projektnavet {self.today}')
            response.encoding = 'ISO-8859-1'
            # Read data into dataframe
            controlObject = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False)
            # Check if response is ok and return dataframe
            return controlObject
        
        except Exception as e:
            print(f"Error connection to Projektnav.NET: {str(e)}")
            return None

    def extract_leveldata(self, from_date, to_date):
        # Set parameters for API call
        params = {
            'proj': '299',
            'projpin': self.projektnav_APISECRET_projektpin,
            'user': '3552',
            'userpin': self.projektnav_APISECRET_userpin,
            'ty': '64',
            'd1': from_date,
            'd2': to_date,
            "frist": "0",    
        }

        try:
            # Call API and get and encode data
            response = requests.get("http://projektnav.net/pub/export-mpklvals-csv.dh", params=params)
            if response:
                print(f'Success connecting to Projektnavet {self.today}')
            response.encoding = 'ISO-8859-1'
            # Read data into dataframe
            Projektnavdata = pd.read_csv(io.StringIO(response.text), encoding='Latin-1', low_memory=False)
            # Check if response is ok rename and return dataframe
            return Projektnavdata
        except Exception as e:
            print(f"Error connection to Projektnav.NET: {str(e)}")
            return None
        

    def map_metadata_to_leveldata(self, data, metadata):
        data = data.rename(
            columns={
                'Nr':'id', 
                'Datum Tid':'datetime',  
                'Anm/Kod':'quality'
                }).copy()
        
        metadata = metadata.rename(
            columns={'Nr':'id', 
                    'X0':'X', 
                    'Y0':'Y', 
                    'Till.':'top_of_casing (m asl)', 
                    'Meta data':'metadata',
                    'Lat': 'latitude', 
                    'Lng': 'longitude',
                    'Anm.': 'comment'
                }).copy()


        dataId = data.id.unique()
        subset_metadata = metadata.loc[metadata.id.isin(dataId)].copy()
        


        subset_metadata_X = dict(zip(subset_metadata.id, subset_metadata.X))
        subset_metadata_Y = dict(zip(subset_metadata.id, subset_metadata.Y))
        subset_metadata_Z = dict(zip(subset_metadata.id, subset_metadata['top_of_casing (m asl)']))

        subset_metadata_lat = dict(zip(subset_metadata.id, subset_metadata.latitude))
        subset_metadata_lon = dict(zip(subset_metadata.id, subset_metadata.longitude))

        subset_metadata_com = dict(zip(subset_metadata.id, subset_metadata.comment))
        subset_metadata_M = dict(zip(subset_metadata.id, subset_metadata.metadata))

        for col, values in [ ('X', subset_metadata_X), ('Y', subset_metadata_Y), 
                            ('top_of_casing (m asl)', subset_metadata_Z), ('metadata', subset_metadata_M),
                            ('latitude', subset_metadata_lat), ('longitude', subset_metadata_lon),
                            ('comment', subset_metadata_com)]:
             data.loc[:, col] = data['id'].map(values)

        # split the metadata column into three new columns
        data.loc[:, 'metadata'] = data['metadata'].astype(str)
        data.loc[:, 'aquifer_type'] = data['metadata'].str.extract(r'aquifer_type=([^\n]+)')
        data.loc[:, 'soil_type'] = data['metadata'].str.extract(r'soil_type=([^\n]+)')
        data.loc[:, 'topographic_location'] = data['metadata'].str.extract(r'topographic_location=([^,\n]+)')

        data.drop('metadata', axis=1, inplace=True)
      
        data.loc[:, 'value'] = data['top_of_casing (m asl)'] + data['Z'].astype(float)
        data.loc[:, 'datetime'] = pd.to_datetime(data['datetime'])
        data.loc[:, 'datetime'] = data['datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
        
        data = data.dropna(subset='value')

        data = data.rename(columns={'value':'m asl'})  

        data = data.loc[:, ['id', 'datetime', 'm asl', 'top_of_casing (m asl)', 'soil_type', 'aquifer_type', 'topographic_location', 'latitude', 'longitude', 'quality', 'comment']].copy()

        
        return data    
