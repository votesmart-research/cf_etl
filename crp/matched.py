import json
from pathlib import Path

import pg8000
import pandas
from rapidfuzz import fuzz
from tqdm import tqdm

from tabular_matcher import records
from tabular_matcher.matcher import TabularMatcher, MatcherConfig


def connect_to_database():
    PACKAGE_DIR = Path(__file__).parent.parent
    CONNECTION_INFO_FILEPATH = PACKAGE_DIR / "connection_info.json"

    with open(CONNECTION_INFO_FILEPATH, "r") as f:
        connection_info = json.load(f)

    return pg8000.connect(**connection_info, timeout=10)


def query_from_database(query: str, connection: pg8000.Connection):
    cursor = connection.cursor()
    cursor.execute(query)
    headers = [str(k[0]) for k in cursor.description]
    return {
        index: dict(zip(headers, row)) for index, row in enumerate(cursor.fetchall())
    }


def load_query_string(query_filename: Path):
    PACKAGE_DIR = Path(__file__).parent.parent
    with open(PACKAGE_DIR / "queries" / query_filename, "r") as f:
        query_string = f.read()

    return query_string


def save_verified(records_verified: dict, records_queried: dict):

    df_verified = pandas.DataFrame.from_dict(records_verified, orient="index")
    df_queried = pandas.DataFrame.from_dict(records_queried, orient="index")

    VERIFIED_FILES = EXPORT_DIR / "VERIFIED_FILES"
    VERIFIED_FILES.mkdir(exist_ok=True)

    df_verified.to_csv(VERIFIED_FILES / f"CRP_Matched.csv", index=False)
    df_queried.to_csv(VERIFIED_FILES / f"CRP_Queried.csv", index=False)


def match(records_crp: dict, records_ec: dict):

    tb_config = MatcherConfig()
    tb_matcher = TabularMatcher(tb_config)

    tb_matcher.x_records = records_crp
    tb_matcher.y_records = records_ec

    tb_config.scorers_by_column.SCORERS.update(
        {"WRatio": lambda x, y: fuzz.WRatio(str(x), str(y))}
    )
    tb_config.scorers_by_column.default = "WRatio"
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match["firstname"] = "nickname", "middlename"

    tb_config.columns_to_group["state_id"] = "state_id"
    tb_config.columns_to_get["candidate_id"] = "candidate_id"

    tb_config.thresholds_by_column["lastname"] = 88
    tb_config.thresholds_by_column["suffix"] = 90
    tb_config.thresholds_by_column["state_id"] = 100
    tb_config.thresholds_by_column["district"] = 98
    tb_config.thresholds_by_column["party"] = 95
    tb_config.thresholds_by_column["office"] = 100

    tb_matcher.required_threshold = 85
    tb_matcher.duplicate_threshold = 3

    p_bar = tqdm(total=len(records_crp))

    matched_records, match_info = tb_matcher.match(update_func=lambda: p_bar.update(1))

    return matched_records, match_info


def verify(records_matched: dict, records_finsource: dict, col_name: str):
    """Adds addtional column to indicate if the finsource code has been
    entered for current or another candidate"""

    n_col_name = f"Entered for {col_name}?"
    records_verified = records_matched.copy()

    for row_i in records_verified.values():

        entered = []
        other_entries = []

        for row_j in records.group_by(
            records_finsource, {"code": str(row_i[col_name])}
        ).values():

            if str(row_i["candidate_id"]) == str(row_j["candidate_id"]):
                entered.append(str(row_j["candidate_id"]))

            else:
                if not str(row_i["candidate_id"]):
                    continue
                else:
                    other_entries.append(str(row_j["candidate_id"]))

        if entered and not other_entries:
            row_i[n_col_name] = "YES"

        elif not entered and other_entries:
            row_i[n_col_name] = f"Entered for {', '.join(other_entries)}"

        elif entered and other_entries:
            row_i[n_col_name] = f"Entered for {', '.join(entered + other_entries)}"

        else:
            row_i[n_col_name] = "NO"

    return records_verified


def main(records_transformed: dict, *election_years) -> tuple[dict, dict]:

    vs_db_connection = connect_to_database()

    ## Match Candidates
    query_election_candidates = load_query_string("election_candidates.sql")

    states = {row["state_id"] for row in records_transformed.values()}

    formatted_query_ec = (
        query_election_candidates
        + f"""
        WHERE election.electionyear IN ({",".join(election_years)})
        AND office.office_id IN (1,5,6)
        AND election_candidate.state_id IN ({",".join([f"'{state}'" for state in set(states)])})
        """
    )

    records_ec = query_from_database(formatted_query_ec, vs_db_connection)
    records_matched, match_info = match(records_transformed, records_ec)

    ## Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)

    ## Verify Candidates
    query_finsource_candidates = load_query_string("finsource_candidates.sql")

    crp_ids = [f"'{row['CID']}'" for row in records_matched.values()]
    fec_ids = [f"'{row['FECCandID']}'" for row in records_matched.values()]

    formatted_query_crp = (
        query_finsource_candidates
        + f"""
        WHERE finsource_id = 1
        AND code IN ({",".join(crp_ids)})
        """
    )

    formatted_query_fec = (
        query_finsource_candidates
        + f"""
        WHERE finsource_id = 2
        AND code IN ({",".join(fec_ids)})
        """
    )

    records_crp = query_from_database(formatted_query_crp, vs_db_connection)
    records_fec = query_from_database(formatted_query_fec, vs_db_connection)

    records_verified_crp = verify(records_matched, records_crp, "CID")
    records_verified_fec = verify(records_verified_crp, records_fec, "FECCandID")

    return records_verified_fec, records_ec


if __name__ == "__main__":

    import sys

    _, EXPORT_DIR, TRANSFORMED_FILE, *YEARS = sys.argv

    if not YEARS:
        print(
            "Please enter at least one election year after" "transformed file parameter"
        )
        exit()

    EXPORT_DIR = Path(EXPORT_DIR)
    TRANSFORMED_FILE = Path(TRANSFORMED_FILE)

    df_transformed = pandas.read_csv(TRANSFORMED_FILE)

    records_transformed = df_transformed.to_dict(orient="index")
    records_verified, records_ec = main(records_transformed, *YEARS)

    save_verified(records_verified, records_ec)
