import re

# External Libraries and Packages
import pandas
from unidecode import unidecode


CRP_ID = "CID"
NAME = "CRPName"
PARTY = "Party"
DISTRICT = "DistIDRunFor"
FEC_ID = "FECCandID"

COLUMNS_TO_RENAME = {PARTY: "party", DISTRICT: "district"}


VALUES_TO_REPLACE = {
    PARTY: {
        "D": "Democratic",
        "I": "Independent",
        "L": "Libertarian",
        "R": "Republican",
        "3": "Other",
    },
    DISTRICT: {
        "S": "U.S. Senate",
        "S0": "U.S. Senate",
        "S1": "U.S. Senate",
        "S2": "U.S. Senate",
        "ES": "President",
    },
}


def transform_name(series: pandas.Series) -> pandas.DataFrame:
    """Splits the name into first, middle, nick and last names"""

    strip_nonwords = lambda x: x.strip(" .") if isinstance(x, str) else x
    middlename = r"(\w+\s+\b)(?P<middlename>[A-Z]{1}\.?)\b"
    nickname = r"[\"\'\(](?P<nickname>.*?)[\"\'\)]"
    suffix = r"\s+(?P<suffix>[IVX][IVX]+$|[DJMS][rs][s]?[\.]?)|[M][\.][D][\.]?"
    firstname = lambda x: (
        re.sub(f"{middlename}|{nickname}|{suffix}", r"\1", x)
        if isinstance(x, str)
        else x
    )

    series = series.apply(lambda x: unidecode(x))

    df_name_split = series.str.split(pat=",", expand=True).apply(
        lambda x: x.apply(strip_nonwords)
    )
    series_firstname = df_name_split[1].apply(firstname).rename("firstname")
    series_middlename = df_name_split[1].str.extract(middlename)["middlename"]
    series_nickname = df_name_split[1].str.extract(nickname)["nickname"]
    series_suffix = df_name_split[1].str.extract(suffix)["suffix"]
    series_lastname = df_name_split[0].rename("lastname")

    return pandas.concat(
        [
            series_firstname.apply(strip_nonwords),
            series_middlename.apply(strip_nonwords),
            series_lastname.apply(strip_nonwords),
            series_suffix.apply(strip_nonwords),
            series_nickname.apply(strip_nonwords),
        ],
        axis=1,
    )


def get_election_info(series: pandas.Series) -> pandas.DataFrame:
    """Use regex to split apart series to state, district and office"""

    state_id = r"(?P<state_id>^..)"
    district = rf"(?P<{DISTRICT}>..$)"
    office = lambda x: re.sub("^\d+$", "U.S. House", x)

    series_state = series.str.extract(state_id)["state_id"]
    series_district = series.str.extract(district)[DISTRICT]
    series_office = series_district.replace(VALUES_TO_REPLACE[DISTRICT]).apply(office)

    presidential_index = series_office.loc[series_office == "President"].index
    series_state[presidential_index] = "NA"

    return pandas.concat(
        [
            series_state,
            series_office.rename("office"),
            series_district.apply(lambda x: re.sub("^0+|(ES)|[S]\d?", "", x)),
        ],
        axis=1,
    )


def main(records_extracted: dict[int, dict[str, str]]) -> dict[int, dict[str, str]]:

    df = pandas.DataFrame.from_dict(records_extracted, orient="index")

    df_name = transform_name(df[NAME])
    df_info = get_election_info(df[DISTRICT])

    df_transformed = pandas.concat(
        [
            df_name,
            df_info,
            df[PARTY],
            df[CRP_ID],
            df[FEC_ID],
        ],
        axis=1,
    )

    df_transformed.replace(VALUES_TO_REPLACE, inplace=True)
    df_transformed.rename(columns=COLUMNS_TO_RENAME, inplace=True)

    records_transformed = (
        df_transformed.astype(str).replace("nan", "").to_dict(orient="index")
    )

    return records_transformed
