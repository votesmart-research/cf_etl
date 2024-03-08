from pathlib import Path

# External packages and libraries
import psycopg
from rapidfuzz import fuzz
from tqdm import tqdm

from record_matcher import records
from record_matcher.matcher import RecordMatcher


def match(
    records_transformed: dict[int, dict[str, str]],
    records_ec: dict[int, dict[str, str]],
):
    """Configures the matching program and matches nimsp candidates with Vote
    Smart's candidates to get the candidate_id"""

    rc_matcher = RecordMatcher()
    rc_config = rc_matcher.config

    rc_matcher.x_records = records_transformed
    rc_matcher.y_records = records_ec

    rc_config.scorers_by_column.SCORERS.update(
        {"WRatio": lambda x, y: fuzz.WRatio(str(x).lower(), str(y.lower()))}
    )
    rc_config.scorers_by_column.default = "WRatio"
    rc_config.thresholds_by_column.default = 85

    rc_config.populate()

    rc_config.columns_to_match["firstname"] = "nickname", "middlename"

    rc_config.columns_to_group["state_id"] = "state_id"
    rc_config.columns_to_get["candidate_id"] = "candidate_id"

    rc_config.thresholds_by_column["lastname"] = 88
    rc_config.thresholds_by_column["suffix"] = 95
    rc_config.thresholds_by_column["state_id"] = 100
    rc_config.thresholds_by_column["district"] = 98
    rc_config.thresholds_by_column["party"] = 90
    rc_config.thresholds_by_column["office"] = 90

    rc_matcher.required_threshold = 85
    rc_matcher.duplicate_threshold = 3

    p_bar = tqdm(total=len(records_transformed), desc="Matching...")
    records_matched, match_info = rc_matcher.match(update_func=lambda: p_bar.update(1))

    # Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)

    return records_matched


def verify(records_matched: dict, records_finsource: dict, col_name):
    """Adds addtional column to indicate if the finsource code has been
    entered for the current candidate or if it has been entered for another"""

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


def query_as_records(query: str, connection, **params):
    """Converts query results into records"""
    cursor = connection.cursor()
    cursor.execute(query, params)
    headers = [str(k[0]) for k in cursor.description]
    return {
        index: dict(zip(headers, row)) for index, row in enumerate(cursor.fetchall())
    }


def query_as_reference(query: str, connection, **params) -> dict[str, int]:
    """A two column query result that can be turn into a reference"""
    cursor = connection.cursor()
    cursor.execute(query, params)
    return {name: ids for ids, name in cursor.fetchall()}


def load_query_string(query_filename):
    """Reads from a .sql file to be executed"""
    package_dir = Path(__file__).parent.parent
    with open(package_dir / "queries" / f"{query_filename}.sql", "r") as f:
        query_string = f.read()

    return query_string


def main(records_transformed: dict, db_connection_info: dict):
    vsdb_conn = psycopg.connect(**db_connection_info)

    query_election_candidates = load_query_string("election_candidates")

    # Remove federal candidates
    query_election_candidates += (
        "AND office.code NOT SIMILAR TO 'US%%|P|Vice President' "
    )

    query_finsource_candidates = load_query_string("finsource_candidates")
    query_offices = load_query_string("office_list")

    # Match Candidates
    election_years = {str(row["election_year"]) for row in records_transformed.values()}
    states = {str(row["state_id"]) for row in records_transformed.values()}

    print("Querying election_candidates...")

    records_election_candidates = query_as_records(
        query_election_candidates,
        vsdb_conn,
        election_years=list(election_years),
        stages=["G", "P"],
        office_ids=list(query_as_reference(query_offices, vsdb_conn).values()),
        state_ids=list(states),
    )

    records_matched = match(records_transformed, records_election_candidates)

    print("Querying finsource_candidates...")

    # Verify Candidates
    records_finsource_candidates = query_as_records(
        query_finsource_candidates,
        vsdb_conn,
        finsource_ids=["4"],
        finsource_codes=[str(row["NIMSP_ID"]) for row in records_matched.values()],
    )

    records_verified = verify(records_matched, records_finsource_candidates, "NIMSP_ID")

    return records_verified, records_election_candidates
