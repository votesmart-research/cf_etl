====================
Campaign Finance ETL
====================

This repository contains scripts designed to extract data from Open Secrets and NIMSP, transform this data to fit the VoteSmart data model, 
and match the transformed data to assign a unique candidate ID from VoteSmart's database.

------------------
Maintainer's Guide
------------------

This section is for the maintainer of this repository, who is responsible for running the scripts to update VoteSmart's campaign finance data, 
resolving any bugs or issue that comes with this repository and general understanding of this 

~~~~~~~~~~~~~~~~~~~~~~
Installation and Setup
~~~~~~~~~~~~~~~~~~~~~~

Before you begin, ensure you have Python installed on your system. This project requires Python 3.x.

1. **Cloning the Repository:**

   First, clone the repository to your local machine using Git:

   .. code-block:: bash
      
      git clone git@github.com:votesmart-research/campaign_finance_etl.git
      

2. **Setting Up a Virtual Environment:**

   It's recommended to use a virtual environment to manage the project's dependencies. Using virt

   Using venv:

   .. code-block:: bash

      python3 -m venv

      # Activate the virtual environment
      # On Windows
      .\venv\Scripts\activate
      # On Unix or MacOS
      source venv/bin/activate
      
3. **Installing Dependencies:**

   Install the required Python packages using pip:

   .. code-block:: bash

      pip install -r requirements.txt

Usage
~~~~~

After setting up the project, you can run the ETL scripts via the terminal. Ensure your virtual environment is activated.

.. code-block:: bash

   # Example command to run an ETL script
   python script_name.py

Replace `script_name.py` with the actual script you wish to run.

Basic Maintenance
~~~~~~~~~~~~~~~~~

- **Updating Dependencies:** Regularly check for updates to dependencies and update them using pip:

  .. code-block:: bash

     pip install --upgrade package_name

- **Virtual Environment Management:** Always activate your virtual environment before working on the project to avoid dependency conflicts.

- **Code Updates:** Pull the latest changes from the main branch frequently to keep your local repository up-to-date.

  .. code-block:: bash

     git pull origin main

---------------------
Verifying the Results
---------------------

This section outlines a checklist for reviewing the campaign finance matched spreadsheet. The goal is to ensure all candidates from the campaign finance groups (OpenSecrets or NIMSP) are accurately matched with candidates in our database. It's expected to find unmatched candidates or matching errors. After reviewing, an "Import" sheet will be prepared for IT to update the database. To avoid assigning the wrong unique ID (finsource_candidate_id) to a candidate, it's crucial to correct any matching errors.

It's not necessary to follow every item if you're familiar with the process. Avoid doing multiple checklist items at once to prevent confusion and ensure a thorough review. Rather, work on them one at a time, such that if you are working on section A, then continue working on section A until you have finished handling that particular issue. The general rule is to thoroughly complete one section before moving on to the other.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A. Handling Duplicates Within the Matched File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. Filter rows marked as 'DUPLICATES' in the match status column.
2. Sort the 'candidate_id' column to compare duplicated IDs side-by-side.
3. Sort the 'match_score' column to prioritize higher or lower scores.
4. Decide which candidate_ids to remove.

**Considerations:**

- Prioritize candidates with higher match scores.
- Verify if the candidate information in the matched file matches VoteSmart's database.

  * Use the 'Find' feature to search candidate by candidate_id in the Query file or search in Admin to compare candidate information.

**Known Cases:**

#. **Same person but different finsource_candidate_ids**: If a single person has multiple finsource_candidate_ids for different elections, keep the ID that best represents their campaign.

#. **Different persons with the same VoteSmart candidate_id**: Keep the one with the higher match score.


B. Reviewing Matches That Need Attention
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Steps:**

1. Filter rows marked as 'REVIEW' in the match status column.
2. Optionally, sort by 'match_score' to prioritize which candidates to review.
3. Filter out rows already marked as entered (contains 'Entered for...') in our database if needed.

**Considerations:**

- Confirm if the candidate information matches between the matched file and VoteSmart's database (via the Query file or Admin)
- Candidates with identical matching scores are likely correctly matched, this would same some time to review, although thoroughly reviewing them would be preferred.

**Known Cases:**

#. If candidate information matches, the candidate_id is likely correct.

#. If information does not match, consider removing the candidate_id.

C. Addressing Ambiguous Matches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ambiguous matches often arise from apparent duplicates in our database. Not every case is a duplicate in our database, some may just be a very probable match.

**Steps:**

1. Filter row marked as 'AMBIGUOUS' in the match status column.

**Considerations:**

- Each case must be reviewed to see if it is the correct match.
- Spouses sharing the same last name, office and district.
- Different persons but sharing very similar information
- Actual duplicates within our database though one with more information (such as experience and education) than the other.

**Known Cases:**

1. **Duplicated candidates within our database**: May need consolidation, either merging their information on Admin or deleting one without merging them (may need to consult the Elections Director)

2. **Non-duplicated candidates but sharing very similar information**: Choose the one with the most appropriate match (see 'matched with rows' and add 2 to the row index)

D. Correcting finsource_candidate_id Assignments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Considerations:**

- Focus on entries marked as "Entered for {candidate_id}" to correct errors.

**Known Cases:**

#. **Previously entered for the correct candidate**: If a finsource_candidate_id had already been previously entered correctly for another candidate, you may verify for potential duplicates. Note: This program may not always be right.

#. **Previously entered for a wrong candidate**: Correct past errors by reassigning the finsource_candidate_id to the correct candidate.

E. Finalizing Review & Creating Import Sheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IMPORTANT: This section should only be completed when all of the section above is considered for.

**Steps:**

1. Filter to exclude blank 'candidate_id' rows.
2. Exclude rows already marked as entered ('YES' in the 'Entered for {finsource}' column)
3. Prepare a new spreadsheet with necessary candidate_id and finsource_candidate_id columns for import.
4. May repeat step 1 to 3 for different finsource (hint: CID vs FECCandID)


