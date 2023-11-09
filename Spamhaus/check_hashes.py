import os
import subprocess
import shlex

subprocess.text_mode = True
query_key = os.environ.get()


query_urls = {
    'HBL':f"{query_key}.hbl.dq.spamhaus.net",
}


def get_hashes():
    hashes = []
    print("Getting hashes from file...")
    with open('hashes.txt', 'r') as output:
        lines = output.readlines()
        for l in lines:
            if l.startswith("\tHASH"):
                hash_line = l
                hash = hash_line.split('=> ')[-1].rstrip()
                
                index = lines.index(l)
                _url = lines[index - 1].rstrip()
                
                print(_url, ":", hash)
                hashes.append([_url, hash])
    return hashes

def check_hashes(hashes):
    results = []
    # run a terminal command
    for query_string in hashes:
        _url, hash = query_string
    
        cmd=f"dig {hash}._url.{query_urls['HBL']} +short > /dev/null"
        
        proc=subprocess.Popen(shlex.split(cmd),stdout=subprocess.PIPE)
        
        out,err=proc.communicate()
        
        results.extend([_url, str(out)])
    
    return results
        
        
        
 

    
hashes  = get_hashes()
results = check_hashes(hashes)

for result in results:
    print(result, '\n')

