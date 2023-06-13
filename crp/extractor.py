import pandas
import numpy
from pathlib import Path


STARTING_ROW = 14
STARTING_COLUMN = 1


def save_extract(records_extract:dict):

    df = pandas.DataFrame.from_dict(records_extract, orient='index')

    EXTRACT_FILES = EXPORT_DIR / 'EXTRACT_FILES'
    EXTRACT_FILES.mkdir(exist_ok=True)

    df.to_csv(EXTRACT_FILES / f"CRP_Extract.csv", index=False)


def main(crp_file):
    df_crp = pandas.read_excel(crp_file, header=None)

    df_extracted = df_crp.iloc[STARTING_ROW:, STARTING_COLUMN:].reset_index(drop=True)
    df_extracted.rename(df_crp.iloc[STARTING_ROW-1], axis='columns', inplace=True)

    df_extracted.replace(numpy.NAN, '', inplace=True)

    records_extracted = df_extracted.to_dict(orient='index')

    return records_extracted


if __name__ == '__main__':

    import sys

    _, EXPORT_DIR, CRP_FILE = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)
    CRP_FILE = Path(CRP_FILE)

    records_extracted = main(CRP_FILE)

    save_extract(records_extracted)