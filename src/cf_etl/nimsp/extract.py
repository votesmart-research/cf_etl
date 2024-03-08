import json
from pathlib import Path
from collections import defaultdict

# External Libraries and Packages
from tqdm import tqdm

# api.py can only be imported relatively when this module is main
from .api import NIMSPApi, NIMSPJson


def extract_json(nimsp_json: NIMSPJson) -> defaultdict[int, dict[str, str]]:
    """Unwrap the values in the JSON file into records"""
    extracted = defaultdict(dict)

    for record in nimsp_json.records.all:
        # The 'Candidate' Tag is ignored, so not to be confused
        # with Candidate Entity
        record.ignore.append("Candidate")
        for tag in record.all:
            # Not Candidate but Candidate Entity, a Candidate can have many
            # Candidate Entity, since they can hold more than one campaigns
            if tag.name == "Candidate_Entity":
                extracted[record.id]["NIMSP_ID"] = tag.id
            # If we change the way we store CF data (eg. storing in a relational
            # database), the line below may change
            extracted[record.id][tag.name] = tag.value

    return extracted


def extract_json_files(files: list[Path]):
    """Extract from the downloaded JSON files instead"""
    extracted = {}

    for file in files:
        with open(file, "r") as f:
            extracted.update(extract_json(NIMSPJson(json.load(f))))

    return extracted


def save_json(nimsp_json: NIMSPJson, filepath: Path):
    """Save the JSON file into a .json file"""

    filepath.mkdir(exist_ok=True)

    last_updated = nimsp_json.meta_info.reports.last_updated
    current_page = nimsp_json.meta_info.pages.current

    filename = (
        f"NIMSP-Extract_page-{current_page}_"
        f"{last_updated.strftime("%Y-%m-%d-%H%M%S") if last_updated else ''}"
    )

    nimsp_json.export(filepath / f"{filename}.json")


def get_api_report(nimsp_api: NIMSPApi, nimsp_json: NIMSPJson, params: dict):
    """Provides the information about the extraction from the API wrapper"""

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

    # Unpack the rest of the URL parameters and what is being queried
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


def main(api_key, year: int, export_path: Path, json_path: Path = None) -> dict:

    if json_path:
        json_files = filter(
            lambda f: f.name.endswith(".json"),
            (export_path / json_path).iterdir(),
        )
        records_extracted = extract_json_files(
            sorted(json_files, key=lambda x: x.stat().st_ctime)
        )
        return records_extracted

    NIMSPApi.API_KEY = api_key

    api_nimsp = NIMSPApi()

    # Group by candidate, sorts by state, office in an ascending order
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
    print()

    records_extracted = {}

    p_bar = tqdm(total=nimsp_json.meta_info.pages.total, desc="Extracting...")
    last_page = nimsp_json.meta_info.pages.last

    while True:

        # Sometimes the API call returns a blank page, will have to catch that and
        # move on to the next.
        if str(nimsp_json.meta_info) != "null":
            if nimsp_json.meta_info.pages.current <= nimsp_json.meta_info.pages.last:

                records_extracted.update(extract_json(nimsp_json))
                save_json(nimsp_json, filepath=export_path / "JSON_FILES")

                p_bar.update(1)
                nimsp_json, params = api_nimsp.make_call(
                    {"p": nimsp_json.meta_info.pages.current + 1}
                )
            else:
                break
        else:
            # Uses the progress bar current iteration to check with the last page
            if p_bar.n < last_page:
                nimsp_json, params = api_nimsp.make_call({"p": p_bar.n + 1})
                p_bar.update(1)
            else:
                break

    return records_extracted
