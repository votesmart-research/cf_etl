import json
import requests
from datetime import datetime


split_params = lambda link: {p.split("=")[0]: p.split("=")[1] for p in link.split("&")}
combine_params = lambda built: "&".join(f"{k}={v}" for k, v in built.items())


class NIMSPApi:
    """A caller and wrapper to the NIMSP API"""

    URL = "https://api.followthemoney.org"
    API_KEY = None
    TOKEN_REF = {
        "APIKey": "API Key",
        "mode": "Page Format",
        "gro": "Group By",
        "so": "Sort By",
        "sod": "Sorting Direction",
        "s": "Election State",
        "y": "Election Year",
        "f-s": "Filing State",
        "f-eid": "Filer",
        "f-y": "Filing Year",
        "c-r-osid": "Offce Sought",
        "c-r-oc": "Offce",
        "c-t-i": "Incumbency Data",
        "c-t-icod": "Incumbency Advantage",
        "d-nme": "Original Name",
        "d-amt": "Amount",
        "d-dte": "Date",
        "d-ludte": "Last Updated",
        "d-typ": "Type of Transaction",
        "d-ad-str": "Street",
        "c-t-id": "Candidate",
        "c-t-p": "Political Party",
        "c-t-pt": "Party Details",
        "c-t-eid": "Career Summary",
        "c-r-id": "Political Race",
        "c-r-ot": "Type of Offce",
        "c-t-sts": "Status of Candidate",
        "c-t-ico": "Incumbency Status",
        "d-id": "Record",
        "d-eid": "Contributor",
        "d-et": "Type of Contributor",
        "d-ccb": "Business Classification",
        "d-cci": "Industry",
        "d-ccg": "Sector",
        "d-ad-cty": "City",
        "d-ad-st": "State",
        "d-ad-zip": "Zip",
        "d-ins": "In-State",
        "d-empl": "Employer",
        "d-occupation": "Occupation",
    }

    TOKEN_VALUE_REF = {"sod": {"0": "Descending", "1": "Ascending"}}

    def __init__(self) -> None:
        self.__built = {
            "APIKey": self.API_KEY,
            "mode": "json",
        }

    def build(self, params: dict):
        """Create the URL parameters appropriate for the API call"""
        self.__built.update(params)

    def unbuild(self, param_names):
        """Deconstruct URL parameters"""
        for p in param_names:
            self.__built.pop(p)

    @property
    def url(self):
        """Combine the URL parameters to be part of the main URL"""
        return f"{self.URL}/?{combine_params(self.__built)}"

    @staticmethod
    def get_active_params(url: str):
        """Gets the current URL parameters from the URL"""
        return split_params(url.split("?")[-1])

    def make_call(self, params: dict = None):
        """Makes the API call by sending a request"""

        if not params:
            params = {}

        if set(self.__built).intersection(set(params)):
            self.__built.update(params)

        combined_params = combine_params(params)
        url = f"{self.url}{'&' if combined_params else ''}{combined_params}"

        try:
            response = requests.get(url)

        except:
            return {}, {}

        active_params = self.get_active_params(response.url)

        try:
            data = json.loads(response.text)
            # Parameters may be used for reporting
            return NIMSPJson(data), active_params

        except json.decoder.JSONDecodeError:
            return NIMSPJson(dict({})), active_params


class JSONObject:
    """JSON mapping into python object for data extraction from Web APIs"""

    def __init__(self, data: dict):
        self.__data = data

    @property
    def data(self) -> dict:
        return self.__data

    @data.setter
    def data(self, data):
        self.__data = data

    def get(self, key):
        return self.__data.get(key)

    def export(self, filepath):
        with open(filepath, "w") as f:
            f.write(str(self))

    def __str__(self):
        return json.dumps(self.data, indent=4)

    def __repr__(self) -> str:
        return str(self)


