# Built-in packages
import json
from pathlib import Path

# External packages and libraries
import pg8000
from rapidfuzz import fuzz
from tqdm import tqdm
from tabular_matcher import records
from tabular_matcher.matcher import TabularMatcher, MatcherConfig


def match(
    records_transformed: dict[int, dict[str, str]],
    records_ec: dict[int, dict[str, str]],
):
    """Configures the matching program and matches nimsp data with Vote
    Smart's to get the candidate_id"""

    tb_config = MatcherConfig()
    tb_matcher = TabularMatcher(tb_config)

    tb_matcher.x_records = records_transformed
    tb_matcher.y_records = records_ec

    tb_config.scorers_by_column.SCORERS.update(
        {"WRatio": lambda x, y: fuzz.WRatio(str(x).lower(), str(y.lower()))}
    )
    tb_config.scorers_by_column.default = "WRatio"
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match["firstname"] = "nickname", "middlename"

    tb_config.columns_to_group["state_id"] = "state_id"
    tb_config.columns_to_get["candidate_id"] = "candidate_id"

    tb_config.thresholds_by_column["lastname"] = 88
    tb_config.thresholds_by_column["suffix"] = 95
    tb_config.thresholds_by_column["state_id"] = 100
    tb_config.thresholds_by_column["district"] = 98
    tb_config.thresholds_by_column["party"] = 90
    tb_config.thresholds_by_column["office"] = 90

    tb_matcher.required_threshold = 85
    tb_matcher.duplicate_threshold = 3

    p_bar = tqdm(total=len(records_transformed), desc="Matching...")

    records_matched, match_info = tb_matcher.match(update_func=lambda: p_bar.update(1))

    return records_matched, match_info


def verify(records_matched: dict, records_finsource: dict, col_name):
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


def load_query_string(query_filename):
    PACKAGE_DIR = Path(__file__).parent.parent
    with open(PACKAGE_DIR / "queries" / query_filename, "r") as f:
        query_string = f.read()

    return query_string


def save_verified(records_verified: dict, records_queried: dict):
    df_verified = pandas.DataFrame.from_dict(records_verified, orient="index")
    df_queried = pandas.DataFrame.from_dict(records_queried, orient="index")

    VERIFIED_FILES = EXPORT_DIR / "VERIFIED_FILES"
    VERIFIED_FILES.mkdir(exist_ok=True)

    df_verified.to_csv(VERIFIED_FILES / f"NIMSP_Matched.csv", index=False)
    df_queried.to_csv(VERIFIED_FILES / f"NIMSP_Queried.csv", index=False)


def main(records_transformed: dict) -> tuple[dict, dict]:
    vs_db_connection = connect_to_database()

    query_election_candidates = load_query_string("election_candidates.sql")
    election_years = {str(row["election_year"]) for row in records_transformed.values()}

    formatted_query_ec = (
        query_election_candidates
        + f"""
        WHERE election.electionyear IN ({",".join(election_years)})
        AND office.code NOT LIKE 'US%'
        """
    )

    records_ec = query_from_database(formatted_query_ec, vs_db_connection)
    records_matched, match_info = match(records_transformed, records_ec)

    # Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)

    query_finsource_candidates = load_query_string("finsource_candidates.sql")
    nimsp_ids = [f"'{row['NIMSP_ID']}'" for row in records_matched.values()]

    formatted_query_nimsp = (
        query_finsource_candidates
        + f"""
        WHERE finsource_id = 4
        AND code IN ({",".join(nimsp_ids)})
        """
    )

    records_nimsp = query_from_database(formatted_query_nimsp, vs_db_connection)
    records_verified = verify(records_matched, records_nimsp, "NIMSP_ID")

    return records_verified, records_ec


if __name__ == "__main__":
    import sys
    import pandas

    _, EXPORT_DIR, TRANSFORMED_FILE = sys.argv

    EXPORT_DIR = Path(EXPORT_DIR)
    TRANSFORMED_FILE = Path(TRANSFORMED_FILE)

    df_transformed = pandas.read_csv(TRANSFORMED_FILE, na_values='', keep_default_na=False)
    
    records_transformed = df_transformed.to_dict(orient="index")
    records_verified, records_ec = main(records_transformed)

    save_verified(records_verified, records_ec)
