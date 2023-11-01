from dns.asyncresolver import Resolver
import dns.resolver
import dns.rrset
import asyncio
from typing import Tuple
import csv

'''
Checks for DMARC records very quickly via Async DNS queries and writes TRUE/FALSE to a CSV file whether or not the domain has a DMARC record.

Usage:
    python3 check_dmarc.py
    
Files:
    lgcrm_domains.csv - CSV file with domains to check [companyid, domain]
'''


async def dns_query(domain: str, rtype: str = 'A', **kwargs) -> dns.rrset.RRset:
    kwargs, res_cfg = dict(kwargs), {}
    # extract 'filename' and 'configure' from kwargs if they're present
    # to be passed to Resolver. we pop them to avoid conflicts passing kwargs
    # to .resolve().
    if 'filename' in kwargs: res_cfg['filename'] = kwargs.pop('filename')
    if 'configure' in kwargs: res_cfg['configure'] = kwargs.pop('configure')

    # create an asyncio Resolver instance
    rs = Resolver(**res_cfg)

    # call and asynchronously await .resolve() to obtain the DNS results
    res: dns.resolver.Answer = await rs.resolve('_dmarc.'+domain, rdtype=rtype, **kwargs)

    # we return the most useful part of Answer: the RRset, which contains
    # the individual records that were found.
    return res.rrset


async def dns_bulk(*queries: Tuple[str, str], **kwargs):
    ret_ex = kwargs.pop('return_exceptions', True)
    
    # Iterate over the queries and call (but don't await) the dns_query coroutine
    # with each query.
    # Without 'await', they won't properly execute until we await the coroutines
    # either individually, or in bulk using asyncio.gather
    coros = [dns_query(dom, rt, **kwargs) for dom, rt in list(queries)]

    # using asyncio.gather, we can effectively run all of the coroutines
    # in 'coros' at the same time, instead of awaiting them one-by-one.
    #
    # return_exceptions controls whether gather() should immediately
    # fail and re-raise as soon as it detects an exception,
    # or whether it should just capture any exceptions, and simply
    # return them within the results.
    #
    # in this example function, return_exceptions is set to True,
    # which means if one or more of the queries fail, it'll simply
    # store the exceptions and continue running the remaining coros,
    # and return the exceptions inside of the tuple/list of results.
    return await asyncio.gather(*coros, return_exceptions=ret_ex)


async def main():
    
    bucket_limit        = 500   # bucket_limit of 500 queries per bulk request
    results             = []    # list of dns results
    queries_bucket_500  = []    # list of tuples of (domain, record type), 500 max
    queries             = []    # list of tuples of (domain, record type)
    
    # Read in CSV file with domains to check
    with open('input/lgcrm_domains.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        reader.__next__() # skip header rowclea
        for row in reader:
            queries.append((row[1], 'TXT'))

    
    # Now we sort the DNS queries into buckets of 500:    
    while queries:
        try:
            queries_bucket_500.append(queries[:bucket_limit]) # get first 500 queries
            queries = queries[bucket_limit:]                  # remove first 500 queries from original list
            queries_bucket_500 = queries_bucket_500[0] # flatten list of queries
            
        # If there are less than 500 queries left, we'll get an IndexError and need to handle it differently
        except IndexError:
            queries_bucket_500.append(queries)          # get remaining queries
            queries_bucket_500  = queries_bucket_500[0] # flatten list of queries
            queries             = []                    # remove remaining queries from original list
        
        finally:
            # Now we check for DMARC records:
            res = await dns_bulk(*queries_bucket_500)   # pass list of queries to dns_bulk()
            results.append(res)                         # append results to list
            

    # Write results to CSV file:
    with open('output/results.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        for i, a in enumerate(results):
            _domain = queries_bucket_500[i][0] # domain
            _cid    = queries_bucket_500[i][1] # companyid
            
            # If there's an exception, write FALSE to CSV file because there's no DMARC record
            if isinstance(a, Exception):
                writer.writerow([_cid, _domain, "FALSE"])
                print(f" [!!!] {_domain}\t\t=> FALSE")
                continue
            
            # If there's no exception, write TRUE to CSV file because there's a DMARC record
            writer.writerow([_cid, _domain, "TRUE"])
            print(f" [+++] {_domain}\t\t=> TRUE")
        
        
# Run the main() function event loop:
asyncio.run(main())