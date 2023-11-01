import requests
import json
import time
import pandas as pd

# Some constants that we need:
LIMIT       = 500                                   # 500 leads per API call
OFFSET      = 0                                     # start at the beginning of the leads list
ITERATION   = 0                                     # keep track of how many times we've looped through the leads
ACCID       = "XXXX"    # api account ID
SKEY        = "XXXX"    # api secret key

# URL for the LGCRM API w/ account ID and secret key:
url = f"https://api.sharpspring.com/pubapi/v1.2/?accountID={ACCID}&secretKey={SKEY}" 

'''
API call explanation:
--------------------
id      : the id of the api call, can be the same every time
method  : the method to call, in this case getLeads
params  : the parameters to pass to the API method. In this case:
    where   - the where clause, in this case we want all leads hence '{}'
    limit   - the number of leads to return per API call
    offset  - the number of leads to skip per API call
    fields  - the fields to return, in this case we want the lead id and email address (review the api schema for all available fields)
'''

records = [] # Create an empty list so we can append to it later

# While we still have leads remaining, run the API call:
while True:
    
    print("Starting Iteration: " + str(ITERATION))
    
    data = {
        "id": 1,
        "method": "getLeads",
        "params": {
            "where": {},
            "limit": LIMIT,
            "offset": OFFSET,
            "fields": [
                "id",
                "emailAddress"
            ]
        }
    }
    
    # Make the API call and store the result in a variable
    result = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'}).json()
    
    # If the result is not empty, append all the records to the list
    if result["result"]["lead"]:
        
        leads = result['result']['lead'] # store the leads in a variable
        
        print("\t=> " + str(len(leads)) + " leads found")
        
        # Loop through the leads and append the id and email address to the records list
        for lead in leads:
            records.append([
                lead["id"],
                lead["emailAddress"]
            ])
        
        OFFSET = OFFSET + LIMIT # increment the offset by the limit to get the next batch of leads
        ITERATION += 1          # increment the itteration counter
        time.sleep(0.007)       # For API limits/avoid timeouts
        
        print("\t=> " + str(len(records)) + " total leads processed")
    else:
        # If the result is empty, break from the loop because we're done
        break
    
# Put lead records from records list into a Pandas DataFrame:
records_df = pd.DataFrame(records, columns=["id", "emailAddress"])

# This ensures the data is loaded into Power BI:
print(records_df)