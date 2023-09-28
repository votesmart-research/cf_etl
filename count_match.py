from collections import Counter
def get_total_match(df):
     matched = df[df['match_status']=='MATCHED']
     counted = Counter(matched['match_score'])
     total = 0
     for k,v in counted.items():
             total += k/100*v
     return total/len(matched)
