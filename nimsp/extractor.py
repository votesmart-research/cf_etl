from pathlib import Path
from datetime import datetime
from collections import defaultdict

# External Libraries and Packages
import pandas
from tqdm import tqdm

try:
    from .api import NIMSPApi, NIMSPJson
except ImportError:
    from nimsp.api import NIMSPApi, NIMSPJson


def extract_json(nimsp_json: NIMSPJson):

    extracted = defaultdict(dict)

    for record in nimsp_json.records.select():
        record.ignore.append("Candidate")
        for tag in record.select():
            if tag.name == "Candidate_Entity":
                extracted[record.id]["NIMSP_ID"] = tag.id
            extracted[record.id][tag.name] = tag.value

    return extracted


def save_json(nimsp_json: NIMSPJson, filepath: Path, filename: str=None):

    last_updated = nimsp_json.meta_info.reports.last_updated
    current_page = nimsp_json.meta_info.pages.current

    filename = f"{last_updated.strftime('%Y-%m-%d-%H%M%S') if last_updated else ''}_NIMSP_page-{current_page}"

    nimsp_json.export(filepath / f"{filename}.json")


def load_api_key():

    script_dir = Path(__file__).parent
    api_key_filepath = script_dir / "API_KEY"

    with open(api_key_filepath, "r") as f:
        NIMSPApi.API_KEY = f.readline()


def get_api_report(nimsp_api: NIMSPApi, nimsp_json: NIMSPJson, params: dict):

    d = {
        "Base URL": [
            nimsp_api.url,
        ],
        "Last Updated": [
            str(nimsp_json.meta_info.reports.last_updated),
        ],
        "Total Pages": [
            nimsp_json.meta_info.pages.total,
        ],
        "Total Records": [
            nimsp_json.meta_info.pages.total_records,
        ],
    }
    param_d = defaultdict(list)

    for token_name, token_value in params.items():

        _token_name = nimsp_api.TOKEN_REF.get(token_name)
        value_ref = nimsp_api.TOKEN_VALUE_REF.get(token_name)

        token_values = token_value.split(",")

        for v in token_values:
            _token_value = (
                value_ref.get(v) if value_ref else nimsp_api.TOKEN_REF.get(v) or v
            )
            param_d[_token_name].append(_token_value)

    d.update(param_d)

    return d


def main(year: int) -> dict:

    load_api_key()

    api_nimsp = NIMSPApi()

    # group by candidates; sort by state, office in ascending order
    api_nimsp.build(
        {
            "y": year,
            "gro": "c-t-id",
            "so": "s,c-r-oc",
            "sod": 1,
        }
    )

    nimsp_json, params = api_nimsp.make_call()

    api_report = get_api_report(api_nimsp, nimsp_json, params)

    for name, l in api_report.items():
        print(f"\033[1m\n{name}:\033[0m")
        for value in l:
            print(f"{' '*4}{value}")

    records_extracted = {}
    json_extracted = []

    p_bar = tqdm(total=nimsp_json.meta_info.pages.total, desc="Extracting...")
    last_page = nimsp_json.meta_info.pages.last

    while True:

        if str(nimsp_json.meta_info) != "null":
            if nimsp_json.meta_info.pages.current <= nimsp_json.meta_info.pages.last:

                records_extracted.update(extract_json(nimsp_json))
                json_extracted.append(nimsp_json)

                p_bar.update(1)
                nimsp_json, params = api_nimsp.make_call(
                    {"p": nimsp_json.meta_info.pages.current + 1}
                )
            else:
                break
        else:
            if p_bar.n < last_page:
                nimsp_json, params = api_nimsp.make_call({"p": p_bar.n + 1})
                p_bar.update(1)
            else:
                break

    return records_extracted, json_extracted


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(prog="nimsp_extractor")
    args = parser.parse_args()

    parser.add_argument(
        "-e",
        "--export_dir",
        type=Path,
        required=True,
        help="Path of the directory where the exported file goes.",
    )
    parser.add_argument(
        "-y",
        "--years",
        required=True,
        nargs="+",
        help="Election year(s) of candidates in the file.",
    )

    records_extracted, json_extract = main(args.years, args.export_dir)

    for e in json_extract:
        save_json(e, args.export_dir / "JSON_FILES", "NIMSP_JSON")

    df_extracted = pandas.DataFrame.from_dict(records_extracted, orient='index')
    df_extracted.to_csv(
            args.export_dir / f"NIMSP_Extract_{datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")}.csv",
            index=False,
        )
