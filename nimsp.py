## built-ins
import os
import re
import json

## external library and packages
import requests
import pandas

from tqdm import tqdm
from rapidfuzz import fuzz
from vs_library import database
from vs_library.vsdb import queries
from tabular_matcher.matcher import TabularMatcher
from tabular_matcher.config import MatcherConfig


class NIMSPJson:

    """
    Extracts the value and records of JSON data from followthemoney.org API

    Properties
    ----------
    current_page: int
        Gets the current page of the JSON
    
    min_page: int
        Gets the starting page

    max_page: int
        Last page where it contains records

    total_pages: int
        Total number of pages

    last_updated: str
        Returns a date string format ('YYYY-MM-DD-HH-MM-SS')

    year: str
        Returns the year of the records
    
    prev_page: int
        Returns the previous page number

    next_page: int
        Returns the next page number
    """

    def __init__(self, json) -> None:

        """
        Parameters
        ----------
        json: dict
            A converted json dictionary from the API
        """

        self.__json = json
        
    @property
    def current_page(self):
        return self.__json['metaInfo']['paging']['currentPage'] 
    
    @property
    def min_page(self):
        return self.__json['metaInfo']['paging']['minPage']

    @property
    def max_page(self):
        return self.__json['metaInfo']['paging']['maxPage']
    
    @property
    def total_pages(self):
        return self.__json['metaInfo']['paging']['totalPages']

    @property
    def last_updated(self):
        u = self.__json['metaInfo']['completeness']['lastUpdated']

        date_str, time_str= u.split()

        return f"{date_str}-{''.join(time_str.split(':'))}"

    @property
    def year(self):
        requested_format = self.__json['metaInfo']['recordFormat']['request']

        # format of the parameters are p_1=v_1&p_2=v_2...
        params_list = requested_format.split('&')
        params_dict = {p.split('=')[0]: p.split('=')[1] for p in params_list}

        return params_dict['y']

    @property
    def prev_page(self):
        return self.current_page - 1 if self.current_page > self.min_page else self.min_page
    
    @property
    def next_page(self):
        # will return one higher than the allowed maximum for iteration purpose
        return self.current_page + 1 if self.current_page < self.max_page else self.total_pages
        
    def update(self, json):

        """
        Updates the current json with another json dictionary
        """

        self.__json = json

    def extract(self, to_remove=['request']):

        """
        Extracts necessary data from json dictionary and convert it into a list of 1-D dictionaries

        Returns
        -------
        list of 1-D dictionaries

        """
        records = []

        for record in self.__json['records']:
            new_record = {'NIMSP_ID': record['Candidate_Entity']['id']}
            new_record.update({k: v[k] if isinstance(v, dict) else v for k,v in record.items()})

            for item in to_remove:
                new_record.pop(item)

            records.append(new_record)

        return records

    def read_from(self, filepath):

        """
        Reads from a json file
        """
        
        with open(filepath, 'r') as f:
            self.__json = json.load(f)

    def export_to(self, filepath):

        """
        Exports json dictionary into a json file
        """
        
        filename = f'{self.last_updated}_NIMSP_page-{self.current_page}.json'
        jstr = json.dumps(self.__json, indent=4)

        with open(f"{filepath}/{filename}", 'w') as f:
            f.write(jstr)

    def __len__(self):
        return self.__json['metaInfo']['paging']['recordsThisPage']


