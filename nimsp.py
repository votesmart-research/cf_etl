import sys
from pathlib import Path

import pandas
from nimsp.api import NIMSPJson
from nimsp.extractor import main as extract
from nimsp.transformer import main as transform
from nimsp.loader import main as nimsp_load

from datetime import datetime


TIMESTAMP = datetime.strftime(datetime.now(), '%Y-%m-%d')


def save_extract(records_extract:dict):

    df_extract = pandas.DataFrame.from_dict(records_extract, orient='index')

    EXTRACT_FILES = EXPORT_DIR / 'EXTRACT_FILES'
    EXTRACT_FILES.mkdir(exist_ok=True)

    df_extract.to_csv(EXTRACT_FILES / f"{TIMESTAMP}_NIMSP_Extract.csv", index=False)


def save_json(nimsp_json:NIMSPJson):

    JSON_FILES = EXPORT_DIR / 'JSON_FILES'
    JSON_FILES.mkdir(exist_ok=True)

    last_updated = nimsp_json.meta_info.reports.last_updated
    current_page = nimsp_json.meta_info.pages.current

    filename = f"{last_updated.strftime('%Y-%m-%d-%H%M%S') if last_updated else ''}_NIMSP_page-{current_page}"
    
    nimsp_json.export(JSON_FILES / f"{filename}.json")


def save_transformed(records_transformed):

    df_transformed = pandas.DataFrame.from_dict(records_transformed, orient='index')

    TRANSFORMED_FILES = EXPORT_DIR / 'TRANSFORMED_FILES'
    TRANSFORMED_FILES.mkdir(exist_ok=True)

    df_transformed.to_csv(TRANSFORMED_FILES / f"{TIMESTAMP}_NIMSP_Transformed.csv", index=False)


def save_verified(records_verified:dict, records_queried:dict):

    df_verified = pandas.DataFrame.from_dict(records_verified, orient='index')
    df_queried = pandas.DataFrame.from_dict(records_queried, orient='index')

    VERIFIED_FILES = EXPORT_DIR / 'VERIFIED_FILES'
    VERIFIED_FILES.mkdir(exist_ok=True)

    df_verified.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_NIMSP_Matched.csv", index=False)
    df_queried.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_NIMSP_Query.csv", index=False)


def main():

    records_extracted, json_extract = extract(YEAR)

    for e in json_extract:
        save_json(e)
    
    save_extract(records_extracted)

    records_transformed = transform(records_extracted)
    save_transformed(records_transformed)

    records_verified, records_queried = nimsp_load(records_transformed)
    save_verified(records_verified, records_queried)


if __name__ == '__main__':
    _, EXPORT_DIR, YEAR = sys.argv
    EXPORT_DIR = Path(EXPORT_DIR)
    main()