# Built-in packages
from pathlib import Path
from datetime import datetime

# External packages and libraries
import pandas

# Internal packages and libraries
from nimsp.api import NIMSPJson
from nimsp.extractor import main as extract
from nimsp.transformer import main as transform
from nimsp.matched import main as nimsp_load


TIMESTAMP = datetime.strftime(datetime.now(), "%Y-%m-%d")


def save_extract(records_extract: dict):

    df_extract = pandas.DataFrame.from_dict(records_extract, orient="index")

    EXTRACT_FILES = EXPORT_DIR / "EXTRACT_FILES"
    EXTRACT_FILES.mkdir(exist_ok=True)

    df_extract.to_csv(EXTRACT_FILES / f"{TIMESTAMP}_NIMSP_Extract.csv", index=False)


def save_json(nimsp_json: NIMSPJson):

    JSON_FILES = EXPORT_DIR / "JSON_FILES"
    JSON_FILES.mkdir(exist_ok=True)

    last_updated = nimsp_json.meta_info.reports.last_updated
    current_page = nimsp_json.meta_info.pages.current

    filename = f"{last_updated.strftime('%Y-%m-%d-%H%M%S') if last_updated else ''}_NIMSP_page-{current_page}"

    nimsp_json.export(JSON_FILES / f"{filename}.json")


def save_transformed(records_transformed):

    df_transformed = pandas.DataFrame.from_dict(records_transformed, orient="index")

    TRANSFORMED_FILES = EXPORT_DIR / "TRANSFORMED_FILES"
    TRANSFORMED_FILES.mkdir(exist_ok=True)

    df_transformed.to_csv(
        TRANSFORMED_FILES / f"{TIMESTAMP}_NIMSP_Transformed.csv", index=False
    )


def save_verified(records_verified: dict, records_queried: dict):

    df_verified = pandas.DataFrame.from_dict(records_verified, orient="index")
    df_queried = pandas.DataFrame.from_dict(records_queried, orient="index")

    VERIFIED_FILES = EXPORT_DIR / "VERIFIED_FILES"
    VERIFIED_FILES.mkdir(exist_ok=True)

    df_verified.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_NIMSP_Matched.csv", index=False)
    df_queried.to_csv(VERIFIED_FILES / f"{TIMESTAMP}_NIMSP_Query.csv", index=False)



def save_records(records: dict[int, dict[str, str]], filepath: Path, filename: str=None):

    filepath.mkdir(exist_ok=True)

    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

    df = pandas.DataFrame.from_dict(records, orient='index')
    df.to_csv(
        filepath / f"{filename if filename else "records"}_{timestamp}.csv",
        index=False,
    )
    
def save_json(nimsp_json: NIMSPJson, filepath: Path, filename: str=None):

    last_updated = nimsp_json.meta_info.reports.last_updated
    current_page = nimsp_json.meta_info.pages.current

    filename = f"{last_updated.strftime('%Y-%m-%d-%H%M%S') if last_updated else ''}_NIMSP_page-{current_page}"

    nimsp_json.export(filepath / f"{filename}.json")



def main(year, export_dir):

    records_extracted, json_extract = extract(year)

    for e in json_extract:
        save_json(e)

    save_extract(records_extracted)

    records_transformed = transform(records_extracted)
    save_transformed(records_transformed)

    records_verified, records_queried = nimsp_load(records_transformed)
    save_verified(records_verified, records_queried)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(prog="campaign_finance_nimsp")

    parser.add_argument(
        "-e",
        "--export_dir",
        type=Path,
        required=True,
        help="Path of the directory where the exported file goes.",
    )
    parser.add_argument(
        "-y",
        "--year",
        required=True,
        help="Election year(s) of candidates in the file.",
    )

    args = parser.parse_args()

    EXPORT_DIR = args.exportdir
    YEAR = args.year

    main(args.export_dir)
