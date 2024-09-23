SELECT 
	DISTINCT ON (candidate_id) 
    code, 
	candidate_id

FROM finsource_candidate

WHERE 
	finsource_id = ANY(%(finsource_ids)s)
	AND code LIKE ANY(%(finsource_codes)s)
