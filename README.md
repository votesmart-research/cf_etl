# Campaign Finance ETL

#### This respository contains scripts that are built to extract data from Open Secrets and NIMSP, transform the extracted data that fits the VoteSmart's data model, match the transformed data so that each will be assigned a unique candidate id from the VoteSmart's database.


## Verifying the Results
This section serves as a comprehensive checklist for reviewing the campaign finance matched spreadsheet. The objective of this review is to ensure accurate matching of all candidates from the campaign finance (CF) groups (OpenSecrets or NIMSP) with candidates from our database. It is expected that there will be candidates that are not matched or errors in matching. Upon completion of the review, an "Import" sheet will be created for submission to IT for database entry. To prevent assigning the finsource_candidate_id (a unique id given to a campaign by a CF group) to the wrong candidate, it is imperative to correct any matching errors.

Correcting errors may involve deleting the candidate_id from the spreadsheet or removing wrongly assigned finsource_candidate_id on Admin.

It is not necessary to go through every item on the checklist if you are already familiar with the process. It is recommended to avoid performing multiple checklist items simultaneously to prevent confusion and overlook important reviews; conducting them one at a time is the most effective approach to avoid confusion.


## A. Dealing with duplicates within the matched file

### Steps:
1. Filter the rows to show only the ones with ‘DUPLICATES’ match status
2. Arrange the column ‘candidate_id’ in order (ascending or descending doesn’t matter), this puts the duplicated candidate_ids for side-by-side comparison
3. Arrange the column ‘match_score’ in order (ascending or descending doesn’t matter), this helps visualize either the top or bottom with the higher or lower score
4. Start choosing which candidate_ids to delete

### Things to look out for:
- Which candidates have the highest score; usually, the one with the higher score is the correct one
- Check to see if the candidate_info (includes names and election info) in the matched file (from CF group) matches with the candidate info in Vote Smart’s database as suggested by the candidate_id
    - 2 ways:
        - Copy & Paste candidate_id onto the ‘Find’ in the Query file and look at the candidate info on the row it returns, compare the info with the one on the matched file
        - Copy & Paste candidate_id onto Admin and search for the candidate to compare candidate info on the matched file vs Admin

### Known cases:
1. **Same person but 2 or more different finsource_candidate_id while having the same PVS candidate_id matched to it**
   The same person might have run for multiple elections and thus have 2 or more finsource_candidate_id for each of the races. This is how the CF group’s organized their data, much like how we may have multiple election_candidate_ids for each unique candidate_id. In this case, you should leave the candidate_id that has the best representation from the finsource_candidate_id and delete the one that doesn’t.
   - **The objective best is to satisfy this question: Does this finsource_candidate_id pull the campaign finance data that correctly reflects the election that the candidate is running for?**

2. **Different person and different finsource_candidate_id while having the same PVS candidate_id matched to it**
   This happens when there are two very probable candidate matches from our perspective, though one usually is higher than the other. In this case, you should leave behind the candidate_id (again from our perspective) that has the higher match score and delete the one with the lower score.



## B. Dealing with matches that needs to be reviewed

### Steps:
1. Filter the rows to show only the ones with ‘REVIEW’ match status
2. Arrange the column ‘match_score’ in order (ascending or descending doesn’t matter), this helps prioritize which candidates to check for (optional if you are going to review all of them)
3. Filter out the rows that are marked “YES” on the “...ENTERED?” column. You won’t be importing the ones that are already entered on our database (also optional if you think it is necessary that you review all of them—no kidding.)

### Things to look out for:
- Exact matching scores for a group of 3 or more candidates. Typically, a group of candidates having the same matching scores are likely to be correctly matched, this is due to the program agreeing that individual columns have data structured in a way that will always return a set score. However, your discretion is advised! It might hurt to review all, but it is always good to be thorough.

- Check to see if the candidate_info (includes names and election info) in the matched file (from CF group) matches with the candidate info in Vote Smart’s database as suggested by the candidate_id
    - 2 ways:
        - Copy & Paste candidate_id onto the ‘Find’ in the Query file and look at the candidate info on the row it returns, compare the info with the one on the matched file
        - Copy & Paste candidate_id onto Admin and search for the candidate info to compare candidate info on the matched file

