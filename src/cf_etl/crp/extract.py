from pathlib import Path

# External Libraries and Packages
import pandas
import numpy


STARTING_ROW = 14
STARTING_COLUMN = 1


def main(crp_file: Path) -> dict[int, dict[str, str]]:
    """Cleans the file: remove blank rows and columns"""
    df_crp = pandas.read_excel(crp_file, header=None)

    df_extracted = df_crp.iloc[STARTING_ROW:, STARTING_COLUMN:].reset_index(drop=True)
    df_extracted.rename(df_crp.iloc[STARTING_ROW - 1], axis="columns", inplace=True)

    df_extracted.replace(numpy.nan, "", inplace=True)

    records_extracted = df_extracted.to_dict(orient="index")

    return records_extracted
