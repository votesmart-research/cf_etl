import re
from pathlib import Path
from datetime import datetime

# External Libraries and Packages
import pandas
from unidecode import unidecode


NIMSP_ID = "NIMSP_ID"
NAME = "Candidate_Entity"
OFFICE = "Office_Sought"
PARTY = "Specific_Party"
STATE = "Election_Jurisdiction"
ELECTION_YEAR = "Election_Year"
ELECTION_TYPE = "Election_Type"
ELECTION_STAGE = "Election_Status"
ELECTION_STATUS = "Status_of_Candidate"


COLUMNS_TO_RENAME = {
    ELECTION_YEAR: "election_year",
    PARTY: "party",
    STATE: "state_id",
}

title_case = lambda x: x.title().strip() if isinstance(x, str) else x


def transform_name(series: pandas.Series) -> pandas.DataFrame:
    """Splits the name into first, middle, nick and last names"""

    suffix = r"\b(?P<suffix>[IVX][IVX]+$|[DJMS][RS][S]?[\.]?$)"
    lastname = lambda x: re.sub(rf"{suffix}|\(.*\)", "", x) if x else ""
    middlename = r"\b(?P<middlename>[A-Z]{1}$)\b"
    nickname = r"[\"\'\(](?P<nickname>.*?)[\"\'\)]"
    firstname = lambda x: re.sub(f"{middlename}|{nickname}", "", x) if x else ""

    series = series.apply(lambda x: unidecode(x))

    df_name_split = series.str.split(pat=", ", expand=True)
    series_firstname = df_name_split[1].apply(firstname).rename("firstname")
    series_middlename = df_name_split[1].str.extract(middlename)["middlename"]
    series_lastname = df_name_split[0].apply(lastname).rename("lastname")
    series_suffix = df_name_split[0].str.extract(suffix)["suffix"]
    series_nickname = df_name_split[1].str.extract(nickname)["nickname"]

    return pandas.concat(
        [
            series_firstname.apply(title_case),
            series_middlename.apply(title_case),
            series_lastname.apply(title_case),
            series_suffix.apply(title_case),
            series_nickname.apply(title_case),
        ],
        axis=1,
    )


def get_election_info(series: pandas.Series) -> pandas.DataFrame:
    """Uses regex to split series into office and district"""

    office = r"(?P<office>.*(?=DISTRICT)|.*(?!=DISTRICT))"
    district = r"(?P<district>(?<=DISTRICT).+)"

    df_office_split = series.str.split(pat="-", expand=True)
    series_office = df_office_split[0].str.extract(office)["office"]
    series_district = df_office_split[0].str.extract(district)["district"]

    return pandas.concat(
        [
            series_office.apply(title_case),
            series_district.apply(title_case),
        ],
        axis=1,
    )


def main(records_extracted: dict) -> dict:

    df = pandas.DataFrame.from_dict(records_extracted, orient="index")

    df_name = transform_name(df[NAME])
    df_info = get_election_info(df[OFFICE])

    df_transformed = pandas.concat(
        [
            df_name,
            df_info,
            df[PARTY].apply(title_case),
            df[STATE],
            df[ELECTION_YEAR],
            df[NIMSP_ID],
        ],
        axis=1,
    )

    df_transformed.rename(columns=COLUMNS_TO_RENAME, inplace=True)
    
    records_transformed = (
        df_transformed.astype(str).replace("nan", "").to_dict(orient="index")
    )

    return records_transformed