### Known cases:
1. Candidate info (includes names and election info) that match up
   If it’s true, leave the candidate_id; you are probably right!

2. Candidate info (includes names and election info) that doesn’t match up
   If it’s true, remove the candidate_id; you are probably right!


## C. Dealing with ambiguous matches (potential duplicates within our database)

Ambiguous matches occur due to apparent duplicates in our database, although it is likely not the case. This situation often arises with married couples who are candidates but one has passed away and the other took their office, both having the same last names and first names producing no significant difference. In technical terms, the program produces the same matching score for 2 or more candidates.

### Steps:
1. Filter the rows to show only the ones with ‘AMBIGUOUS’ match status

### Things to look out for:
You will have to review each one of them. This is a rare case, so it shouldn’t be many unless there is something wrong with the queried datasets from our database.

### Known cases:
1. **Duplicated candidates within our database**
   This occurs when biographical and election info is shared between 2 or more candidate_ids albeit the same person. Bring this to the attention of your superiors or if you have the authority to delete them, do so.
   
2. **Non-duplicated candidates within our database but share very similar info**
   This only happens when one or more columns return the same score albeit having different values, this is a fuzzy string matching issue. Example: ‘Kim’ matching with ‘Jim’ vs ‘Kim’ matching with ‘Tim’ will produce the same matching score, assuming all other info is kept constant.


## D. Dealing with finsource_candidate_id that have been assigned to another candidate_id(s) other than the ones being matched

**finsource_candidate_id columns: CID, FECCandID, NIMSP_ID**

- **YES:** the candidate_id on that row already has the finsource_candidate_id for that row assigned to it
- **NO:** the candidate_id on that row does not have the finsource_candidate_id for that row assigned to it
- **“Entered for (other candidate_id)”:** the finsource_candidate_id on that row is assigned to another candidate_id in our database

### Steps:
1. Filter the rows to show only “Entered for…” on the “...ENTERED?” column

### Things to look out for:
- **Match status**
  Depending on the filtered rows, the match_status may or may not matter. 
  If there are any statuses other than “UNMATCHED” (you can filter them out), and you have already reviewed them, you may just ignore the candidate_id portion (that may or may not be empty). If it’s not empty, turn your focus then to the candidate_id(s) that are in “Entered for…”.
  
- **Multiple candidate_ids in the “Entered for…” column**
  This signifies that there are more than one candidate on our database that is assigned the same finsource_candidate_id. This is obviously an error since more than one person cannot receive more than one finsource_candidate_id, the only possible exception is that they are running the same campaign like a Governor and Lieutenant governor.

### Known cases:

1. **Had already been entered correctly for a candidate**
   This could mean that the current match is wrong. Either that or it is a duplicate candidate within our database. There have been cases where we create another newer candidate which is a duplicate of the old one, most likely caused by being oblivious to the old candidates. In this case, if it is not a duplicate, then you could just remove the candidate_id on the spreadsheet. If it is a duplicate, make sure that the duplicate is merged with the candidate with the older id.
   
2. **Previously entered for a wrong candidate**
   This could mean that we have made an error in the past. In this case, make sure to remove the finsource_candidate_id previously assigned to the wrong candidate. Although there are some cases where the one previously entered is a duplicate of the one currently matched. If the one previously entered is a duplicate, make sure it is merged with the currently matched candidate.


## E. Finalizing Review & Creating Import Sheet

Once you have done all the necessary checks, it is time to create the import sheet.

### Steps:

1. Filter out rows that are blank on the ‘candidate_id’ column
2. Filter out rows that are “YES” on the “...ENTERED?” column
3. Create a new spreadsheet
4. **Copy & Paste** both “candidate_id” and a finsource_candidate_id column (CID, FECCandID, NIMSP_ID)
5. Repeat the process from step 3 if there are more than one finsource_candidate_id (in the case of Open Secrets)

**Copy the whole column by selecting every possible row or you can also just click on the alphabet on top of the column names.