class NIMSPApi:

    """
    An object model to interact with followthemoney.org API

    Properties
    ----------
    url: str
        The main url for the API

    full_url: str
        The main url combined with its parameters


    Token Reference
    ---------------
    Format: mode ; eg. xml, json
    Grouping: gro
    Sorting: so
    Sorting Direction: sod ; eg. 0(desc), 1(asc)
    Paging: p
    Election_State: s
    Election_Year: y
    Office_Sought: c-r-osid
    Office: c-r-oc
    Candidate: c-t-id
    Political_Party: c-t-p ; eg. 1(Democratic), 2(Republican), 3(Third-Party), 4(NonPartisan)
    Candidate_Entity: c-t-eid (NIMSP ID)
    Type_of_Office: c-r-ot ; eg. G(Gubernatorial), U(US House), L(US Senate)
    Incumbency_Status: c-t-ico ; eg. I(Incumbent), O(Open)
    """

    def __init__(self, api_key, year) -> None:

        """
        Parameters
        ----------
        api_key: str
            Unique API key by followthemoney.org

        year: int or str
            The year in which data is needed
        """


        self.url = "https://api.followthemoney.org"
        self.__params = {'APIKey': api_key,
                        'mode': 'json',
                        'gro': 'c-t-id',
                        'y': year,
                        'so': 's,c-r-oc',
                        'sod': 1,
                        'p': '',
                        }

    @property
    def full_url(self):
        combined_params = "&".join([f"{k}={v}" for k, v in self.__params.items()])
        return f"{self.url}/?{combined_params}"

    def update_params(self, params: dict):

        """
        Allow changes to the parameter value only if the parameter key existed
        """

        if set(params.keys()).issubset(self.__params.keys()):
            self.__params.update(params)

    def change_page(self, page_num):

        """
        Allow a more direct change to the page parameter
        """
        self.update_params({'p': page_num})

    def page_source(self, as_type='json'):

        """
        Send a request to the full url and returns the page source
        """
        r = requests.get(self.full_url)

        if as_type == 'str':
            return r.text
        elif as_type == 'json':
            return r.json()


def extract(nimsp_api, nimsp_json, json_files=[], extract_path='~/NIMSP_JSON'):

    """
    Performs the extraction process by reading files or pulling data from API

    Parameters
    ----------
    nimsp_api: nimsp.NIMSPApi
        
    nimsp_json: nimsp.NIMSPJson

    json_files: list
        Contains a list of folder paths to the json file

    extract_path: filepath
        A filepath to save the extract files

    Returns
    -------
    (list of 1-D dictionaries, date)
    """

    api_last_update = nimsp_json.last_updated

    pbar = tqdm(total=nimsp_json.max_page + 1)
    extracted = []

    for json_file in json_files:

        nimsp_json.read_from(json_file)

        # Assuming that the files are up-to-date with the API,
        # breaks the loop if the number of files are incomplete and it is the last json file
        # The next while loop will store the extracted records instead
        if nimsp_json.last_updated == api_last_update and \
           len(json_files) < nimsp_json.total_pages and \
           nimsp_json.current_page == len(json_files) - 1:
            break

        extracted += nimsp_json.extract(to_remove=['request', 'Candidate', 'record_id'])
        pbar.update(1)

    if nimsp_json.last_updated != api_last_update:
        return extracted, nimsp_json.last_updated

    while nimsp_json.current_page <= nimsp_json.max_page:

        nimsp_json.export_to(extract_path)
        extracted += nimsp_json.extract(to_remove=['request', 'Candidate', 'record_id'])
        pbar.update(1)

        nimsp_api.change_page(nimsp_json.next_page)
        nimsp_json.update(nimsp_api.page_source())

    return extracted, nimsp_json.last_updated


