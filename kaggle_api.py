import os
import json
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi

load_dotenv()

# Initialize and authenticate the API
api = KaggleApi()
api.authenticate()

# Example 1: List datasets (e.g., searching for covid datasets)
datasets = api.dataset_list(search='covid')
for dataset in datasets:
    print(dataset.ref)

# Example 2: Download a specific dataset
api.dataset_download_files('blastchar/telco-customer-churn', path='./data', unzip=True)