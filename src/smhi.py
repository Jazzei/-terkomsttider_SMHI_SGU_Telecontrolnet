import pandas as pd
import datetime
import io
import json
import os
import requests
from typing import List, Optional
from pydantic import BaseModel


'''
Dålig implementering av Pydantic klasser, behöver ses över.

'''
class Station(BaseModel):
    key: str
    name: str
    owner: str
    ownerCategory: str
    measuringStations: str
    height: int

class Parameter(BaseModel):
    key: str
    name: str
    summary: str
    unit: str


class Datetime:
    def __init__(self, current_date=None) -> None:
        
        self.cwd = os.path.abspath(os.path.dirname(__file__))
        if current_date == None:
            current_date = datetime.datetime.now().date()
        
        self.today = str(current_date)
        self.yesterday = str(current_date - datetime.timedelta(days=1))

class fetch_smhi_data:

    def __init__(self) -> None:
        
        datetime = Datetime()
        self.cwd = datetime.cwd
        self.today = datetime.today
        self.yesterday = datetime.yesterday
        # To get historical data, use include_historic_data=True in fetch_data(). Use 'latest-day' to get data for the last 24 hours.
        self.period = 'latest-months'


        # Loading metadata from SMHI active stations. Cannot find URL "Ladda ned stationsinformation (.csv)", see exmepel below.  
        # https://www.smhi.se/data/meteorologi/ladda-ner-meteorologiska-observationer#param=airtemperatureInstant,stations=core

        precipitation_smhi_metadata = os.path.join('..', 'metadata', 'metobs_precipitationHourlySum_active_sites.csv')

        self.station_ids_precipitation = pd.read_csv(precipitation_smhi_metadata, sep=';')

        temperature_smhi_metadata = os.path.join('..', 'metadata', 'metobs_airtemperatureInstant_core_sites.csv')
        self.station_ids_temperature = pd.read_csv(temperature_smhi_metadata, sep=';')
        self.station_ids_temperature = self.station_ids_temperature.loc[self.station_ids_temperature['Aktiv'] == 'Ja']

        air_pressure_smhi_metadata = os.path.join('..', 'metadata', 'metobs_airPressure_active_sites.csv')
        self.station_ids_air_pressure = pd.read_csv(air_pressure_smhi_metadata, sep=';')


    def set_data_type(self, data_type):

        if data_type == 'temperature':
            self.data_type = 1
            self.station_ids = self.station_ids_temperature
        elif data_type == 'precipitation':
            self.data_type = 7
            self.station_ids = self.station_ids_precipitation
        elif data_type == 'air_pressure':
            self.data_type = 9
            self.station_ids = self.station_ids_air_pressure
        else:
            print('Wrong data type: choose between "temperature", "precipitation", "air_pressure"')
            return None
        
        
    def set_station(self):
        stations = self.station_ids_air_pressure.loc[self.station_ids_air_pressure['Namn'].str.contains('Göteborg A')]
        self.ids = stations['Id'].unique()
        # print(len(self.ids))

    def print_station_ids(self):
        print(self.ids)
        

    def fetch_data(self, include_historic_data=None) -> pd.DataFrame:

        all_data = []

        for station_id in self.ids:
            print(f"Fetching data for station {station_id}.../nPeriod: {self.period}")

            url = f"https://opendata-download-metobs.smhi.se/api/version/latest/parameter/{self.data_type}/station/{station_id}/period/{self.period}/data.json"
            response = requests.get(url)
            print(response.content[0:100])

            response.encoding = 'utf-8-sig'
            try:
                
                response.raise_for_status()
                json_data = response.json()
                
                parameter = Parameter(**json_data.get('parameter', {}))
                df_parameter = pd.DataFrame(parameter.dict(), index=[0])

                station = Station(**json_data.get('station', {}))
                df_station = pd.DataFrame(station.dict(), index=[0])
            
                position_data = json_data.get('position', [])
                df_position = pd.DataFrame(position_data)
                
                value_data = json_data.get('value') 
                df_value = pd.DataFrame(value_data)
                # print(df_value.head())
                df_value['id'] = df_station['name'][0]
                df_value['station_id'] = df_station['key'][0]
                df_value['unit'] = df_parameter['unit'][0]
                df_value['type'] = df_parameter['name'][0]
                df_value['latitude'] = df_position['latitude'].iloc[-1]
                df_value['longitude'] = df_position['longitude'].iloc[-1]
                df_value.rename(columns={'date': 'datetime'}, inplace=True)
                df_value['datetime'] = pd.to_datetime(df_value['datetime'], unit='ms')

                # print(df_value.head())

                
                df_value = df_value[['id', 'station_id', 'datetime', 'value', 'unit', 'type', 'latitude', 'longitude']].copy()
                
                type = df_parameter['name'][0]
                print(type)
                type = type.replace(" ", "")
                print(type)
                if include_historic_data:

                    STANDARD_SKIP_ROWS = 7
                    skip_rows = len(df_position.index) + STANDARD_SKIP_ROWS                
                    historic_dframe = self._fetch_historic_data(station_id, skip_rows, type)
                    print(historic_dframe.head())

                    df_value['datetime'] = pd.to_datetime(df_value['datetime'])
                    historic_dframe['datetime'] = pd.to_datetime(historic_dframe['datetime'])

                    df_value.sort_values(by='datetime', inplace=True)
                    historic_dframe.sort_values(by='datetime', inplace=True)

                    min_date_df1 = df_value['datetime'].min()
                    historical_data_df2 = historic_dframe[historic_dframe['datetime'] < min_date_df1]

                    df_combined = pd.concat([df_value, historical_data_df2], ignore_index=True)
                    columns_to_fillna = ['id', 'station_id', 'unit', 'type', 'latitude', 'longitude']
                    df_combined[columns_to_fillna] = df_combined[columns_to_fillna].ffill()
                
                    df_combined = df_combined.sort_values(by='datetime')
                
                else:
                    df_combined = df_value

                all_data.append(df_combined)

            except requests.exceptions.RequestException as err:
                print(f"Error for station {station_id}: {err}")
                continue
            except Exception as err:
                print(f"Error for station {station_id}: {err}")
                continue

        print(all_data)
        dFrames_all = pd.concat(all_data).sort_values(by=['id', 'datetime']).drop_duplicates().reset_index(drop=True)
        # print(dFrames_all.head())
        dFrames_all['value'] = pd.to_numeric(dFrames_all['value'], errors='coerce')
        dFrames_all['station_id'] = dFrames_all['station_id'].astype(int)

        return dFrames_all
    

    def _fetch_historic_data(self, station_id, skip_rows, type):

        period = 'corrected-archive'
        dFrames = []
        url = f"https://opendata-download-metobs.smhi.se/api/version/latest/parameter/{self.data_type}/station/{station_id}/period/{period}/data.csv"
        response = requests.get(url)
        # print(response.content[0:100])

        try:
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), delimiter=';', skiprows=skip_rows, header=0, low_memory=False) 
            df.columns = df.columns.map(lambda x: x.replace(' ', ''))
            df['datetime'] = df['Datum'] + ' ' + df['Tid(UTC)']

            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
            print(df.head())

            dFrames.append(df)

        except requests.exceptions.RequestException as err:
            print(f"Error for station {station_id}: {err}")
        except KeyError as err:
            print(f"Error for station {station_id}: {err}")
            return None

        df = pd.concat(dFrames)
        df.rename(columns={f'{type}': 'value'}, inplace=True)
        
        df = df[['datetime', 'value']].copy()
        return df

      