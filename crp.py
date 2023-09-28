import sys
import pandas

from pathlib import Path

from crp.extractor import main as extract
from crp.loader import main as crp_load
from crp.transformer import main as transform

from datetime import datetime

TIMESTAMP = datetime.strftime(datetime.now(), '%Y-%m-%d')

def save_extract(records_extract:dict):

    df = pandas.DataFrame.from_dict(records_extract, orient='index')

    EXTRACT_FILES = EXPORT_DIR / 'EXTRACT_FILES'
    EXTRACT_FILES.mkdir(exist_ok=True)

    df.to_csv(EXTRACT_FILES / f"{TIMESTAMP}_CRP_Extract.csv", index=False)


def save_transformed(records_transformed):

    df_transformed = pandas.DataFrame.from_dict(records_transformed, orient='index')

    TRANSFORMED_FILES = EXPORT_DIR / 'TRANSFORMED_FILES'
    TRANSFORMED_FILES.mkdir(exist_ok=True)

    df_transformed.to_csv(TRANSFORMED_FILES / f"{TIMESTAMP}_CRP_Transformed.csv", index=False)


def save_verified(records_verified:dict, records_queried:dict):

    df_verified = pandas.DataFrame.from_dict(records_verified, orient='index')
    df_queried = pandas.DataFrame.from_dict(records_queried, orient='index')

    VERIFIED_FILES = EXPORT_DIR / 'VERIFIED_FILES'
    VERIFIED_FILES.mkdir(exist_ok=True)

    df_verified.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_CRP_Matched.csv", index=False)
    df_queried.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_CRP_Query.csv", index=False)


def main():

    records_extracted = extract(CRP_FILE)
    save_extract(records_extracted)

    records_transformed = transform(records_extracted)
    save_transformed(records_transformed)

    records_verified, records_queried = crp_load(records_transformed, *YEARS)
    save_verified(records_verified, records_queried)


if __name__ == '__main__':

    _, EXPORT_DIR, CRP_FILE, *YEARS = sys.argv
    
    if not YEARS:
        print("Please enter at least one election year after"
              " extract file parameter")
        exit()

    EXPORT_DIR = Path(EXPORT_DIR)
    CRP_FILE = Path(CRP_FILE)
    
    main()