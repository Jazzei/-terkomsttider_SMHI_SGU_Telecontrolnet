from matplotlib import axes
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from scipy.stats import pearsonr

import telecontrolnet


class groundwater_return_periods:
    """
    A class for calculating groundwater return periods.

    Attributes:
    - telecontrolnet_instance: An instance of the telecontrolnet class.
    - return_periods: A variable to store return periods after calculation.
    - frequencyfactors: A dictionary of frequency factors for different return intervals.

    Methods:
    - create_overlapping_dataframes: Creates overlapping dataframes based on observation and reference data.
    - process_observed_values: Processes observed values of the reference well.
    """

    def __init__(self):
        """
        Initializes the groundwater_return_periods class.
        """
        self.telecontrolnet_instance = telecontrolnet.fetch_telecontrolnet_data()
        self.return_periods = None
        self.frequencyfactors = {
            10: 1.2816,
            20: 1.6449,
            50: 2.0538,
            100: 2.3264,
            200: 2.5758,
            500: 2.8782,
            2400: 3.20,
        }

    def create_overlapping_dataframes(self, obs_data, ref_data, correlation_threshold=0.5):
        """
        Creates overlapping dataframes based on observation and reference data.

        Parameters:
        - obs_data: DataFrame containing observation data.
        - ref_data: DataFrame containing reference data.
        - correlation_threshold: Threshold for correlation value.

        Returns:
        - overlapping_dfs: List of overlapping dataframes containing matching above correlation threshold 
        observation and refrences wells.
        """
         # Convert 'datetime' to datetime type
        obs_data['datetime'] = pd.to_datetime(obs_data['datetime'])
        ref_data['datetime'] = pd.to_datetime(ref_data['datetime'])

        # Get unique IDs from observation and reference data
        unique_obs_ids = obs_data['id'].unique()
        # np.random.shuffle(unique_obs_ids)
        unique_ref_ids = ref_data['id'].unique()

        # Create a list to store overlapping dataframes
        overlapping_dfs = []

        # Check for overlapping date range for each unique ID
        for obs_id in unique_obs_ids:
            
            obs_date_range = obs_data[obs_data['id'] == obs_id]['datetime']

            # Drop any missing values before creating the IntervalIndex
            obs_date_range = obs_date_range.dropna()

            obs_start = obs_date_range.min()
            obs_end = obs_date_range.max()

            for ref_id in unique_ref_ids:
                
                ref_date_range = ref_data[ref_data['id'] == ref_id]['datetime']

                # Drop any missing values before creating the IntervalIndex
                ref_date_range = ref_date_range.dropna()

                ref_start = ref_date_range.min()
                ref_end = ref_date_range.max()

                overlap = not (obs_end < ref_start or obs_start > ref_end)

                # print(f"Wells: {obs_id} & {ref_id} overlap: {overlap}\n")


                if overlap:
                    print(f"Wells: {obs_id} & {ref_id} overlap: {overlap}\n")

                    # def _plot1(obs_df, ref_df):
                    #     fig, axes = plt.subplots(nrows=1, figsize=(16, 8))
                    #     ax2 = axes.twinx()

                    #     sns.lineplot(data=obs_df, x='datetime', y='m asl', marker='o', ax=axes, color='blue', label=f'Observation {obs_df.id.iloc[0]}')
                    #     sns.lineplot(data=ref_df, x='datetime', y='value', marker='.', ax=ax2, color='orange', label=f'Reference {ref_df.id.iloc[0]}')


                    #     plt.tight_layout()
                    #     plt.show()

                    obs_df = obs_data[obs_data['id'] == obs_id]
                    ref_df = ref_data[ref_data['id'] == ref_id]


                    

                    # _plot1(obs_df, ref_df)

                    aligned_df = pd.merge_asof(
                        obs_df.sort_values('datetime'),
                        ref_df.sort_values('datetime'),
                        on='datetime',
                        # tolerance=pd.Timedelta('15 days')
                    )

                    # def _plot(obs_df, ref_df, aligned_df, corr):
                    #     fig, axes = plt.subplots(nrows=2, figsize=(16, 8))
                    #     ax1 = axes[0]  # First subplot
                    #     ax1_1 = ax1.twinx()
                    #     ax2 = axes[1]  # Second subplot
                    #     ax2_1 = ax2.twinx()

                    #     sns.lineplot(data=obs_df, x='datetime', y='m asl', marker='o', ax=ax1, color='blue', label=f'Observation {obs_df.id.iloc[0]}')
                    #     sns.lineplot(data=ref_df, x='datetime', y='value', marker='.', ax=ax1_1, color='orange', label=f'Reference {ref_df.id.iloc[0]}')

                    #     sns.lineplot(data=aligned_df, x='datetime', y='m asl', marker='o', ax=ax2, color='blue', label=f'Aligned Observation {obs_df.id.iloc[0]}')
                    #     sns.lineplot(data=aligned_df, x='datetime', y='value', marker='.', ax=ax2_1, color='orange', label=f'Aligned Reference {ref_df.id.iloc[0]}')

                    #     ax1.set_title(f'Time Series Plot for {obs_id} and {ref_id}')
                    #     ax1.set_xlabel('Datetime')
                    #     ax1.set_ylabel('m asl', color='blue', )
                    #     ax1_1.set_ylabel('m asl', color='orange')

                    #     ax2.set_title(f'Aligned Time Series Plot for {obs_id} and {ref_id} with Correlation: {corr:.2f}')
                    #     ax2.set_xlabel('Datetime')
                    #     ax2.set_ylabel('m asl', color='blue')
                    #     ax2_1.set_ylabel('m asl', color='orange')

                    #     ax1.tick_params(axis='y', labelcolor='blue')
                    #     ax1_1.tick_params(axis='y', labelcolor='orange')
                    #     ax2.tick_params(axis='y', labelcolor='blue')
                    #     ax2_1.tick_params(axis='y', labelcolor='orange')

                    #     ax1.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
                    #     ax1_1.legend(loc='center left', bbox_to_anchor=(1.1, 0.4))
                    #     ax2.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
                    #     ax2_1.legend(loc='center left', bbox_to_anchor=(1.1, 0.4))

                    #     plt.tight_layout()
                    #     plt.show()

                    

                    pd.set_option('future.no_silent_downcasting', True)
                    aligned_df = aligned_df.replace([np.inf, -np.inf], np.nan).dropna().copy()
                    corr = None
                    
                    # Check if both arrays have at least two data points
                    if len(aligned_df['value']) >= 2 and len(aligned_df['m asl']) >= 2:
                        corr, p_value  = pearsonr(aligned_df['value'], aligned_df['m asl'])

                        # print(f"OBS well: {obs_df.head(2)} \nREF well {ref_df.head(2)}\nCorrelation: {corr}, P-value: {p_value}\n{aligned_df.head(2)}")

                    if corr is not None and corr > correlation_threshold:
                        # _plot(obs_df, ref_df, aligned_df, corr)
                        
                        obs_df = obs_df.copy()
                        ref_df = ref_df.copy()
                        obs_df['coorelation'] = corr
                        ref_df['coorelation'] = corr
                        obs_df['probability'] = p_value 
                        ref_df['probability'] = p_value
                        filtered_obs, filtered_ref = self.compare_and_filter_variation(obs_df, ref_df)

                        # print(f"obs: {filtered_obs} /nref:{filtered_ref}")
                    
                        if filtered_obs is not None and filtered_ref is not None:
                            
                            return_time, standard_deviation, max_values_by_year, frequencyfactors, Y_RmaxT, S_tr = self.calculate_return_periods(filtered_ref, filtered_obs)
                            filtered_obs.loc[:, 'ref_id'] = ref_id
                            filtered_obs.loc[:, 'obs_id'] = obs_id
                            filtered_obs.loc[:, 'return_time'] = return_time                     
                            filtered_obs.loc[:, 'standard_deviation'] = standard_deviation
                            
                            filtered_obs.loc[:, 'Y_RmaxT'] = Y_RmaxT
                            filtered_obs.loc[:, 'S_tr'] = S_tr
                            
