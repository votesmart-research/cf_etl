# Campaign Finance ETL pipeline

This repository contains scripts designed to extract data from Open Secrets and NIMSP, transform this data to fit the VoteSmart data model, and match the transformed data to assign a unique candidate ID to each candidate from VoteSmart's database.

</br>

# User Guide

This section is a guide for users of this pipeline.

## Download

**Requirements:** Python 3.10 or higher, Python's pip 21.0 or higher, setuptools 61.0 or higher

### Get source

There are two ways to download the code:

   1. **Download and unzip [here](https://github.com/votesmart-research/campaign_finance_etl/archive/refs/heads/main.zip).**

   2. **Clone the Repository (do this if you are planning to maintain this repository):**

      On the terminal, type

      ```bash
      git clone git@github.com:votesmart-research/campaign_finance_etl.git
      ```
      It is better to fork the repository if you are working with another person rather than making changes directly to the main repo.


## Setup

Before installation, there are a few patch ups in order for the program to be installed correctly.

### Create a .env file
This file contains sensitive information and is not uploaded to the main repository by default. The .env file contains the following information:

   1. **NIMSP API Key**: This would be the API key provided by NIMSP.
      
   2. **VoteSmart's Database Connection**: This is the conenction info to connect to VoteSmart's database

#### Create a `.env` file within this directory:

```bash
src/cf_etl/config/.env
```

*Make a copy of the `.env.sample` file and remove '.sample' from the extension, and fill in the variables as described in the file.*


## Installation
If you are a maintaner of this repo, you might want to follow the maintainer's installation guide below.

### Create a Virtual Environment

   Although optional, it is highly recommended to install the application to a virtual environment, as this would prevent any unintended system-wide changes.

   **On the terminal,**

   ```bash
   python3 -m venv ~/venv/cf_etl
   ```

   **Activate virtual environment on Windows,**
   ```bash
   .~\venv\cf_etl\Scripts\activate
   ```

   **Activate virtual environment on Mac,**

   ```bash
   source ~/venv/cf_etl/bin/activate
   ```

### Install using pip and setuptools

Within the top directory of the folder, on the terminal type:

   ```bash
   pip3 install .
   ```

### Installing Postgres
Psycopg is a dependency of this package. The pure python installation of psycopg in the requirements.txt assumes that libpq (the library for Postgres) is provided system-wide. Using a pure python version of psycopg avoids any conflict that might occur if the user had already install postgres on their system. 

This package may not work if you have not installed postgres, to install postgres use this [link](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).


## Usage

Two commands will be available after installation. If package is installed in a virtual environment, be sure to activate it.

```bash
# For CRP
cf_crp

# For NIMSP
cf_nimsp
```
Running individual script is possible, although not recommended as the pipeline is desgined to be ran using commands.

The commands above accepts required inputs such as the Election year(s) of the candidates (-y), filepath (-f) and export directory (-d). It also accepts optional parameters such as (-e), (-t) and (-m), these parameters are used to call individual process modules, and can only be used one at a time.

### Example Usage

```bash
# For CRP
cf_crp -f ~/Filepath/CRP_File.xlsx -d ~/Export_Direcotry -y 2023 2024

# For NIMSP
cf_nimsp -d ~/Export_Direcotry -y 2024
```

### Help with parameters

```bash
# For CRP
cf_crp --help

# For NIMSP
cf_nimsp --help
```

## Configuration

There are settings on this pipeline that requires re-configurations from time to time, this will require re-installation of the program.

### Uninstall

**To uninstall, on the terminal type,**

```bash
pip3 uninstall cf_etl
```

### Re-configure .env file

If the information within the .env file changes, such as a change in the database connection info or getting a new NIMSP API Key. 

Reflect changes in the .env file within this folder,

```bash
src/cf_etl/config/.env
```
Create a new .env file if there is none (see 'Setup' for instructions).

After changing .env file, make sure to re-install the program (see 'Installation' for instructions).


## Maintenance
If you are both a user and a maintainer (developer) of this project, there are some guide here that will make your life easier.

### Installing by symlink
Instead of installing the project (aka copying files), you create a symlink to the project directory (aka creating a shortcut). This will ensure that any changes to the project does not require a re-installation.

To do this, within your project directory type,
```bash
pip3 install -e .
```

### Forking this repository
Use a fork instead of cloning this repo directly to your local environment. Fork this repo, clone the forked repo to your local environment. That way, if any changes to the project, it will only affect your forked repo, and you can merge with this repo when you are ready. This is to reduce conflict occuring within the main repo, and it can get quite complicated with multiple pull requests. 


</br>
</br>

# Reviewer's Guide

This section outlines a checklist for reviewing the campaign finance matched spreadsheet. The goal is to ensure all candidates from the campaign finance groups (OpenSecrets or NIMSP) are accurately matched with candidates in our database. It's expected to find unmatched candidates or matching errors. After reviewing, an "Import" sheet will be prepared for IT to update the database. To avoid assigning the wrong unique ID (finsource_candidate_id) to a candidate, it's crucial to correct any matching errors.

It's not necessary to follow every item if you're familiar with the process. Avoid doing multiple checklist items at once to prevent confusion and ensure a thorough review. Rather, work on them one at a time, such that if you are working on section A, then continue working on section A until you have finished handling that particular issue. The general rule is to thoroughly complete one section before moving on to the other.

## A. Handling Duplicates Within the Matched File

### Steps:

1. Filter rows marked as 'DUPLICATES' in the match status column.
2. Sort the 'candidate_id' column to compare duplicated IDs side-by-side.
3. Sort the 'match_score' column to prioritize higher or lower scores.
4. Decide which candidate_ids to remove.

### Considerations:

- Prioritize candidates with higher match scores.
- Verify if the candidate information in the matched file matches VoteSmart's database.
  - Use the 'Find' feature to search candidate by candidate_id in the Query file or search in Admin to compare candidate information.

### Known Cases:

1. **Same person but different finsource_candidate_ids**:</br>
   If a single person has multiple finsource_candidate_ids for different elections, keep the ID that best represents their campaign.

2. **Different persons with the same VoteSmart candidate_id**:</br>
   Keep the one with the higher match score.

## B. Reviewing Matches That Need Attention

### Steps:

1. Filter rows marked as 'REVIEW' in the match status column.
2. Optionally, sort by 'match_score' to prioritize which candidates to review.
3. Filter out rows already marked as entered (contains 'Entered for...') in our database if needed.

### Considerations:

- Confirm if the candidate information matches between the matched file and VoteSmart's database (via the Query file or Admin)
- Candidates with identical matching scores are likely correctly matched, this would save some time to review, although thoroughly reviewing them would be preferred.

### Known Cases:

1. If candidate information matches, the candidate_id is likely correct.

2. If information does not match, consider removing the candidate_id.

## C. Addressing Ambiguous Matches

Ambiguous matches often arise from apparent duplicates in our database. Not every case is a duplicate in our database, some may just be a very probable match.

### Steps:

1. Filter row marked as 'AMBIGUOUS' in the match status column.

### Considerations:

- Each case must be reviewed to see if it is the correct match.
- Spouses sharing the same last name, office, and district.
- Different persons but sharing very similar information
- Actual duplicates within our database

### Known Cases:

1. **Duplicated candidates within our database**:</br>
   May need consolidation, either merging their information on Admin or deleting one without merging them (may need to consult the Elections Director)

2. **Non-duplicated candidates but sharing very similar information**:</br>
   Choose the one with the most appropriate match (see 'matched with rows' and add 2 to the row index)

## D. Correcting finsource_candidate_id assignments

### Considerations:

- Focus on entries marked as "Entered for {candidate_id}" to correct errors.

### Known Cases:

1. **Previously entered for the correct candidate**:</br>
   If a finsource_candidate_id had already been previously entered correctly for another candidate, you may verify for potential duplicates. Note: This program may not always be right.

2. **Previously entered for a wrong candidate**:</br>
   Correct past errors by reassigning the finsource_candidate_id to the correct candidate.

## E. Finalizing Review & Creating Import Sheet

**IMPORTANT:** This section should only be completed when all of the sections above are accounted for.

### Steps:

1. Filter to exclude blank 'candidate_id' rows.
2. Exclude rows already marked as entered ('YES' in the 'Entered for {finsource}' column)
3. Prepare a new spreadsheet with necessary candidate_id and finsource_candidate_id columns for import.
4. May repeat steps 1 to 3 for different finsource (hint: CID vs FECCandID)
