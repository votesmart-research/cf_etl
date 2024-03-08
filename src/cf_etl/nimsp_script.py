import os
import argparse
from pathlib import Path
from datetime import datetime

# External packages and libraries
import pandas
from dotenv import load_dotenv

# Internal packages and libraries
if __name__ == '__main__':
    from nimsp.extract import main as extract
    from nimsp.transform import main as transform
    from nimsp.match import main as nimsp_match
else:
    from cf_etl.nimsp.extract import main as extract
    from cf_etl.nimsp.transform import main as transform
    from cf_etl.nimsp.match import main as nimsp_match


def save_records(records: dict[int, dict[str, str]], filepath: Path, filename: str=None):

    filepath.mkdir(exist_ok=True)

    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

    df = pandas.DataFrame.from_dict(records, orient='index')
    df.to_csv(
        filepath / f"{filename if filename else "records"}_{timestamp}.csv",
        index=False,
    )


def main():

    parser = argparse.ArgumentParser(prog="campaign_finance_nimsp")

    parser.add_argument(
        "-y",
        "--year",
        required=True,
        help="election year of candidates",
    )

    parser.add_argument(
        "-d",
        "--export_path",
        type=Path,
        required=True,
        help="filepath of the directory where files are exported to",
    )

    parser.add_argument(
        "-jd",
        "--json_path",
        type=Path,
        help="filepath of the JSON files to read",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="filepath of the spreadsheet file to read",
    )

    parser.add_argument(
        "-e",
        "--extract",
        action='store_true',
        help="calls the extract module",
    )

    parser.add_argument(
        "-t",
        "--transform",
        action='store_true',
        help="calls the transform module",
    )

    parser.add_argument(
        "-m",
        "--match",
        action='store_true',
        help="calls the match module",
    )

    args = parser.parse_args()

    package_dir = Path(__file__).parent
    load_dotenv(package_dir / 'config' / '.env')

    db_connection_info = {
        'host': os.getenv('VSDB_HOST'),
        'dbname': os.getenv('VSDB_DATABASE'),
        'port':os.getenv('VSDB_PORT'),
        'user':os.getenv('VSDB_USER'),
        'password':os.getenv('VSDB_PASSWORD'),
    }
    if not(any((args.extract, args.transform, args.match))):
        records_extracted = extract(os.getenv('NIMSP_API_KEY'), args.year, args.export_path, args.json_path)
        
        print("Extracting...")
        save_records(records_extracted,
                    args.export_path,
                    "NIMSP-Extract",)

        print("Transforming...")
        records_transformed = transform(records_extracted)
        save_records(records_transformed,
                    args.export_path,
                    "NIMSP-Transformed",)


        print("Matching...")
        records_verified, records_election_candidates = nimsp_match(records_transformed, db_connection_info)
        save_records(records_verified,
                    args.export_path,
                    "NIMSP-Matched_Verified",)
        
        save_records(records_election_candidates,
                    args.export_path,
                    "VSDB-Election-Candidates",)
        
    elif args.extract and not (any((args.transform, args.match))):
        records_extracted = extract(os.getenv('NIMSP_API_KEY'), args.year, args.export_path, args.json_path)
        save_records(records_extracted,
                    args.export_path,
                    "NIMSP-Extract",)
    
    elif args.transform and not (any((args.extract, args.match))):
        if not args.file:
            parser.print_help()
            parser.error('Please specify the filepath of the spreadsheet.')

        df_extracted = pandas.read_csv(args.file)
        records_extracted = df_extracted.to_dict(orient="index")

        records_transformed = transform(records_extracted)
        save_records(records_transformed,
                    args.export_path,
                    "NIMSP-Transformed",)

    elif args.match and not (any((args.extract, args.transform))):
        if not args.file:
            parser.print_help()
            parser.error('Please specify the filepath of the spreadsheet.')

        df_transformed = pandas.read_csv(args.file, na_values="", keep_default_na=False)
        records_transformed = df_transformed.to_dict(orient="index")

        records_verified, records_election_candidates = nimsp_match(records_transformed, db_connection_info)
        save_records(records_verified,
                     args.export_path,
                     "NIMSP-Matched_Verified",)
        
        save_records(records_election_candidates,
                     args.export_path,
                     "VSDB-Election-Candidates",)

    else:
        module_arguments = []

        if args.extract:
            module_arguments.append('-e')
        if args.transform:
            module_arguments.append('-t')
        if args.match:
            module_arguments.append('-m')

        parser.print_help()
        
        parser.error(f"Only one process module can be run one at a time, you have entered '{", ".join(module_arguments)}' at once,"
                     " which is ambiguous. If you want to run every process, please leave out the arguments.")


if __name__ == "__main__":
    main()
