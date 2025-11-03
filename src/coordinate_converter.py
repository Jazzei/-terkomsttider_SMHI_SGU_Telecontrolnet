from geopy.geocoders import OpenCage
import os
from math import radians, sin, cos, sqrt, atan2
from pyproj import CRS, Transformer
import pandas as pd
from geopy.distance import geodesic

class convert_coordinate:

    def __init__(self) -> None:
        self.api_key = os.environ.get('OPENCAGE_API_KEY')
          

    def sweref_to_lat_lon(self, df):

    
        # Define the CRS for the source (sweref99)
        sweref99 = CRS.from_string("EPSG:3006") # +proj=utm +zone=33 +ellps=GRS80 +units=m +no_defs

        # Define the CRS for the target (WGS84)
        wgs84 = CRS.from_string("EPSG:4326")

        # Create a transformer
        transformer = Transformer.from_crs(sweref99, wgs84, always_xy=True)

        # df['longitude'], df['latitude'] = transformer.transform(
        #     df['E'].values, df['N'].values
        # )
        df[['longitude', 'latitude']] = df.apply(lambda row: pd.Series(transformer.transform(row['E'], row['N'])), axis=1)


        return df
    

    
    def sweref_1200_to_lat_lon(self, df):

    
        # Define the CRS for the source (sweref99)
        sweref99 = CRS.from_string("EPSG:3007")

        # Define the CRS for the target (WGS84)
        wgs84 = CRS.from_string("EPSG:4326")

        # Create a transformer
        transformer = Transformer.from_crs(sweref99, wgs84, always_xy=True)

        df['longitude'], df['latitude'] = transformer.transform(
            df['E'].values, df['N'].values
        )
      
        return df

    def haversine(self, lat1, lon1, lat2, lon2):
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Radius of Earth in kilometers is 6371
        distance = 6371 * c  
        return distance

    def find_closest_coordinate(self, target, coordinates):
        min_distance = float('inf')
        closest_coordinate = None

        for coord in coordinates:
            distance = self.haversine(target[0], target[1], coord[0], coord[1])
            if distance < min_distance:
                min_distance = distance
                closest_coordinate = coord

        return closest_coordinate


    def get_reverse_geocode(self, df, coordinates):

        geolocator = OpenCage(api_key=self.api_key)
        location = geolocator.reverse(coordinates, language='swe')
            
        df['address'] = location.address
        
        # df = self.expand_address(df)

        return df

    def expand_address(self, df):
        split_result = df['address'].str.split(', ', expand=True)
        # If you have three components, assign them to respective columns
        df[['place', 'street', 'postal_city', 'country']] = split_result.iloc[:, :4]

        split_result_1  = df['postal_city'].str.split(' ', expand=True)
        df[['postal_1', 'postral_2', 'city']] = split_result_1.iloc[:, :3]
        df.drop(columns=['postal_1', 'postral_2', 'postal_city', 'street', 'country'], inplace=True)

        df = df[['id', 'station_id', 'date', 'value', 'unit', 'type', 'latitude', 'longitude', 'place', 'city', 'address']].copy()

        return df


    def set_closest_coordinate_true(self, df, closest_coordinate):
        df['closet_coordinate'] = False
        df.loc[(df.latitude == closest_coordinate[0]) & (df.longitude == closest_coordinate[1]), 'closet_coordinate'] = True
        
        return df
    
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





