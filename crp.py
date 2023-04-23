## built-ins
import os
import sys
import re

from datetime import datetime

## external libraries and packages
import pandas

from rapidfuzz import fuzz
from vs_library import database
from vs_library.vsdb import queries
from tabular_matcher.matcher import TabularMatcher
from tabular_matcher.config import MatcherConfig


def model(df):

    """
    Changes the initial raw format into a format comparable to Vote Smart's

    Parameter
    ---------
    df: pandas.DataFrame
        Extracted and/or cleaned data from CRP 

    Returns
    -------
    pandas.DataFrame
    """

    party_reference = {'D': 'Democratic',
                       'I': 'Independent',
                       'L': 'Libertarian',
                       'R': 'Republican',
                        3: 'Other'}

    office_reference = {'S0': 'U.S. Senate',
                        'S1': 'U.S. Senate',
                        'S2': 'U.S. Senate',
                        'ES': 'President'}
    
    middlename = r'\s+\b(?P<middlename>[A-Z]{1})\b'
    nickname = r'[\"\'\(](?P<nickname>.*?)[\"\'\)]'
    suffix = r'(?P<suffix>[IVX][IVX]+$|[DJMS][rs][s]?[\.]?)'
    firstname = lambda x: re.sub(f'{middlename}|{nickname}|{suffix}','', x).strip() if isinstance(x, str) else x
    state_id = r'(?P<state_id>^..)'
    district = r'(?P<district>..$)'
    party = lambda x: party_reference[x] if x in party_reference.keys() else x
    office = lambda x: office_reference[x] if x in office_reference.keys() else re.sub('\d+', 'U.S. House', x)

    name_split_df = df['CRPName'].str.split(pat=",", expand=True).apply(lambda x: x.apply(lambda y: y.strip() if y else y))
    name_extract_df = name_split_df[1].str.extract(f"{middlename}|{nickname}|{suffix}")
    state_extract = df['DistIDRunFor'].str.extract(state_id)['state_id']
    dist_extract = df['DistIDRunFor'].str.extract(district)['district']
    party_transform = df['Party'].apply(party)
    office_transform = dist_extract.apply(office)

    presidential_index = office_transform.loc[office_transform=='President'].index
    state_extract.iloc[presidential_index] = 'NA'

    transformed_df = pandas.concat([name_split_df[0].rename('lastname'), 
                                    name_split_df[1].apply(firstname).rename('firstname'), 
                                    name_extract_df,
                                    state_extract,
                                    dist_extract.apply(lambda x: re.sub("^0+|(ES)|[S]\d+", "", x)),
                                    party_transform.rename('party'),
                                    office_transform.rename('office'),
                                    df['CID'],
                                    df['FECCandID']], axis=1)

    return transformed_df


def match(crp_df: pandas.DataFrame, election_candidates_df: pandas.DataFrame):

    """
    Configures the matching program and matches crp data with Vote Smart's to get the candidate_id

    Parameters
    ----------
    crp_df: pandas.DataFrame
        The modeled CRP data

    election_candidates_df: pandas.DataFrame
        Query Results from Vote Smart's database that show all relevant candidates

    
    Returns
    -------
    (pandas.DataFrame, dict)
    """

    records_crp = crp_df.to_dict('index')
    records_ec = election_candidates_df.to_dict('index')

    tb_config = MatcherConfig(records_crp, records_ec)
    tb_matcher = TabularMatcher(records_crp, records_ec, tb_config)

    tb_config.scorers_by_column.SCORERS.update({'WRatio': lambda x,y: fuzz.WRatio(x,y)})
    tb_config.scorers_by_column.default = 'WRatio'
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match.pop('CID')
    tb_config.columns_to_match.pop('FECCandID')
    tb_config.columns_to_match['firstname'] = 'nickname', 'middlename'

    tb_config.columns_to_group['state_id'] = 'state_id'
    tb_config.columns_to_get.add('candidate_id')
    
    tb_config.thresholds_by_column['lastname'] = 88
    tb_config.thresholds_by_column['suffix'] = 90
    tb_config.thresholds_by_column['state_id'] = 100
    tb_config.thresholds_by_column['district'] = 98
    tb_config.thresholds_by_column['party'] = 95
    tb_config.thresholds_by_column['office'] = 100

    tb_config.required_threshold = 85
    tb_config.duplicate_threshold = 3

    return tb_matcher.match()