def model(df: pandas.DataFrame):

    """
    Changes the initial raw format into a format comparable to Vote Smart's

    Parameters
    ----------
    df: pandas.DataFrame
        Extracted and/or cleaned data from NIMSP


    Returns
    -------
    pandas.DataFrame
    """

    suffix = r'\b(?P<suffix>[IVX][IVX]+$|[DJMS][RS][S]?[\.]?$)'
    lastname = lambda x: re.sub(f"{suffix}|\(.*\)", "", x) if x else ""
    middlename = r'\b(?P<middlename>[A-Z]{1}$)\b'
    nickname = r'[\"\'\(](?P<nickname>.*?)[\"\'\)]'
    firstname = lambda x: re.sub(f"{middlename}|{nickname}", "", x) if x else ""
    office = r'(?P<office>.*(?= DISTRICT)|.*(?!= DISTRICT))'
    district = r'(?P<district>(?<=DISTRICT ).+)'
    
    name_split_df = df['Candidate_Entity'].str.split(pat=', ', expand=True)
    lastname_extract = name_split_df[0].apply(lastname).rename('lastname')
    suffix_extract = name_split_df[0].str.extract(suffix)['suffix']
    firstname_extract = name_split_df[1].apply(firstname).rename('firstname')
    middlename_extract = name_split_df[1].str.extract(middlename)['middlename']
    nickname_extract = name_split_df[1].str.extract(nickname)['nickname']
    state_extract = df['Election_Jurisdiction'].rename('state_id')
    party_extract = df['Specific_Party'].rename('party')

    office_split_df = df['Office_Sought'].str.split(pat='-', expand=True)
    office_extract = office_split_df[0].str.extract(office)['office']
    district_extract = office_split_df[0].str.extract(district)['district']

    transformed_df = pandas.concat([
        lastname_extract.apply(lambda x: x.title()),
        firstname_extract.apply(lambda x: x.title()),
        middlename_extract.apply(lambda x: x.title() if isinstance(x, str) else x),
        nickname_extract.apply(lambda x: x.title() if isinstance(x, str) else x),
        suffix_extract.apply(lambda x: x.title() if isinstance(x, str) else x),
        state_extract,
        party_extract.apply(lambda x: x.title() if isinstance(x, str) else x),
        office_extract.apply(lambda x: x.title() if isinstance(x, str) else x),
        district_extract.apply(lambda x: re.sub(r'^0+',"", x.title()) if isinstance(x,str) else x),
        df['NIMSP_ID'],
    ], axis=1)

    return transformed_df


def match(nimsp_df: pandas.DataFrame, election_candidates_df: pandas.DataFrame):

    """
    Configures the matching program and matches nimsp data with Vote Smart's to get the candidate_id

    Parameters
    ----------
    nimsp_df: pandas.DataFrame
        The modeled NIMSP data

    election_candidates_df: pandas.DataFrame
        Query Results from Vote Smart's database that show all relevant candidates

    
    Returns
    -------
    (pandas.DataFrame, dict)
    """

    records_nimsp = nimsp_df.to_dict('index')
    records_ec = election_candidates_df.to_dict('index')

    tb_config = MatcherConfig(records_nimsp, records_ec)
    tb_matcher = TabularMatcher(records_nimsp, records_ec, tb_config)

    tb_config.scorers_by_column.SCORERS.update({'WRatio': lambda x,y: fuzz.WRatio(x,y)})
    tb_config.scorers_by_column.default = 'WRatio'
    tb_config.thresholds_by_column.default = 85

    tb_config.populate()

    tb_config.columns_to_match.pop('NIMSP_ID')
    tb_config.columns_to_match['firstname'] = 'nickname', 'middlename'

    tb_config.columns_to_group['state_id'] = 'state_id'
    tb_config.columns_to_get.add('candidate_id')

    tb_config.thresholds_by_column['lastname'] = 88
    tb_config.thresholds_by_column['suffix'] = 95
    tb_config.thresholds_by_column['state_id'] = 100
    tb_config.thresholds_by_column['district'] = 98
    tb_config.thresholds_by_column['party'] = 90
    tb_config.thresholds_by_column['office'] = 90
    
    tb_config.required_threshold = 85
    tb_config.duplicate_threshold = 3

    return tb_matcher.match()