#                             print(f"filtered_obs {filtered_obs}")
#                             print(f"filtered_ref {filtered_ref}")
                            
                            overlapping_dfs.append((filtered_obs, filtered_ref))

        
        return overlapping_dfs

    def calculate_return_periods(self, referens_data, observation_data, hydrological_start_month=10, return_time=2400):
        """
        Processes observed values of the reference well.

        Parameters:
        - referens_data: DataFrame with columns 'datetime', 'value'.
        - observation_data: DataFrame with columns 'datetime', 'value'.
        - hydrological_start_month: Start month of the hydrological year (October).
        - return_time: Return time for calculating return period.

        Returns:
        - return_time: Return time for the maximum value.
        - standard_deviation: Standard deviation of the maximum values.
        - max_values_by_year: DataFrame with columns 'rank', 'max_value', 'probability'.
        - frequencyfactors: Frequency factor for the return time.
        - Y_RmaxT: Y value for the return time.
        - S_tr: S value for the return time.
        """

        # Convert 'datetime' to datetime format
        referens_data['datetime'] = pd.to_datetime(referens_data['datetime'])
        observation_data['datetime'] = pd.to_datetime(observation_data['datetime'])

        # Extract hydrological year from the observation date
        referens_data['hydrological_year'] = np.where(referens_data['datetime'].dt.month >= hydrological_start_month,
                                                    referens_data['datetime'].dt.year,
                                                    referens_data['datetime'].dt.year - 1)


        observation_data['hydrological_year'] = np.where(observation_data['datetime'].dt.month >= hydrological_start_month,
                                                    observation_data['datetime'].dt.year,
                                                    observation_data['datetime'].dt.year - 1)
        
        # Group data by hydrological year and find the maximum value in each year
        max_values_by_year = referens_data.groupby('hydrological_year')['value'].max().reset_index()


        # Sort values in descending order to rank them
        max_values_by_year = max_values_by_year.sort_values(by='value', ascending=False).reset_index(drop=True)

        # Assign ranks to sorted values
        max_values_by_year['rank'] = max_values_by_year.index + 1

        # Calculate plotting positions using Weibull formula
        max_values_by_year['probability'] = (len(max_values_by_year) + 1 - max_values_by_year['rank']) / (len(max_values_by_year) + 1)
        
        # Calculate return period using the provided formula (equation 7)
        max_values_by_year['return_period'] = 1 / max_values_by_year['probability']

        # Create a DataFrame with the required columns
        plotting_positions = max_values_by_year[['rank', 'value', 'probability']].rename(columns={'value': 'max_value'})

        standard_deviation = Smax = plotting_positions['max_value'].std()
        
        # Set frequency factor for the return time
        frequencyfactors = self.frequencyfactors.get(return_time)
        
