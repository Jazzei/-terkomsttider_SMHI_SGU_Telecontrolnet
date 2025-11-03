import sqlite3
import pandera as pa
import pandas as pd
import os
import logging
import datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import Integer, String, Float, DateTime


'''
Lokal databas för att lagra data offline och arbeta i fält utan internetuppkoppling.

Utveckla en databas som kan hantera data från Telecontrolnet, SMHI och SGU.

Telecontrolnet:

    - Lagra anropet från Telecontrolnet och lagra i databasen.

SMHI:

    - Lagra anropet från SMHI (smhi.py) och lagra i databasen.

'''

class Groundwater(Base):
    __tablename__ = "groundwater"

    id: Mapped[str] = mapped_column(Integer, primary_key=True, nullable=False)
    station_id: Mapped[int] = mapped_column(Integer)
    date: Mapped[DateTime] = mapped_column(DateTime)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"Groundwater(id={self.id}, station_id={self.station_id}, date={self.date}, value={self.value}, unit={self.unit}, type={self.type}, latitude={self.latitude}, longitude={self.longitude})"

def main() -> None:
    number_of_stations = int(input("Enter the number of stations: "))

    database_path = "sqlite:///groundwater.db".absolute()
    engine = create_engine(rf"sqlite:///{database_path}", echo=True)

    stmt = select(
        Groundwater.id,
        Groundwater.station_id,

    ).join(Groundwater).filter(Groundwater.station_id == 1)
    



class DatabaseConnection:

    def __init__(self, name, database_path=None):
        if database_path is None:
            cwd = os.getcwd()
            database_path = os.path.abspath(os.path.join(cwd, '..', 'database', f'{name}.db'))
        print(f"Database path: {database_path}")

        self.conn = sqlite3.connect(database_path)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logging.error(f"An error occurred: {exc_value}", exc_info=(exc_type, exc_value, traceback))
        try:
            self.conn.commit()
            self.conn.close()
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {e}")
            raise

    def create_table(self, cursor, table_name):
        # Define the table schema
        table_schema = '''
            id TEXT,
            station_id INTEGER PRIMARY KEY,  
            date TIMESTAMP,           
            value REAL,           
            unit TEXT,
            type TEXT,
            latitude REAL,
            longitude REAL
        '''

        # Create the table if not exists
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({table_schema})')

    def insert_data(self, df, name, database_path=None):
        table_name = name
        
        # Connect to SQLite database
        with DatabaseConnection(name, database_path) as (conn, cursor):
            # Use try-except block for error handling
            try:
                # Ensure the table exists
                self.create_table(cursor, table_name)

                # Validate the data

                validated_df = self.database_validator(df)

                # Insert data into the table
                validated_df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"Data loaded to database {name}")


            except Exception as e:
                print(f"Error loading data to database: {e}")
                raise

    def database_validator(self, df):
        schema = pa.DataFrameSchema(
            columns={
                "id": pa.Column(pa.String, coerce=True),
                "station_id": pa.Column(pa.Int, coerce=True),
                "date": pa.Column(pa.DateTime, coerce=True),
                "value": pa.Column(pa.Float, coerce=True),
                "unit": pa.Column(pa.String, coerce=True),
                "type": pa.Column(pa.String, coerce=True),
                "latitude": pa.Column(pa.Float, coerce=True),
                "longitude": pa.Column(pa.Float, coerce=True),
            }
        )
        validated_df = schema.validate(df)
        return validated_df
    
    def load_data(self, name, database_path=None):
        table_name = name
        with DatabaseConnection(name, database_path) as (conn, cursor):
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                return df
            except Exception as e:
                print(f"Error loading data from database: {e}")
                raise
            

