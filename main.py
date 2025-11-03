from src import coordinate_converter, groundwater_calculation, groundwater_level_plotter, sgu, smhi, sqlite, telecontrolnet

from dotenv import load_dotenv
load_dotenv(".env")



import os

SGU = sgu.fetch_sgu_data()
SMHI = smhi.fetch_smhi_data()


def main_telecontrolnet():

    database_path = os.path.abspath(os.path.join(os.getcwd(), 'database', 'telecontrolnet.db'))
    
    telecontrolnet_instance = telecontrolnet.fetch_telecontrolnet_data()
                
    access_token, tags_mwf, tags_temp = telecontrolnet_instance.accesstoken()
    df_level = telecontrolnet_instance.get_data(access_token, tags_mwf)
    df_temp = telecontrolnet_instance.get_data(access_token, tags_temp)
        
    df_level_ = telecontrolnet_instance.megre_frames(df_level, df_temp, tags_mwf)

    # Create a new SQLite database and insert data
    with sqlite.DatabaseConnection('telecontrolnet', database_path) as (conn, cursor):
        df_level_.to_sql('observation_database', conn, index=False, if_exists='replace')



def main():

    if not os.path.exists('database'):
        os.makedirs('database')

    database_path = os.path.abspath(os.path.join(os.getcwd(), 'database', 'telecontrolnet.db'))

    if not os.path.exists(database_path):
        telecontrolnet_instance = telecontrolnet.fetch_telecontrolnet_data()
                
        access_token, tags_mwf, tags_temp = telecontrolnet_instance.accesstoken()
        df_level = telecontrolnet_instance.get_data(access_token, tags_mwf)
        df_temp = telecontrolnet_instance.get_data(access_token, tags_temp)
            
        df_level_ = telecontrolnet_instance.megre_frames(df_level, df_temp, tags_mwf)

        # Create a new SQLite database and insert data
        with sqlite.DatabaseConnection('telecontrolnet', database_path) as (conn, cursor):
            df_level_.to_sql('observation_database', conn, index=False, if_exists='replace')


    else:
        print("Database already exists.")

    # elif os.path.exists('database/telecontrolnet.db'):


    # if not os.path.exists('database/sgu.db'):
        
    #     sgu_instance = sgu.fetch_sgu_data()
    #     sgu_stations = sgu_instance.fetch_stations('14')
    #     print(sgu_stations.head())

    #     sgu_rawdata = sgu_instance.fetch_measurements(sgu_stations)
    #     print(sgu_rawdata.head())

    #     sgu_dFrame = sgu_instance.convert_columns_to_standard(sgu_rawdata)
    #     print(sgu_dFrame.head())
    #     sqlite.insert_data(sgu_dFrame, 'sgu')


        # elif not os.path.exists('database/smhi.db'):
        
        #     smhi.set_data_type('precipitation')
        #     dFrame_smhi = smhi.fetch_smhi_data(include_historic_data=True)
        #     sqlite.DatabaseConnection('smhi')
        #     sqlite.insert_data(dFrame_smhi, 'smhi')
    #     elif not os.path.exists('database/telecontrolnet.db'):

    #         access_token, tags_mwf, tags_temp = telecontrolnet.accesstoken()
    #         df_level = telecontrolnet.get_data(access_token, tags_mwf)
    #         # df_temp = telecontrolnet.get_data(access_token, tags_temp)

            
    #         df_level = telecontrolnet.megre_frames(df_level, df_temp, tags_mwf)
    #         df_level = telecontrolnet.distance_calculation(df_level, df_level)



    
    # coordinate_converter = coordinate_converter.geolocator()
    # groundwater_calculation = groundwater_calculation.GroundwaterReturnPeriods()

    # database = sqlite.DatabaseConnection('groundwater_level')



if __name__ == '__main__':
    main()


'''

# TO-DO

Telecontrolnet:

    - Observationsdata från Telecontrolnet ska hämtas och lagras i en lokal databas.

    - Lagra anropet från Telecontrolnet i lokal databas (hur struktureras databasen bäst?). Prioritet medel.

    - Inkludera även lufttrycksdata från Telecontrolnet. Priotet låg.

    - Filtrera data, flertalet av observationerna är inte relevanta. Detta då då GDTerna (sensorn) kan ha varit installerad i flera brunnar. 
        Därmed återspeglar en del av observationerna inte grundvattennivån i nuvarande observationsbrunn. En del av observationerna 
        är även felaktiga då de inte kompenserats gentemot rörets över kant. Prioritet hög.

   # Detta är ett massivt dataset. För att kunna beräkna återkomsttider enligt Chalmersmodellen i alla lämpliga observationsrör behövs bra 
        filter för in data. Chalmersmodellen kanske inte är den bästa metoden men en standard i geoteknik om inte långa tidserier för att 
        beräkna dimiensioneradefinns grundevattennivå. Efter 3 månader med med två observationer i månaden går det att passa data mot lämpligt SGU referensrör. 
        
SGU:

    - Lämplig referensdata skall lagras i en lokal databas.

SMHI:

    - Nederbördsdata från SMHI ska hämtas och lagras i en lokal databas. (Möjligen lufttryck och temperatur också)

coordinate_converter:

    Referensdata från SGU ska hämtas och lagras i en databas.

    - Lagra anropet från SGU (sgu.py) och lagra i databasen.


'''