#         print(f"frequencyfactors {frequencyfactors}")
        # 
        Y_RmaxT = plotting_positions['max_value'].mean() + frequencyfactors * Smax

        S_tr = Y_RmaxT - plotting_positions['max_value'].max()

        # Calculate the return time for the maximum value 
        return_time = Y0_max_T = observation_data['m asl'].max() + S_tr * ((observation_data['m asl'].max() - observation_data['m asl'].min()) / (plotting_positions['max_value'].max() - plotting_positions['max_value'].min()))


        referens_data_id = referens_data.id.unique()[0]
        observation_data_id = observation_data.id.unique()[0]
        
#         print('referens well: ', referens_data_id
#               , '\nobservation well: ', observation_data_id
#               , '\nReturn time 50 years: ', Y0_max_T
#               )
        
        return return_time, standard_deviation, max_values_by_year, frequencyfactors, Y_RmaxT, S_tr
    
    def compare_and_filter_variation(self, observations_data, reference_data):
        """
        Filters data based on specified criteria for reference and observation datasets.

        Parameters:
        - referens_data: DataFrame with columns 'observation_date', 'variations', and 'reference_lifetime'.
        - observations_data: DataFrame with columns 'observation_date', 'variations'.

        Returns:
        - filtered_referens: DataFrame after applying filters and interpolation for reference data.
        - filtered_observations: DataFrame after applying filters and interpolation for observation data.
        """
        # Convert 'datetime' to datetime format for both datasets
        reference_data['datetime'] = pd.to_datetime(reference_data['datetime'])
        observations_data['datetime'] = pd.to_datetime(observations_data['datetime'])

        # Set the date frequency to 'MS' (Month Start) to check for monthly observations for both datasets
        reference_data.set_index('datetime', inplace=True)
        observations_data.set_index('datetime', inplace=True)

        # Resample only numeric columns
        reference_data_resampled = reference_data.select_dtypes(include=[np.number]).resample('MS').max()
        observations_data_resampled = observations_data.select_dtypes(include=[np.number]).resample('MS').max()

        # Calculate the lifetime variation range for reference and observation datasets
        lifetime_variation_range_reference = reference_data_resampled['value'].max() - reference_data_resampled['value'].min()
        lifetime_variation_range_observation = observations_data_resampled['m asl'].max() - observations_data_resampled['m asl'].min()

        print(f"lifetime_variation_range_reference: {lifetime_variation_range_reference:.2f}, lifetime_variation_range_observation: {lifetime_variation_range_observation:.2f}")

        # Set the maximum allowed variation as 30% of the variation range for the entire lifetime
        max_variation_observation = 1.3 * lifetime_variation_range_reference

        # Check if the observation well's variation is within the allowed range
        if lifetime_variation_range_observation <= max_variation_observation:
            # Filter data based on variations for reference_data
            filtered_reference = reference_data[abs(reference_data['value'] - reference_data['value'].mean()) <= max_variation_observation].copy()
            
            filtered_reference.infer_objects(copy=False)
            filtered_reference = filtered_reference.interpolate(method='linear')

            observations_data.infer_objects(copy=False)
            filtered_observations = observations_data.interpolate(method='linear')

            # Reset index for final result for both datasets
            filtered_reference.reset_index(inplace=True)
            filtered_observations.reset_index(inplace=True)

            return filtered_observations, filtered_reference
        else:
            print(f"Reference well {reference_data.id.iloc[0]} has too high variation compared to the observation well {observations_data.id.iloc[0]}.")
            return None, None
        

    def filter_reference_wells_not_within_distance(self, observation_wells, sgu_data_modify, distance=50):
            """
            Applies a filter to the groundwater data based on distance and time criteria.

            Args:
                observation_wells (DataFrame): DataFrame containing observation well data.
                sgu_data_modify (DataFrame): DataFrame containing SGU data.

            Returns:
                DataFrame: Filtered DataFrame containing reference well data.
            """
            distance_to_refrence_well = self.telecontrolnet_instance.distance_calculation(observation_wells, sgu_data_modify)

            result = distance_to_refrence_well.drop(columns=['id', 'comment', 'm asl', 'datetime','latitude','longitude', 'quality', 'top_of_casing (m asl)', 'soil_type', 'aquifer_type', 'topographic_location'])
            columns_to_check = result.columns

            result[columns_to_check] = result[columns_to_check].map(lambda x: x if x <= distance else pd.NA)
            result = result.dropna(axis=1, how='all')
            sgu_refrence_wells = [item.replace('distance_', '') for item in result.columns]

            refrence_wells = sgu_data_modify.loc[sgu_data_modify.id.isin(sgu_refrence_wells)].dropna(subset='value').reset_index(drop=True)


            def _filter_refrence_wells_below_20_years(refrence_wells):
                refrence_wells['datetime'] = pd.to_datetime(refrence_wells['datetime'])
                grouped_data = refrence_wells.groupby('id')
                # Calculate the difference between min and max datetime for each group
                time_difference = grouped_data['datetime'].max() - grouped_data['datetime'].min()

                # Filter the groups where the time difference is equal to or greater than 20 years
                filtered_groups = time_difference[time_difference >= pd.Timedelta('7300 days')].reset_index()
                filtered_groups_list = filtered_groups.id.unique()

                refrence_wells = refrence_wells.loc[refrence_wells.id.isin(filtered_groups_list)].copy()

                return refrence_wells


            refrence_wells_ = _filter_refrence_wells_below_20_years(refrence_wells)
            return refrence_wells_


    def plot_return_periods(self, overlapping_dfs, savefig=False):
        """
        Plots the time series of observed and reference groundwater levels for each pair of overlapping dataframes.
        
        Parameters:
        - overlapping_dfs (list): A list of overlapping dataframes containing groundwater level data.
        - savefig (bool, optional): If True, saves the plot as an image file. Default is False.
        
        Returns:
        None
        """
        for i in range(len(overlapping_dfs)):
            overlapping_dfs_ = pd.concat(overlapping_dfs[i])
            
            obs = overlapping_dfs_.loc[overlapping_dfs_.id == overlapping_dfs_.obs_id.iloc[i]]
            ref = overlapping_dfs_.loc[overlapping_dfs_.id == overlapping_dfs_.ref_id.iloc[i]]
                                                                                    
            
            fig, axes = plt.subplots(nrows=1, figsize=(16, 6))
            ax1 = axes
            ax2 = ax1.twinx()

            sns.lineplot(data=obs, x='datetime', y='m asl', marker='o', ax=ax1, label=overlapping_dfs_.obs_id.iloc[i], color='blue')
            sns.lineplot(data=ref, x='datetime', y='value', marker='.', ax=ax2, label=f'{overlapping_dfs_.ref_id.iloc[i]}\nSoil type: {ref.soil_type.iloc[0]}\nAquifer: {ref.aquifer_type.iloc[0]}\nTopographic: {ref.topographic_location.iloc[0]}', color='orange')


            ax1.set_title(f'Time Series Plot for {overlapping_dfs_.obs_id.iloc[i]} and {overlapping_dfs_.ref_id.iloc[i]}')
            ax1.set_xlabel('Datetime')
            ax1.set_ylabel('m asl', color='blue', )
            ax2.set_ylabel('m asl', color='orange')

            ax1.tick_params(axis='y', labelcolor='blue')
            ax2.tick_params(axis='y', labelcolor='orange')
            
            corr = overlapping_dfs_.coorelation.iloc[0]
            ax1.axhline(y=obs.return_time.iloc[0], color='red', linestyle='--', label=f"Return Period 2400 year (m asl): {obs.return_time.iloc[0]:.2f}\nCorrelation (r): {corr:.2f}\nP-value: {obs.probability.iloc[0]:.3f}")


            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper left', fontsize=12, bbox_to_anchor=(1.05, 0.65))
            
            plt.tight_layout()
            if savefig:
                plt.savefig(f"Time_Series_{overlapping_dfs_.obs_id.iloc[i]}_{overlapping_dfs_.ref_id.iloc[i]}.jpg")
            plt.show()



