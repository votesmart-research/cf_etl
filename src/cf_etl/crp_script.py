import os
import argparse
from pathlib import Path
from datetime import datetime

# External packages and libraries
import pandas
from dotenv import load_dotenv

# Internal packages and libraries
if __name__ == '__main__':
    from crp.extract import main as extract
    from crp.match import main as match
    from crp.transform import main as transform
else:
    from cf_etl.crp.extract import main as extract
    from cf_etl.crp.match import main as match
    from cf_etl.crp.transform import main as transform


def save_records(records: dict[int, dict[str, str]], filepath: Path, filename: str=None):

    filepath.mkdir(exist_ok=True)

    timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M%S-%f")

    df = pandas.DataFrame.from_dict(records, orient='index')
    df.to_csv(
        filepath / f"{filename if filename else "records"}_{timestamp}.csv",
        index=False,
    )

def main():
    
    parser = argparse.ArgumentParser(prog='campaign_finance_crp')

    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        required=True,
        help="filepath of the spreadsheet file to read",
    )
    
    parser.add_argument(
        "-d",
        "--export_path",
        type=Path,
        required=True,
        help="filepath of the directory where files are exported to",
    )
    parser.add_argument(
        "-y",
        "--years",
        nargs="+",
        required=True,
        help="election year(s) of candidates",
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
        records_extracted = extract(args.file)
        save_records(records_extracted,
                     args.export_path,
                     'CRP-Extract',)

        records_transformed = transform(records_extracted)
        save_records(records_transformed,
                     args.export_path,
                     'CRP-Transformed',)

        records_verified, records_queried = match(records_transformed, db_connection_info, args.years)
        save_records(records_verified,
                     args.export_path,
                     'CRP-Matched-Verified',)

        save_records(records_queried,
                     args.export_path,
                     'VSDB-Election-Candidates',)
    
    elif args.extract and not (any((args.transform, args.match))):
        records_extracted = extract(args.file)
        save_records(records_extracted,
                     args.export_path,
                     'CRP-Extract',)
    
    elif args.transform and not (any((args.extract, args.match))):
        df_extracted = pandas.read_csv(args.file)
        records_extracted = df_extracted.to_dict(orient="index")

        records_transformed = transform(records_extracted)
        save_records(records_transformed,
                     args.export_path,
                     'CRP-Transformed',)

    elif args.match and not (any((args.extract, args.transform))):
        df_transformed = pandas.read_csv(args.file, na_values="", keep_default_na=False)
        records_transformed = df_transformed.to_dict(orient="index")

        records_verified, records_queried = match(records_transformed, db_connection_info, args.years)
        save_records(records_verified,
                     args.export_path,
                     'CRP-Matched-Verified',)

        save_records(records_queried,
                     args.export_path,
                     'VSDB-Election-Candidates',)

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

if __name__ == '__main__':
    main()
