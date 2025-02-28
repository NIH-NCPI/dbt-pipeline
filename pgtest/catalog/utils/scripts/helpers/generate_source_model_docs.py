import yaml
import os
import csv
import pandas as pd
from helpers.general import *


def load_column_data(data_dictionary, study_id):
    """Loads column names, descriptions, and data types from CSV files once and stores them in a dictionary."""
    column_data = {}

    for table_id, table_info in data_dictionary.items():
        raw_table_id = f"{study_id}_raw_{table_id}"
        ddict = table_info.get("table_details")
        df = read_file(ddict)

        columns = []
        for _, row in df.iterrows():
            col_name = row["variable_name"]
            col_name_code = col_name.lower().replace(" ", "_")
            col_description = row.get("variable_description", "UNKNOWN_VARIABLE_DESCRIPTION")
            col_data_type = row.get("data_type", "UNKNOWN").lower() 
            
            # Store column metadata
            columns.append((col_name, col_name_code, col_description, col_data_type))

        column_data[raw_table_id] = columns

    return column_data


def generate_dbt_models_yml(data_dictionary, column_data, output_dir, study_id):
    """Generates dbt models.yml file for each table in its respective directory."""

    for table_id, table_info in data_dictionary.items():
        raw_table_id = f"{study_id}_raw_{table_id}"
        # Create a dictionary for just this table
        models = {
            "version": 2,
            "models": [
                {
                    "name": raw_table_id,
                    "description": f'{{{{ doc("{raw_table_id}_description") }}}}',
                    "columns": [
                        {
                            "name": col_name,
                            "description": f'{{{{ doc("{col_name_code}") }}}}',
                            "data_type": col_data_type
                        }
                        for col_name, col_name_code, col_description, col_data_type in column_data.get(raw_table_id, [])
                    ]
                }
            ]
        }

        table_models_dir = f"{output_dir}/{table_id}"
        filename = "__models.yml"

        write_file(table_models_dir, filename, models)

def generate_column_descriptions(data_dictionary, column_data, output_dir, study_id):
    """Generates a separate column_descriptions.md for each table in its respective docs directory."""

    for table_id, table_info in data_dictionary.items():
        raw_table_id = f"{study_id}_raw_{table_id}"
        descriptions = []

        # Table description
        table_description = table_info.get("description", f"Model for {raw_table_id}.")
        descriptions.append(f"{{% docs {raw_table_id}_description %}}\n{table_description}\n{{% enddocs %}}\n")

        # Column descriptions
        for col_name, col_name_code, col_description, _ in column_data.get(raw_table_id, []):
            descriptions.append(f"{{% docs {col_name_code} %}}\n{col_description}\n{{% enddocs %}}\n")

        data = "\n".join(descriptions)

        table_docs_dir = f"{output_dir}/{table_id}/docs"
        filename = "column_descriptions.md"

        write_file(table_docs_dir, filename, data)

def generate_model_descriptions(data_dictionary, output_dir, study_id):
    """Generates model_descriptions.md using the specified format."""
    model_descriptions = []

    # Group tables by prefix (e.g., "moo_raw_", "moo_stg_")
    grouped_tables = {}
    for table_id, table_info in data_dictionary.items():
        prefix = table_id.split("_")[0]  # Assumes prefix is the first part of table_id
        grouped_tables.setdefault(prefix, []).append((table_id, table_info))

    for prefix, tables in grouped_tables.items():
        model_descriptions.append(f"### {prefix.capitalize()} Models\n")

        for table_id, table_info in tables:
            raw_table_id = f"{study_id}_raw_{table_id}"
            description = table_info.get("description", f"Model for {raw_table_id}.")
            model_descriptions.append(f"{{% docs {raw_table_id} %}}\n{description}\n{{% enddocs %}}\n")

            data = "\n".join(model_descriptions)

            filename = "model_descriptions.md"

            write_file(output_dir, filename, data)

def generate_raw_sql_files(data_dictionary, output_dir, db_name, study_id):
    """Generates SQL files dynamically for each table in its respective directory."""

    for table_id in data_dictionary.keys():
        raw_table_id = f"{study_id}_raw_{table_id}"
        sql_filename = f"{raw_table_id}.sql"
        sql_content = f"""{{{{ config(materialized='table') }}}}

SELECT * FROM {db_name}.{study_id}_raw_data.{table_id}
"""
        # Define table-specific SQL directory
        table_sql_dir = f"{output_dir}/{table_id}"

        write_file(table_sql_dir, sql_filename, sql_content)

def generate_model_docs(study_config, table_id, models_dir, outer_docs_dir, db_name):
    """Main function to generate dbt model files, loading column data once."""

    data_dictionary = study_config.get("data_dictionary", {})

    study_id = study_config.get("study_id", "study")

    column_data = load_column_data(data_dictionary, study_id) 

    generate_dbt_models_yml(data_dictionary, column_data, models_dir, study_id)
    generate_column_descriptions(data_dictionary, column_data, models_dir, study_id)
    generate_model_descriptions(data_dictionary, outer_docs_dir, study_id)
    generate_raw_sql_files(data_dictionary, models_dir, db_name, study_id)
