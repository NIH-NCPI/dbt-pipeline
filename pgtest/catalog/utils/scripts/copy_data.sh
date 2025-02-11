#!/bin/bash

# Define your PostgreSQL connection parameters
DB_HOST="localhost"
DB_USER="gutmanb"
DB_NAME="default_db"


# Insert the SQL generated by process_data.py.
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY dbo_raw_data.participants_m00m002 (\"Study Code\", \"Participant Global ID\", \"Participant External ID\", \"Family ID\", \"Family Type\", \"Father ID\", \"Mother ID\", \"Sibling ID\", \"Other Family Member ID\", \"Family Relationship\", \"Sex\", \"Race\", \"Ethnicity\", \"Down Syndrome Status\", \"Age at First Patient Engagement\", \"First Patient Engagement Event\", \"Outcomes Vital Status\", \"Age at Last Vital Status\")
    FROM 'data/participants_M00M00.csv'
    DELIMITER ',' 
    CSV HEADER;
    ;"
