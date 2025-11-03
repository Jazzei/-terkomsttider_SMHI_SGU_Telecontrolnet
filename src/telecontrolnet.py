import os
import requests
import datetime
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

from scipy.stats import pearsonr
import warnings
from geopy.distance import geodesic
from pydantic import BaseModel, HttpUrl
from typing import List, Optional

from dotenv import load_dotenv
load_dotenv("C:/Users/serojans/hydro_SGU_SMHI_return_periods/.env")


class Datetime:
    def __init__(self, current_date=None) -> None:
        
        self.cwd = os.path.abspath(os.path.dirname(__file__))
        if current_date == None:
            current_date = datetime.datetime.now().date()
        
        self.today = str(current_date)
        self.yesterday = str(current_date - datetime.timedelta(days=1))

class Location(BaseModel):
    code: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    departmentcode: Optional[str] = None
    department: Optional[str] = None
    type: Optional[str] = None
    active: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    zonecode: Optional[str] = None
    zone: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    displaycode: Optional[str] = None
    lastmodified: Optional[str] = None
    lastmodified_uts: Optional[str] = None
    id: Optional[str] = None
    xRd: Optional[float] = None
    yRd: Optional[float] = None

class Tag(BaseModel):
    id: Optional[str]
    name: Optional[str]
    locationid: Optional[str]

class TagsResponse(BaseModel):
    tags: List[Tag]



