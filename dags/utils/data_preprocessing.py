# import libraries
import pandas as pd
import numpy as np
from pathlib import Path

# Custom imports
import dags.utils.config as config
from dags.utils.log_config import setup_logging
from dags.utils.helper import load_data_from_pickle, save_data_to_pickle

# Logger setup for data preprocessing
logger = setup_logging(config.PROJECT_ROOT, "data_preprocessing.py")
DATA_DIR = config.DATA_DIR

def data_preprocess_pipeline(data_input, data_output):

    """
    Load, preprocess, and save the dataframe.

    Args:
        data_input (str): Path to the input pickle file containing the dataframe.
        data_output (str): Path to save the preprocessed dataframe as a pickle file.
    """

    try:
        # Load data from pickle file
        df = load_data_from_pickle(data_input)

        # Preprocess the dataframe
        columns_to_drop = ['SBP', 'DBP', 'EtCO2', 'BaseExcess', 'HCO3',
                           'pH', 'PaCO2', 'Alkalinephos', 'Calcium',
                           'Magnesium', 'Phosphate', 'Potassium', 'PTT',
                           'Fibrinogen', 'Unit1', 'Unit2']
        df["Unit"] = df["Unit1"] + df["Unit2"]

        # Drop redundant columns
        df.drop(columns=columns_to_drop, inplace=True)
        grouped_by_patient = df.groupby('Patient_ID')

        # Impute missing values with forward and backward fill
        df = grouped_by_patient.apply(lambda x: x.bfill().ffill()).reset_index(drop=True)

        # Drop columns with more than 25% null values and 'Patient_ID'
        columns_with_nulls = ['TroponinI', 'Bilirubin_direct', 'AST', 'Bilirubin_total',
                              'Lactate', 'SaO2', 'FiO2', 'Unit', 'Patient_ID']
        df.drop(columns=columns_with_nulls, inplace=True)

        # Apply log transformation to normalize specific columns
        columns_to_normalize = ['MAP', 'BUN', 'Creatinine', 'Glucose', 'WBC', 'Platelets']
        for col in columns_to_normalize:
            df[col] = np.log1p(df[col])

        # One-hot encode the 'Gender' column
        df = pd.get_dummies(df, columns=['Gender'], drop_first=True)

        # Drop remaining rows with any NaN values
        df.dropna(inplace=True)

        # Save the preprocessed dataframe to a pickle file
        save_data_to_pickle(df, data_output)

    except KeyError as ke:
        logger.error("KeyError during preprocessing: %s", ke)
    except ValueError as ve:
        logger.error("ValueError during preprocessing: %s", ve)
    except Exception as ex:
        logger.error("An unexpected error occurred during preprocessing: %s", ex)
        raise