def verify(matched_df, query_tool):

    """
    Adds addtional column to indicate if the nimsp_id has been entered for current or another candidate

    Parameters
    ----------
    matched_df: pandas.DataFrame
        The matched data containing both datapoints from Vote Smart and NIMSP

    query_tool: vs_library.database.QueryTool

    Returns
    -------
    pandas.DataFrame
    """

    verified_df = matched_df.copy()
    col_name = 'NIMSP_ID'
    
    query = \
        '''
        SELECT code, candidate_id
        FROM finsource_candidate
        WHERE finsource_id = 4
        AND code IN ({0})
        '''.format(",".join([f"\'{nimsp_id}\'" for nimsp_id in verified_df[col_name]]))

    query_tool.query = (query,)
    query_tool.run()

    query_df = query_tool.results(as_format='pandas_df')

    for i, row_i in verified_df.iterrows():
        entered = []
        other_entries = []

        for _, row_j in query_df[query_df['code']==str(row_i[col_name])].iterrows():

            if str(row_i['candidate_id']) == str(row_j['candidate_id']):
                entered.append(str(row_j['candidate_id']))
            else:
                other_entries.append(str(row_j['candidate_id']))

        if entered and not other_entries:
            verified_df.at[int(i), f'{col_name} ENTERED?'] = 'YES'

        elif not entered and other_entries:
            verified_df.at[int(i), f'{col_name} ENTERED?'] = f"Entered for {', '.join(other_entries)}"
        
        elif entered and other_entries:
            verified_df.at[int(i), f'{col_name} ENTERED?'] = f"Entered for {', '.join(entered + other_entries)}"
        
        else:
            verified_df.at[int(i), f'{col_name} ENTERED?'] = 'NO'

    return verified_df


def main():

    nimsp_api = NIMSPApi(API_KEY, YEAR)
    nimsp_json = NIMSPJson(nimsp_api.page_source())

    extracted_records, last_updated = extract(nimsp_api, nimsp_json, JSON_FILES, EXTRACT_FOLDER)

    ## Extracted DataFrame
    extracted_df = pandas.DataFrame.from_records(extracted_records)
    extracted_df.to_csv(f"{FILEPATH}/{last_updated}_NIMSP_Extract.csv", index=False)

    ## Modeled DataFrame
    modeled_df = model(extracted_df)
    modeled_df.to_csv(f"{FILEPATH}/{last_updated}_NIMSP_Modeled.csv", index=False)
    
    connection_manager = database.ConnectionManager(os.path.dirname(__file__))
    connection_info, _ = connection_manager.read(1)
    connection_adapter = database.PostgreSQL(connection_info)
    query_tool = database.QueryTool(connection_adapter)
    connection_adapter.connect()

    election_candidates_query = queries.ElectionCandidates.statement
    election_candidates_conditions = \
        f"""
         WHERE election.electionyear IN ({YEAR})
         AND office.code NOT LIKE 'US%'
        """
        
    query_tool.query = (election_candidates_query + election_candidates_conditions,)
    query_tool.run()

    ## Query DataFrame
    election_candidates_df = query_tool.results(as_format='pandas_df')
    election_candidates_df.to_csv(f"{FILEPATH}/{last_updated}_Query.csv", index=False)

    matched_df, match_info = match(modeled_df, election_candidates_df)

    ## Verified DataFrame
    verified_df = verify(matched_df, query_tool)
    verified_df.to_csv(f"{FILEPATH}/{last_updated}_NIMSP_Matched.csv", index=False)

    ## Prints match results
    max_key_length = max(match_info, key=lambda x: len(x)) if match_info else 0
    for k, v in match_info.items():
        print(f"{k.rjust(max_key_length+4)}:", v)


if __name__ == '__main__':

    import sys

    try:
        _, YEAR, FILEPATH, *JSON_FILES = sys.argv

    except ValueError:
        print('Script, year, FILEPATH, *json_files')
        exit()

    try:
        with open('API_KEY', 'r') as f:
            API_KEY = f.read()
            
    except FileNotFoundError:
        print('API_KEY file not found. Try again after you have include the key.')
        exit()

    EXTRACT_FOLDER = f"{FILEPATH}/NIMSP_Extract"

    if not os.path.isdir(EXTRACT_FOLDER):
        os.makedirs(EXTRACT_FOLDER)

    main()