class fetch_telecontrolnet_data:

    def __init__(self, start_date=None) -> None:
        self.TELECONTROLNET_ID = os.environ.get('TELECONTROLNET_ID')
        self.TELECONTROLNET_API_KEY = os.environ.get('TELECONTROLNET_API_KEY')
        self.TELECONTROLNET_PASSWORD = os.environ.get('TELECONTROLNET_PASSWORD')

        datetime = Datetime()
        self.cwd = datetime.cwd
        self.today = datetime.today
        self.yesterday = start_date
        if self.yesterday == None:
            self.yesterday = '2024-02-05'

    def accesstoken(self):

        def _accesstoken():

                data = {
                    "client_id": self.TELECONTROLNET_ID,
                    "client_secret": self.TELECONTROLNET_API_KEY,
                    "grant_type": "password",
                    "password": self.TELECONTROLNET_PASSWORD,
                    "username": "robin.jansson@vastlanken",
                }
                response = requests.post("https://www.telecontrolnet.nl/oauth/token", data=data)
                if response:
                    print('Success connecting to Telecontrolnet!')
                else:
                    print('An error has occurred when connecting to Telecontrolnet...')
                re = json.loads(response.content)
                access_token = re.get('access_token')

                return access_token 
        
        def _get_locations(access_token: str) -> list[Location]:
            headers = {"Authorization": access_token}
            response = requests.get("https://www.telecontrolnet.nl/api/v1/locations", headers=headers)
            response.raise_for_status()
            locations_data = response.json()
            return [Location(**loc['location']) for loc in locations_data.get("locations", [])]

        
        def _get_tags(access_token: str) -> pd.DataFrame:
            headers = {"Authorization": access_token}
            response_tags = requests.get("https://www.telecontrolnet.nl/api/v1/tags?type=10,12", headers=headers)
            response_tags.raise_for_status()
            tags_data = response_tags.json()

            # Parse JSON response using the Pydantic model
            # tags_response = TagsResponse.parse_obj(tags_data)
            # tags_list = [{'tag.id': tag.id, 'tag.name': tag.name, 'tag.locationid': tag.locationid} for tag in tags_response.tags]
            # tags_df = pd.DataFrame(tags_list)

            tags_df = pd.json_normalize(tags_data['tags'])
            
            tags_mwf = tags_df.loc[tags_df['tag.name'] == 'N1_mwf']
            tags_mwf = tags_mwf[['tag.id', 'tag.locationid']]

            tags_temp = tags_df.loc[tags_df['tag.name'] == 'T1_mwf']
            tags_temp = tags_temp[['tag.id', 'tag.locationid']]

            # tags_df = tags_mwr.merge(tags_temp, on='tag.locationid', how='outer')

            
            return tags_mwf, tags_temp

        def _merge_data(locations: list[Location], tags_df: pd.DataFrame) -> pd.DataFrame:
            data = {'id': [], 'tag_locationid': [], 'name': [], 'x': [], 'y': [], 'city':[], 'active': []}

            for loc in locations:
                data['id'].append(loc.code)
                data['tag_locationid'].append(loc.id)
                data['name'].append(loc.name)
                data['x'].append(loc.x)
                data['y'].append(loc.y)
                data['city'].append(loc.city)
                data['active'].append(loc.active)

            TelecontrolnetTags = pd.DataFrame(data)
            TelecontrolnetTags = TelecontrolnetTags.merge(tags_df, left_on='tag_locationid', right_on='tag.locationid')
            return TelecontrolnetTags

        def _tags(access_token: str) -> tuple[pd.DataFrame, list[Location]]:
            locations = _get_locations(access_token)
            tags_mwr, tags_temp = _get_tags(access_token)
            mwr_tags = _merge_data(locations, tags_mwr)
            temp_tags = _merge_data(locations, tags_temp)
            return mwr_tags, temp_tags
        
        access_token  = _accesstoken()
        tags_mwr, tags_temp = _tags(access_token)

        return access_token, tags_mwr, tags_temp


    def get_data(self, access_token, tags):
            
            # Set the time interval for API call
            to_date = str(datetime.datetime.strptime(self.today, '%Y-%m-%d') + datetime.timedelta(hours=2))
            from_date = str(datetime.datetime.strptime(self.yesterday, '%Y-%m-%d') + datetime.timedelta(hours=2))
            
            # Set the API parameters
            querystring = {"s":f"{from_date}","e":f"{to_date}","ts":"SOME_STRING_VALUE"}
            headers = {"Authorization": access_token}

            def ExtractLevelData(tagid, id_nr):

                url = f"https://www.telecontrolnet.nl/api/v1/tags/{tagid}/trend"
                response = requests.request("GET", url, headers=headers, params=querystring)
                namn = response.text
                namn = json.loads(namn)
                namn = pd.json_normalize(namn)
                namn['id'] = id_nr
                return namn, response

            df_tcn1 = []
            df = tags[['tag.id', 'name']]
            

            for a, b in df.itertuples(index=False):
                x, response = ExtractLevelData(a, b)
                df_tcn1.append(x)

            tcn = pd.concat(df_tcn1)

            return tcn
    
    def megre_frames(self, df_level, df_temp, tags_level):


        def _modify_level_data(df):
            # Convert to datetime and handle timezone formate
            df['logtime'] = pd.to_datetime(df['logtime']).dt.strftime("%Y-%m-%d %H:%M:%S")  
            # Rename columns 
            df = df.rename(columns={'logtime':'datetime', 'logvalue':'m asl'})
            # Convert datetime and value to nummeric 
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['m asl'] = pd.to_numeric(df['m asl'], errors='coerce')
            # Convert centimeter to meter
            df['m asl'] = (df['m asl'] / 100).round(2)
        
            df = df[['id', 'datetime', 'm asl']].copy()
            return df
        
        def _modify_temprature_data(df):
            # Convert to datetime and handle timezone formate
            df['logtime'] = pd.to_datetime(df['logtime']).dt.strftime("%Y-%m-%d %H:%M:%S")  
            # Rename columns 
            df = df.rename(columns={'logtime':'datetime', 'logvalue':'°C'})
            # Convert datetime and value to nummeric 
            df['datetime'] = pd.to_datetime(df['datetime'])

            df['°C'] = pd.to_numeric(df['°C'], errors='coerce').round(1)
            df = df[['id', 'datetime', '°C']].copy()

            return df
        
        df_level = _modify_level_data(df_level)
        df_temp = _modify_temprature_data(df_temp)

        dFrame = df_level.merge(df_temp, on=['id', 'datetime'], how='outer')
        dFrame_level = dFrame.merge(tags_level, on='id', how='left')

        tags_x = dict(zip(tags_level['name'], tags_level['x']))
        tags_y = dict(zip(tags_level['name'], tags_level['y']))
        tags_city = dict(zip(tags_level['name'], tags_level['city']))
        tags_active = dict(zip(tags_level['name'], tags_level['active']))
        tags_id = dict(zip(tags_level['name'], tags_level['id']))

        for i in tags_x.keys():
            dFrame_level.loc[dFrame_level['id'] == i, 'name'] = tags_id[i]
            dFrame_level.loc[dFrame_level['id'] == i, 'x'] = tags_x[i]
            dFrame_level.loc[dFrame_level['id'] == i, 'y'] = tags_y[i]
            dFrame_level.loc[dFrame_level['id'] == i, 'city'] = tags_city[i]
            dFrame_level.loc[dFrame_level['id'] == i, 'active'] = tags_active[i]
            

        dFrame_level = dFrame_level[['name', 'id', 'datetime', 'm asl', '°C', 'x', 'y', 'city', 'active']].copy()
        dFrame_level.rename(columns={'x':'latitude', 'y':'longitude', 'name':'station_id'}, inplace=True)
        dFrame_level = dFrame_level.dropna()

        return dFrame_level
    
    def distance_calculation(self, df1, df2):
    
        df1 = df1.drop_duplicates(subset='id').copy().dropna(subset=['latitude', 'longitude'])
        df2 = df2.drop_duplicates(subset='id').copy().dropna(subset=['latitude', 'longitude'])

        # Create an empty DataFrame to store distances
        distance_df = pd.DataFrame()

        def _haversine_distance(coord1, coord2):
            return geodesic(coord1, coord2).kilometers
        
        # Calculate distances for each unique ID
        for unique_id_1 in df1['id'].unique():
            # Extract coordinates for the current ID from both DataFrames
            coords_df1 = df1.loc[df1['id'] == unique_id_1, ['latitude', 'longitude']].values[0]
            temp_data = {'id': [unique_id_1]}
            for unique_id_2 in df2['id'].unique():
                coords_df2 = df2.loc[df2['id'] == unique_id_2, ['latitude', 'longitude']].values[0]
                # Calculate distance using Haversine formula
                distance = _haversine_distance(coords_df1, coords_df2)
                
                # Store the distance in the temp_data dictionary
                temp_data[f'distance_{unique_id_2}'] = [round(distance, 2)]

            # Convert temp_data to DataFrame and store it in distance_df
            temp_df = pd.DataFrame(temp_data)
            distance_df = pd.concat([distance_df, temp_df])

        # Merge the distance_df with the original df1
        df1 = pd.merge(df1, distance_df, on='id', how='left')

        return df1
    

    def plot_sgu_and_telecontrolnet(self, df_sgu, df_telecontrolnet, coorelation_value=0.7):
        warnings.filterwarnings("ignore", "is_categorical_dtype is deprecated and will be removed in a future version. Use isinstance(dtype, CategoricalDtype) instead.")
        warnings.filterwarnings("ignore", "use_inf_as_na option is deprecated and will be removed in a future version. Convert inf values to NaN before operating instead.")
                
        """
        Plots the data from SGU and Telecontrolnet and calculates the correlation between them.

        Args:
            df_sgu (pd.DataFrame): DataFrame containing SGU data.
            df_telecontrolnet (pd.DataFrame): DataFrame containing Telecontrolnet data.
            coorelation_value (float, optional): Threshold value for correlation. Defaults to 0.7.

        Returns:
            None
            
        """

        sns.set_theme()

        # Plotting on individual figures
        unique_ids = df_telecontrolnet['id'].unique()
        unique_sgu_ids = df_sgu['id'].unique()

        for nr in unique_sgu_ids:
            subset = df_sgu.loc[df_sgu.id == nr]
            
            subset.loc[:,'datetime'] = pd.to_datetime(subset['datetime'], format='%Y-%m-%d %H:%M:%S')
            subset.set_index('datetime', inplace=True)

            # Resample 'm asl' to daily values using mean aggregation
            resampled_sgu = subset['value'].resample('D').mean().reset_index()
            resampled_sgu['datetime'] = pd.to_datetime(resampled_sgu['datetime'].dt.strftime('%Y-%m-%d') + ' 12:00:00')

            # Convert the 'datetime' column back to datetime type
            resampled_sgu['datetime'] = pd.to_datetime(resampled_sgu['datetime'], format='%Y-%m-%d %H:%M:%S')
            resampled_sgu['id'] = nr
            resampled_sgu = resampled_sgu.dropna()
            
        
            for i, unique_id in enumerate(unique_ids):
                
                subset_df = df_telecontrolnet[df_telecontrolnet['id'] == unique_id]
                subset_df.loc[:,'datetime'] = pd.to_datetime(subset_df['datetime'], format='%Y-%m-%d %H:%M:%S')
                subset_df.set_index('datetime', inplace=True)

                # Resample 'm asl' to daily values using mean aggregation
                resampled_df = subset_df['m asl'].resample('D').mean().reset_index()
                resampled_df['datetime'] = pd.to_datetime(resampled_df['datetime'].dt.strftime('%Y-%m-%d') + ' 12:00:00')

                # Convert the 'datetime' column back to datetime type
                resampled_df['datetime'] = pd.to_datetime(resampled_df['datetime'], format='%Y-%m-%d %H:%M:%S')
                resampled_df['id'] = unique_id


                resampled_sgu.loc[:,'datetime'] = pd.to_datetime(resampled_sgu['datetime'], format='%Y-%m-%d %H:%M:%S')
                
                resampled_sgu = resampled_sgu.loc[
                    (resampled_sgu['datetime'] >= resampled_df['datetime'].min()) &
                    (resampled_sgu['datetime'] <= resampled_df['datetime'].max())
                ]
                
                resampled_df = resampled_df.loc[
                    (resampled_df['datetime'] >= resampled_sgu['datetime'].min()) &
                    (resampled_df['datetime'] <= resampled_sgu['datetime'].max())
                ]


                if not resampled_sgu.empty and not resampled_df.empty:
                    scaler_m_asl = StandardScaler()
                    scaler_value = StandardScaler()

                    resampled_sgu['value'] = scaler_value.fit_transform(resampled_sgu[['value']])
                    resampled_df['m asl'] = scaler_m_asl.fit_transform(resampled_df[['m asl']])
                
                
                aligned_df = pd.merge_asof(
                    resampled_sgu.sort_values('datetime'),
                    resampled_df.sort_values('datetime'),
                    on='datetime'
                )
                # Check if 'aligned_df' DataFrame is not empty before calculating correlation
                if len(aligned_df) > 0 and len(aligned_df['value'].dropna()) > 1 and len(aligned_df['m asl'].dropna()) > 1:
                    # Calculate correlation and standardize it
                    aligned_df = aligned_df.replace([np.inf, -np.inf], np.nan).dropna()
                    corr, _ = pearsonr(aligned_df['value'], aligned_df['m asl'])
                    
            
                    if corr > coorelation_value:
                        fig, axes = plt.subplots(nrows=1, figsize=(16, 6))
                        ax1 = axes
                        ax2 = ax1.twinx()

                        sns.lineplot(data=resampled_df, x='datetime', y='m asl', marker='o', ax=ax1, label=unique_id, color='blue')
                        sns.lineplot(data=resampled_sgu, x='datetime', y='value', marker='.', ax=ax2, label=nr, color='orange')

                        ax1.set_title(f'Time Series Plot for {unique_id}')
                        ax1.set_xlabel('Datetime')
                        ax1.set_ylabel('m asl', color='blue')
                        ax2.set_ylabel('m asl', color='orange')

                        ax1.tick_params(axis='y', labelcolor='blue')
                        ax2.tick_params(axis='y', labelcolor='orange')

                        lines, labels = ax1.get_legend_handles_labels()
                        lines2, labels2 = ax2.get_legend_handles_labels()
                        ax2.legend(lines + lines2, labels + labels2, loc='upper right', fontsize=12)
                        
                        
                        textstr = f'Correlation (r): {corr:.2f}\nR-squared: {corr**2:.2f}'
                        ax2.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=12,
                                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))



            plt.tight_layout()
            plt.show()


    def plot_sgu_and_telecontrolnet_meter(self, df_sgu, df_telecontrolnet, coorelation_value=0.7):
            warnings.filterwarnings("ignore", "is_categorical_dtype is deprecated and will be removed in a future version. Use isinstance(dtype, CategoricalDtype) instead.")
            warnings.filterwarnings("ignore", "use_inf_as_na option is deprecated and will be removed in a future version. Convert inf values to NaN before operating instead.")

            sns.set_theme()

            # Plotting on individual figures
            unique_ids = df_telecontrolnet['id'].unique()
            unique_sgu_ids = df_sgu['id'].unique()

            for nr in unique_sgu_ids:
                subset = df_sgu.loc[df_sgu.id == nr]
                
                subset.loc[:,'datetime'] = pd.to_datetime(subset['datetime'], format='%Y-%m-%d %H:%M:%S')
                subset.set_index('datetime', inplace=True)

                # Resample 'm asl' to daily values using mean aggregation
                resampled_sgu = subset['value'].resample('D').mean().reset_index()
                resampled_sgu['datetime'] = pd.to_datetime(resampled_sgu['datetime'].dt.strftime('%Y-%m-%d') + ' 12:00:00')

                # Convert the 'datetime' column back to datetime type
                resampled_sgu['datetime'] = pd.to_datetime(resampled_sgu['datetime'], format='%Y-%m-%d %H:%M:%S')
                resampled_sgu['id'] = nr
                resampled_sgu = resampled_sgu.dropna()
                
            
                for i, unique_id in enumerate(unique_ids):
                    
                    subset_df = df_telecontrolnet[df_telecontrolnet['id'] == unique_id]
                    subset_df.loc[:,'datetime'] = pd.to_datetime(subset_df['datetime'], format='%Y-%m-%d %H:%M:%S')
                    subset_df.set_index('datetime', inplace=True)

                    # Resample 'm asl' to daily values using mean aggregation
                    resampled_df = subset_df['m asl'].resample('D').mean().reset_index()
                    resampled_df['datetime'] = pd.to_datetime(resampled_df['datetime'].dt.strftime('%Y-%m-%d') + ' 12:00:00')

                    # Convert the 'datetime' column back to datetime type
                    resampled_df['datetime'] = pd.to_datetime(resampled_df['datetime'], format='%Y-%m-%d %H:%M:%S')
                    resampled_df['id'] = unique_id


                    resampled_sgu.loc[:,'datetime'] = pd.to_datetime(resampled_sgu['datetime'], format='%Y-%m-%d %H:%M:%S')
                                   
                    
                    aligned_df = pd.merge_asof(
                        resampled_sgu.sort_values('datetime'),
                        resampled_df.sort_values('datetime'),
                        on='datetime'
                    )
                    # Check if 'aligned_df' DataFrame is not empty before calculating correlation
                    if len(aligned_df) > 0 and len(aligned_df['value'].dropna()) > 1 and len(aligned_df['m asl'].dropna()) > 1:
                        # Calculate correlation and standardize it
                        aligned_df = aligned_df.replace([np.inf, -np.inf], np.nan).dropna()
                        corr, _ = pearsonr(aligned_df['value'], aligned_df['m asl'])
                        
                
                        if corr > coorelation_value:
                            fig, axes = plt.subplots(nrows=1, figsize=(16, 6))
                            ax1 = axes
                            ax2 = ax1.twinx()

                            sns.lineplot(data=resampled_df, x='datetime', y='m asl', marker='o', ax=ax1, label=unique_id, color='blue')
                            sns.lineplot(data=resampled_sgu, x='datetime', y='value', marker='.', ax=ax2, label=nr, color='orange')

                            ax1.set_title(f'Time Series Plot for {unique_id}')
                            ax1.set_xlabel('Datetime')
                            ax1.set_ylabel('m asl', color='blue')
                            ax2.set_ylabel('m asl', color='orange')

                            ax1.tick_params(axis='y', labelcolor='blue')
                            ax2.tick_params(axis='y', labelcolor='orange')

                            lines, labels = ax1.get_legend_handles_labels()
                            lines2, labels2 = ax2.get_legend_handles_labels()
                            ax2.legend(lines + lines2, labels + labels2, loc='upper right', fontsize=12)
                            
                            
                            textstr = f'Correlation (r): {corr:.2f}\nR-squared: {corr**2:.2f}'
                            ax2.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=12,
                                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))



                plt.tight_layout()
                plt.show()
            


def main():
    telecontrolnet = fetch_telecontrolnet_data()

    access_token, tags_mwr, tags_temp = telecontrolnet.accesstoken()
    tags_level = telecontrolnet.get_data(access_token, tags_mwr)
    tags_temp = telecontrolnet.get_data(access_token, tags_temp)

    df_level = telecontrolnet.megre_frames(tags_level, tags_temp, tags_level)
    df_level = telecontrolnet.distance_calculation(df_level, df_level)
    


if __name__ == "__main__":
    main()