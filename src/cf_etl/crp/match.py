from pathlib import Path
from collections import defaultdict

# External Libraries and Packages
import psycopg

from psycopg import ClientCursor
from rapidfuzz import fuzz
from tqdm import tqdm
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
        {"WRatio": lambda x, y: fuzz.WRatio(str(x).lower(), str(y).lower())}
    )
    rc_config.scorers_by_column.default = "WRatio"
    rc_config.thresholds_by_column.default = 85

    rc_config.populate()

    rc_config.columns_to_match["firstname"] = "nickname", "middlename"

    rc_config.columns_to_group["state_id"] = "state_id"
    rc_config.columns_to_get["candidate_id"] = "candidate_id"

    rc_config.thresholds_by_column["lastname"] = 88
    rc_config.thresholds_by_column["suffix"] = 90
    rc_config.thresholds_by_column["state_id"] = 100
    rc_config.thresholds_by_column["district"] = 98
    rc_config.thresholds_by_column["party"] = 95
    rc_config.thresholds_by_column["office"] = 100

    rc_matcher.required_threshold = 85
    rc_matcher.duplicate_threshold = 3

    p_bar = tqdm(total=len(records_transformed), desc="Matching...")
    matched_records, match_info = rc_matcher.match(update_func=lambda: p_bar.update(1))

    # Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(len(max_key_length)+4)}:", v)

    return matched_records


def verify(
    records_matched: dict[int, dict[str, str]],
    records_finsource: dict[int, dict[str, str]],
    col_name: str,
):
    """Adds addtional column to indicate if the finsource code has been
    entered for the current candidate or if it has been entered for another"""

    n_col_name = f"Entered for {col_name}?"
    records_verified = records_matched.copy()

    code_to_candidates = defaultdict(list)

    for row in records_finsource.values():
        code = str(row["code"]).strip()
        candidate_id = str(row["candidate_id"]).strip()
        code_to_candidates[code].append(candidate_id)

    for row_i in records_verified.values():

        code = str(row_i[col_name]).strip()
        candidate_id = str(row_i["candidate_id"]).strip()

        if code in code_to_candidates.keys():
            candidate_ids = code_to_candidates[code]

            entered = [cid for cid in candidate_ids if cid == candidate_id]
            other_entries = [cid for cid in candidate_ids if cid != candidate_id]

            if entered and not other_entries:
                row_i[n_col_name] = "YES"

            else:
                row_i[n_col_name] = f"Entered for {', '.join(entered + other_entries)}"

        else:
            row_i[n_col_name] = "NO"

    return records_verified


def query_as_records(query: str, connection, **params) -> dict[str, str]:
    """Converts query results into records"""
    cursor = connection.cursor()
    # print(cursor.mogrify(query, params))
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


def load_query_string(query_filename: Path) -> str:
    """Reads from a .sql file to be executed"""
    package_dir = Path(__file__).parent.parent
    with open(package_dir / "queries" / f"{query_filename}.sql", "r") as f:
        query_string = f.read()

    return query_string


def main(
    records_transformed: dict[int, dict[str, str]],
    db_connection_info: dict,
    election_years: list,
) -> tuple[dict, dict]:

    assert election_years != []  # At least one election year is provided

    print("Connecting to database...")
    vsdb_conn = psycopg.connect(**db_connection_info, cursor_factory=ClientCursor)
    print("Connected.")

    ## Match Candidates
    query_election_candidates = load_query_string("election_candidates")
    query_finsource_candidates = load_query_string("finsource_candidates")

    states = {str(row["state_id"]) for row in records_transformed.values()}

    records_election_candidates = query_as_records(
        query_election_candidates,
        vsdb_conn,
        election_years=election_years,
        stages=["G", "P"],
        office_ids=["1", "5", "6"],
        state_ids=list(states),
    )

    records_matched = match(records_transformed, records_election_candidates)

    # Verify Candidates
    query_finsource_candidates = load_query_string("finsource_candidates")

    print("Querying election_candidates...")
    records_finsource_crp = query_as_records(
        query_finsource_candidates,
        vsdb_conn,
        finsource_ids=["1"],
        finsource_codes=[
            f'%{row["CID"].strip()}%' for row in records_matched.values() if row["CID"]
        ],
    )
    print("Done.")

    print("Querying finsource_candidates...")
    records_finsource_fec = query_as_records(
        query_finsource_candidates,
        vsdb_conn,
        finsource_ids=["2"],
        finsource_codes=[
            f'%{row["FECCandID"].strip()}%'
            for row in records_matched.values()
            if row["FECCandID"]
        ],
    )
    print("Done.")

    records_verified_crp = verify(records_matched, records_finsource_crp, "CID")
    records_verified_fec = verify(
        records_verified_crp, records_finsource_fec, "FECCandID"
    )

    return records_verified_fec, records_election_candidates