class NIMSPJson(JSONObject):
    """Root of the JSON produce from NIMSP APIs"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.__root = data

    @property
    def root(self) -> dict:
        return self.__root

    @property
    def meta_info(self):
        return MetaInfo(self.root)

    @property
    def records(self):
        return Records(self.root)

    def export_root(self, filepath):
        with open(filepath, "w") as f:
            f.write(json.dumps(self.root, indent=4))


class MetaInfo(NIMSPJson):
    """Second to records, this will provide information about the records itself"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("metaInfo")

    @property
    def format(self) -> str:
        return self.get("format")

    @property
    def reports(self):
        return Reports(self.root)

    @property
    def pages(self):
        return Pages(self.root)

    @property
    def grouping(self):
        return Grouping(self.root)

    @property
    def sorting(self):
        return Sorting(self.root)

    @property
    def record_format(self) -> dict:
        return RecordFormat(self.root)


class Reports(MetaInfo):
    """This contains all the records in the JSON"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("completeness")

    @property
    def all(self) -> int:
        return int(self.get("allReports"))

    @property
    def available(self) -> int:
        return int(self.get("availableReports"))

    @property
    def complete(self) -> int:
        return int(self.get("completeReports"))

    @property
    def incomplete(self) -> int:
        return int(self.get("incompleteAvailable"))

    @property
    def last_updated(self) -> datetime | None:
        try:
            return datetime.strptime(self.get("lastUpdated"), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    @property
    def recent_date(self) -> datetime | None:
        try:
            return datetime.strptime(self.get("mostRecentReportDate"), "%Y-%m-%d")
        except ValueError:
            return None


class Pages(MetaInfo):
    """Desribe the structure of each page from the API call"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("paging")

    @property
    def params(self) -> dict:
        return split_params(self.get("pageLink"))

    @property
    def start(self) -> int:
        return self.get("minPage")

    @property
    def last(self) -> int:
        return self.get("maxPage")

    @property
    def current(self) -> int:
        return self.get("currentPage")

    @property
    def total(self) -> int:
        return self.get("totalPages")

    @property
    def total_records(self) -> int:
        return int(self.get("totalRecords"))

    @property
    def records(self) -> int:
        return self.get("recordsPerPage")

    @property
    def records_this_page(self) -> int:
        return self.get("recordsThisPage")


class Grouping(MetaInfo):
    """Data generated by the API has a grouping by default"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("grouping")

    @property
    def params(self) -> dict:
        return split_params(self.get("groupLink"))

    @property
    def current(self) -> dict:
        return self.get("currentGrouping")

    @property
    def available(self) -> dict:
        return self.get("availableGrouping")


class Sorting(MetaInfo):
    """Data generated by the API can be sorted by the token name"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("sorting")

    @property
    def params(self) -> str:
        return split_params(self.get("sortLink"))

    @property
    def current(self) -> list:
        return self.get("currentSorting")

    @property
    def available(self) -> dict:
        return self.get("availableSorting")

    @property
    def direction(self) -> str:
        return self.get("sortingDirection")


class RecordFormat(MetaInfo):
    """Describes the structure for each record"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("recordFormat")
        self.ignore = [
            "request",
        ]

    @property
    def params(self) -> dict:
        return split_params(self.get("request"))

    @property
    def columns(self) -> list:
        return [k for k in self.data if k not in self.ignore]


class Tag(JSONObject):
    """Each section (column) in a single record called a tag. It
    contains the token, id and value.
    """

    def __init__(self, data: dict, name) -> None:
        super().__init__(data)
        self.__name = name

    @property
    def name(self) -> str:
        return self.__name

    @property
    def token(self) -> str:
        return self.get("token")

    @property
    def id(self) -> str:
        return self.get("id")

    @property
    def value(self) -> str:
        return self.get(self.__name)


class Record(JSONObject):
    """A single record generated by the API"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.ignore = [
            "record_id",
            "request",
        ]

    @property
    def id(self) -> str:
        return self.get("record_id")

    @property
    def params(self) -> dict:
        return split_params(self.get("request"))

    @property
    def all(self) -> list[Tag]:
        return [
            Tag(self.get(tag_name), tag_name)
            for tag_name in self.data
            if tag_name not in self.ignore
        ]


class Records(NIMSPJson):
    """Contains multiple records"""

    def __init__(self, data: dict):
        super().__init__(data)
        self.data = self.get("records")

    @property
    def all(self) -> list[Record]:
        return [Record(record) for record in self.data]