def verify(matched_df, query_tool, col_name):

    """
    Adds addtional column to indicate if the finsource code has been entered for current or another candidate

    Parameters
    ----------
    matched_df: pandas.DataFrame
        The matched data containing both datapoints from Vote Smart and CRP

    query_tool: vs_library.database.QueryTool

    Returns
    -------
    pandas.DataFrame
    """

    query_tool.run()
    query_df = query_tool.results(as_format='pandas_df')

    for i, row_i in matched_df.iterrows():
        entered = []
        other_entries = []

        for _, row_j in query_df[query_df['code']==str(row_i[col_name])].iterrows():

            if str(row_i['candidate_id']) == str(row_j['candidate_id']):
                entered.append(str(row_j['candidate_id']))
            else:
                other_entries.append(str(row_j['candidate_id']))

        if entered and not other_entries:
            matched_df.at[int(i), f'{col_name} ENTERED?'] = 'YES'

        elif not entered and other_entries:
            matched_df.at[int(i), f'{col_name} ENTERED?'] = f"Entered for {', '.join(other_entries)}"
        
        elif entered and other_entries:
            matched_df.at[int(i), f'{col_name} ENTERED?'] = f"Entered for {', '.join(entered + other_entries)}"
        
        else:
            matched_df.at[int(i), f'{col_name} ENTERED?'] = 'NO'


def main():

    # df = pandas.read_excel(CRP_FILE, skiprows=13, usecols="B:F", na_values="")
    df = pandas.read_excel(CRP_FILE, header=None)

    _m, _d, _y = df.iloc[0,0].lstrip('updated ').split('/')
    last_updated = "-".join(map(lambda x: '0' + x if len(x) < 2 else x, [_y, _m, _d]))

    cleaned_df = df.iloc[STARTING_ROW+1:, STARTING_COLUMN:].reset_index(drop=True)
    cleaned_df = cleaned_df.set_axis(list(df.iloc[STARTING_ROW, STARTING_COLUMN:]), axis='columns')

    ## Modeled DataFrame
    modeled_df = model(cleaned_df)
    modeled_df.to_csv(f"{FILEPATH}/{last_updated}_CRP_Modeled.csv", index=False)


    states = list(modeled_df['state_id'].value_counts().keys())

    connection_manager = database.ConnectionManager(os.path.dirname(__file__))
    connection_info, _ = connection_manager.read(1)
    
    connection_adapter = database.PostgreSQL(connection_info)
    connection_adapter.connect()

    election_candidates_query = queries.ElectionCandidates.statement
    election_candidates_conditions = \
        f"""
         WHERE election.electionyear IN ({YEAR})
         AND office.office_id IN (1,5,6)
         AND election_candidate.state_id IN ({",".join([f"'{state}'" for state in states])})
        """

    query_tool = database.QueryTool(connection_adapter)
    query_tool.query = (election_candidates_query + election_candidates_conditions,)
    query_tool.run()

    ## Query DataFrame
    election_candidates_df = query_tool.results(as_format='pandas_df')
    election_candidates_df.to_csv(f"{FILEPATH}/{TIMESTAMP}_Query.csv", index=False)

    matched_df, match_info = match(modeled_df, election_candidates_df)

    entered_crp_query = \
        '''
        SELECT code, candidate_id
        FROM finsource_candidate
        WHERE finsource_id = 1
        AND code IN ({0})
        '''.format(",".join([f"\'{cid}\'" for cid in matched_df['CID']]))

    query_tool.query = (entered_crp_query,)

    verify(matched_df, query_tool, 'CID')

    entered_fec_query = \
        '''
        SELECT code, candidate_id
        FROM finsource_candidate
        WHERE finsource_id = 2
        AND code IN ({0})
        '''.format(",".join([f"\'{fecid}\'" for fecid in matched_df['FECCandID']]))

    query_tool.query = (entered_fec_query,)

    verify(matched_df, query_tool, 'FECCandID')
    
    ## Verified and Matched DataFrame
    matched_df.to_csv(f"{FILEPATH}/{last_updated}_CRP_Matched.csv", index=False)

    ## Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(max_key_length+4)}:", v)



if __name__  == "__main__":
    
    _, YEAR, CRP_FILE = sys.argv

    FILEPATH = os.path.dirname(CRP_FILE)
    TIMESTAMP = datetime.strftime(datetime.now(), '%Y-%m-%d')
    STARTING_ROW = 13
    STARTING_COLUMN = 1
    
    main()
