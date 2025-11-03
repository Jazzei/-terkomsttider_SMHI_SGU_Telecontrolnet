import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import seaborn as sns
import pandas as pd
import numpy as np
import math
from scipy.stats import linregress
import itertools


def plot_groundwater_level(
    groundwater_data, precipitation_data, sgu_data, start_date=None, end_date=None
):
    # Data processing
    df_start_to_end_date = groundwater_data.loc[
        (groundwater_data['datetime'] >= start_date)
        & (groundwater_data['datetime'] <= end_date)
    ].reset_index(drop=True)

    df_groundwater = df_start_to_end_date[['id', 'datetime', 'value']].copy()
    df_groundwater = df_groundwater.dropna(subset=['value', 'datetime'])
    df_groundwater['datetime'] = pd.to_datetime(df_groundwater['datetime'])
    df_groundwater.set_index('datetime', inplace=True)
    df_groundwater = df_groundwater.resample('D')['value'].mean().reset_index()

    df_precipitation = precipitation_data.loc[
        (precipitation_data.datetime >= start_date)
        & (precipitation_data.datetime <= end_date)
    ].copy().reset_index(drop=True)
    df_precipitation['datetime'] = pd.to_datetime(df_precipitation['datetime'])

    df_precipitation.set_index('datetime', inplace=True)
    df_precipitation = df_precipitation.resample('D')['value'].sum().reset_index()
    
    date_range = precipitation_data['datetime'].max() - precipitation_data['datetime'].min()
    num_days = date_range.days
    bar_width = math.ceil(num_days / len(precipitation_data))

   
    markers_array = ['o', '-', 'x', '+', 'v', '^', '<', '>', 's', 'd', 'p', '*']
    marker_size = 4 
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'black', 'yellow']


    sgu_df = sgu_data.loc[
        (sgu_data['datetime'] >= sgu_data['datetime'].min())
        & (sgu_data['datetime'] <= end_date)
    ].reset_index(drop=True)

    sgu_df = sgu_df[['id', 'datetime', 'value']].copy()
    sgu_df = sgu_df.dropna(subset=['value', 'datetime'])
    sgu_df['datetime'] = pd.to_datetime(sgu_df['datetime'])
    sgu_df.set_index('datetime', inplace=True)
    sgu_df = sgu_df.resample('D')['value'].mean().reset_index()
        

    # Plotting
    sns.despine(top=True)
    sns.set_theme(font_scale=1.3)
    sns.set_style('whitegrid', {"grid.color": "0.6", "grid.linestyle": ":"})

    fig, axs = plt.subplots(1, 1, figsize=(16, 6), dpi=300)
    axs2 = axs.twinx()
    axs2.bar(
        df_precipitation['datetime'],
        df_precipitation['value'].astype(float),
        width=int(bar_width),
        alpha=0.5,
        color='lightblue',
        label='Precipitation',
    )

    axs.plot(
        df_groundwater['datetime'],
        df_groundwater['value'],
        label=df_groundwater.id.unique()[0],
        lw=3,
        alpha=0.9,
        marker=markers_array[0],
        markersize=marker_size,
    )
    for index, i in enumerate(sgu_df.id.unique()):
        subset = sgu_df.loc[sgu_df['id'] == i]

        axs.plot(
            subset['datetime'],
            subset['value'],
            label=i,
            lw=3,
            alpha=0.9,
            marker=markers_array[index + 1],
            markersize=marker_size,
            colors  = colors[index + 1]
        )


    axs.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
    axs.set_ylabel(' m asl ', fontsize='16', labelpad=15)
    axs2.set_ylabel(' mm ', fontsize='16', rotation=-90, labelpad=25)

    if df_precipitation.value.astype(float).max() < 25:
        axs2.set_ylim(0, 25)
    elif df_precipitation.value.astype(float).max() < 50:
        axs2.set_ylim(0, df_precipitation.value.astype(float).max() + 10)
    else:
        axs2.set_ylim(0, 50)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    plt.tight_layout()
    plt.show()

def plot_only_groundwater_level(groundwater_data):
    # Data processing
    groundwater_data_ = groundwater_data[['id', 'datetime', 'value']].copy()
    df_groundwater = groundwater_data_.dropna(subset=['value', 'datetime'])
    df_groundwater['datetime'] = pd.to_datetime(df_groundwater['datetime'])
    
    
    markers_array = ['o', 'x', '+', 'v', '^', '<', '>', 's', 'd', 'p', '*']
    marker_size = 4 
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'black', 'yellow']
    
    
    sns.despine(top=True)
    sns.set_theme(font_scale=1.3)
    sns.set_style('whitegrid', {"grid.color": "0.6", "grid.linestyle": ":"})

    marker_cycle = itertools.cycle(markers_array)
    color_cycle = itertools.cycle(colors)
    
    for i in df_groundwater.id.unique():
        
        marker = next(marker_cycle)
        color = next(color_cycle)
        
        
        subset = df_groundwater.loc[df_groundwater.id == i].copy()
        subset.set_index('datetime', inplace=True)
        subset = subset.resample('D')['value'].mean().reset_index()
  
        fig, axs = plt.subplots(1, 1, figsize=(16, 6), dpi=300)

        axs.plot(
            subset['datetime'],
            subset['value'],
            label=i,
            lw=3,
            alpha=0.9,
#             marker=marker,
            markersize=marker_size,
            color=color
        )


        axs.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
        axs.set_ylabel(' m asl ', fontsize='16', labelpad=15)

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
        plt.tight_layout()
        plt.show()


def plot_groundwater_return_period(overlapping_dfs, savefig=False):

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
