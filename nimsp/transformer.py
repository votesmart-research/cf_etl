import re
import pandas
import numpy
from pathlib import Path


NIMSP_ID = 'Candidate_Entity_id'
NAME = 'Candidate_Entity'
OFFICE = 'Office_Sought'
PARTY = 'Specific_Party'
STATE = 'Election_Jurisdiction'
ELECTION_YEAR = 'Election_Year'
ELECTION_TYPE = 'Election_Type'
ELECTION_STAGE = 'Election_Status'
ELECTION_STATUS = 'Status_of_Candidate'


COLUMNS_TO_RENAME = {NIMSP_ID: 'NIMSP_ID',
                     ELECTION_YEAR: 'election_year',
                     PARTY: 'party',
                     STATE: 'state_id',
                     }

title_case = lambda x: x.title().strip() if isinstance(x, str) else x


def transform_name(series:pandas.Series) -> pandas.DataFrame:

    suffix = r'\b(?P<suffix>[IVX][IVX]+$|[DJMS][RS][S]?[\.]?$)'
    lastname = lambda x: re.sub(fr"{suffix}|\(.*\)", "", x) if x else ""
    middlename = r'\b(?P<middlename>[A-Z]{1}$)\b'
    nickname = r'[\"\'\(](?P<nickname>.*?)[\"\'\)]'
    firstname = lambda x: re.sub(f"{middlename}|{nickname}", "", x) if x else ""

    df_name_split = series.str.split(pat=', ', expand=True)
    series_firstname = df_name_split[1].apply(firstname).rename('firstname')
    series_middlename = df_name_split[1].str.extract(middlename)['middlename']
    series_lastname = df_name_split[0].apply(lastname).rename('lastname')
    series_suffix = df_name_split[0].str.extract(suffix)['suffix']
    series_nickname = df_name_split[1].str.extract(nickname)['nickname']


    return pandas.concat([series_firstname.apply(title_case),
                          series_middlename.apply(title_case),
                          series_lastname.apply(title_case),
                          series_suffix.apply(title_case),
                          series_nickname.apply(title_case),
                          ],
                          axis=1)


def get_office_district(series:pandas.Series) -> pandas.DataFrame:

    office = r'(?P<office>.*(?=DISTRICT)|.*(?!=DISTRICT))'
    district = r'(?P<district>(?<=DISTRICT ).+)'

    df_office_split = series.str.split(pat='-', expand=True)
    series_office = df_office_split[0].str.extract(office)['office']
    series_district = df_office_split[0].str.extract(district)['district']


    return pandas.concat([series_office.apply(title_case),
                          series_district.apply(title_case),
                          ],
                          axis=1)


def save_transformed(records_transformed):
    
    df = pandas.DataFrame.from_dict(records_transformed, orient='index')

    TRANSFORMED_FILES = EXPORT_DIR / 'TRANSFORMED_FILES'
    TRANSFORMED_FILES.mkdir(exist_ok=True)

    df.to_csv(TRANSFORMED_FILES / f"NIMSP_Transformed.csv", index=False)


def main(records_extracted:dict) -> dict:

    df = pandas.DataFrame.from_dict(records_extracted, orient='index')

    df_name = transform_name(df[NAME])
    df_office_district = get_office_district(df[OFFICE])

    df.rename(columns=COLUMNS_TO_RENAME, inplace=True)

    df_transformed = pandas.concat([df_name,
                                    df_office_district,
                                    df['party'].apply(title_case),
                                    df['state_id'],
                                    df['election_year'],
                                    df['NIMSP_ID'],
                                    ],
                                    axis=1)
    
    # Empty df cells will need replaced with empty string for tabular matcher to work
    # correctly
    df_transformed.replace(numpy.NAN, '', inplace=True)
    
    records_transformed = df_transformed.to_dict(orient='index')
    return records_transformed


if __name__ == '__main__':
    import sys

    _, EXPORT_DIR, EXTRACT_FILE = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)
    EXTRACT_FILE = Path(EXTRACT_FILE)

    df_extract = pandas.read_csv(EXTRACT_FILE)
    records_extracted = df_extract.to_dict(orient='index')

    records_transformed = main(records_extracted)

    save_transformed(records_transformed)