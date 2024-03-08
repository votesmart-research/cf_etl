====================
Campaign Finance ETL
====================

This repository contains scripts designed to extract data from Open Secrets and NIMSP, transform this data to fit the VoteSmart data model, 
and match the transformed data to assign a unique candidate ID from VoteSmart's database.

----------------------
Setup and Installation
----------------------

Requirements: Python 3.10 or higher, Python's pip 21.0 or higher, setuptools 61.0 or higher

Get source
----------

There are two options for you to get the source code. The first is to download the source code from GitHub. The second is preferred if you are 
planning on making changes to this repo.

1. Download and unzip `here <https://github.com/votesmart-research/campaign_finance_etl/archive/refs/heads/main.zip>`_.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2. Clone the Repository:
~~~~~~~~~~~~~~~~~~~~~~~~

On the terminal, type

   .. code-block:: bash
      
      git clone git@github.com:votesmart-research/campaign_finance_etl.git


Setup
------

You would need to create a .env file within the top direcotry of the source code. This file contains sensitive information and is not uploaded
to the main repository by default. Such information are the API Key that connects to NIMSP as well as read-only connection to VoteSmart's database.

Create the .env file
~~~~~~~~~~~~~~~~~~~~
Simply make a copy of the .env.sample file and remove '.sample' from the extension, and fill in the variables as you see fit.


1. **NIMSP API Key**
This would be the API key provided by NIMSP. 

2. **VoteSmart's Database Connection**
Vote Smart uses PostgreSQL for their database connection, so you will need the host, database name, port, username and password connection info.



Install
-------

1. Setting Up a Virtual Environment:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Although optional, it is highly recommended to use a virtual environment when running this application, as this would prevent any unintended system wide changes.


Within the repository folder that you downloaded (or cloned), perform the following on the terminal:

Create a virtual environment,

   .. code-block:: bash

      python3 -m venv venv/cf_etl


Activating virtual environment (on Windows),

   .. code-block:: bash

      .\venv\cf_etl\Scripts\activate


Activating virtual environment (on Mac),

   .. code-block:: bash

      source venv/cf_etl/bin/activate


2. Install using pip and setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Within the same repository, on the terminal, type (make sure you have already activated the virtual environment if you are using one):

   .. code-block:: bash

      pip3 install .

   

-----
Usage
-----

If you install this within a virtual environment, make sure to first activate it (see above for instructions), below shows the command you have after activating the environment

      .. code-block:: bash

         # For CRP
         cf_crp

         # For NIMSP
         cf_nimsp


Each of the command has their required parameters

For CRP,
   Required parameters:
   1. Filepath to CRP file (-f or --crp_file)
   2. Years: Can have multiple inputs (-y or --years)
   3. Export Directory (-d or --export_path)

For NIMSP,
   Required parameters:
   1. Year: Single input only (-y or --years)
   2. Export Directory (-d or --export_path)


**Example Usage**

   .. code-block:: bash

      # For CRP
      cf_crp -y 2023 2024 -f ~/Filepath/CRP_file.xlsx -d ~/Downloads

      # For NIMSP
      cf_nimsp -y 2024 -d ~/Downloads



----------------
Reviewer's Guide
----------------

This section outlines a checklist for reviewing the campaign finance matched spreadsheet. The goal is to ensure all candidates from the 
campaign finance groups (OpenSecrets or NIMSP) are accurately matched with candidates in our database. 
It's expected to find unmatched candidates or matching errors. After reviewing, an "Import" sheet will be prepared for IT to update the database. 
To avoid assigning the wrong unique ID (finsource_candidate_id) to a candidate, it's crucial to correct any matching errors.

It's not necessary to follow every item if you're familiar with the process. Avoid doing multiple checklist items at once to prevent confusion 
and ensure a thorough review. Rather, work on them one at a time, such that if you are working on section A, 
then continue working on section A until you have finished handling that particular issue. 
The general rule is to thoroughly complete one section before moving on to the other.

A. Handling Duplicates Within the Matched File
----------------------------------------------

Steps:
~~~~~~

1. Filter rows marked as 'DUPLICATES' in the match status column.
2. Sort the 'candidate_id' column to compare duplicated IDs side-by-side.
3. Sort the 'match_score' column to prioritize higher or lower scores.
4. Decide which candidate_ids to remove.

Considerations:
~~~~~~~~~~~~~~~

- Prioritize candidates with higher match scores.
- Verify if the candidate information in the matched file matches VoteSmart's database.

  * Use the 'Find' feature to search candidate by candidate_id in the Query file or search in Admin to compare candidate information.

Known Cases:
~~~~~~~~~~~~

#. **Same person but different finsource_candidate_ids**: If a single person has multiple finsource_candidate_ids for different elections, keep the ID that best represents their campaign.

#. **Different persons with the same VoteSmart candidate_id**: Keep the one with the higher match score.


B. Reviewing Matches That Need Attention
----------------------------------------

Steps:
~~~~~~

1. Filter rows marked as 'REVIEW' in the match status column.
2. Optionally, sort by 'match_score' to prioritize which candidates to review.
3. Filter out rows already marked as entered (contains 'Entered for...') in our database if needed.

Considerations:
~~~~~~~~~~~~~~~

- Confirm if the candidate information matches between the matched file and VoteSmart's database (via the Query file or Admin)
- Candidates with identical matching scores are likely correctly matched, this would same some time to review, although thoroughly reviewing them would be preferred.

Known Cases:
~~~~~~~~~~~~

#. If candidate information matches, the candidate_id is likely correct.

#. If information does not match, consider removing the candidate_id.


C. Addressing Ambiguous Matches
-------------------------------

Ambiguous matches often arise from apparent duplicates in our database. Not every case is a duplicate in our database, some may just be a very probable match.

Steps:
~~~~~~

1. Filter row marked as 'AMBIGUOUS' in the match status column.

Considerations:
~~~~~~~~~~~~~~~

- Each case must be reviewed to see if it is the correct match.
- Spouses sharing the same last name, office and district.
- Different persons but sharing very similar information
- Actual duplicates within our database though one with more information (such as experience and education) than the other.

Known Cases:
~~~~~~~~~~~~

1. **Duplicated candidates within our database**: May need consolidation, either merging their information on Admin or deleting one without merging them (may need to consult the Elections Director)

2. **Non-duplicated candidates but sharing very similar information**: Choose the one with the most appropriate match (see 'matched with rows' and add 2 to the row index)


D. Correcting finsource_candidate_id Assignments
------------------------------------------------

Considerations:
~~~~~~~~~~~~~~~

- Focus on entries marked as "Entered for {candidate_id}" to correct errors.

Known Cases:
~~~~~~~~~~~~

#. **Previously entered for the correct candidate**: If a finsource_candidate_id had already been previously entered correctly for another candidate, you may verify for potential duplicates. Note: This program may not always be right.

#. **Previously entered for a wrong candidate**: Correct past errors by reassigning the finsource_candidate_id to the correct candidate.


E. Finalizing Review & Creating Import Sheet
--------------------------------------------

IMPORTANT: This section should only be completed when all of the section above is considered for.

Steps:
~~~~~~

1. Filter to exclude blank 'candidate_id' rows.
2. Exclude rows already marked as entered ('YES' in the 'Entered for {finsource}' column)
3. Prepare a new spreadsheet with necessary candidate_id and finsource_candidate_id columns for import.
4. May repeat step 1 to 3 for different finsource (hint: CID vs FECCandID)


