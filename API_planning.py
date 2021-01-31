import requests
import numpy as np
from pprint import PrettyPrinter
pp = PrettyPrinter()


# This returns pageviews elsewhere in the parsetree as an otherprop
# it also returns size in bytes (always a positive number, even when content is removed...)
# it also returns the full text of the wikipedia page.
## So, I guess I can measure the diffs myself. That seems exhaustive, though.

## Notes: Average edit diff is not hard to calculate, but is expensive. Make it an on-demand request.

class Wiki_Query():

    def __init__(self, title=str, *args, **kwargs):
        self.title = title
        self.action = 'query'


    def revisions_data(self, props='revisions|pageviews|info', rvprops='user|timestamp|size', inprops='protection|watchers', **kwargs):
        # base URL for API call
        BASE_URL = "http://en.wikipedia.org/w/api.php"

        # empty list to hold our timestamps once retrieved.
        revision_list = []
        while not revision_list:
            # set parameters for API call
            parameters = {'action': self.action,
                          'format': 'json',
                          'continue': '',
                          'titles': self.title,
                          'prop': props,
                          'rvprop': rvprops,
                          'inprop': inprops,
                          'rvlimit': 'max',
                          }

            # add keyword arguments to parameters prior to call
            parameters = {**parameters, **kwargs}
            #print(parameters)

            # make the call
            wp_call = requests.get(BASE_URL, params=parameters)
            # get the response
            response = wp_call.json()
            revision_list.append(response)


            # parse the response
            pages = response['query']['pages']
            page_id = list(pages.keys())[0]
            page_info = pages[str(page_id)]


            revisions = page_info['revisions']
            #daily_pageviews_dict = response['query']['pages'][page_id]['pageviews']
            """
            # calculating some stats. Perhaps move all calculations out of the function.
            #avg_daily_pageviews_60 = np.average([v for k,v in daily_pageviews_dict.items()]) # average daily pageviews, last 60 days
            # Revision stats should be moved out of the function. 
            #avg_rev_size = np.average([item['size'] for item in revisions]) # Average revision size (in bytes). This is all-time, since it's a revision property.
            #rev_char_counts = [len(item['*']) for item in revisions]
            #rev_char_counts.reverse()
            #rev_diffs = np.diff(rev_char_counts) # diffs matching those found on Wikipedia. Yay! In reverse order?
            #rev_diffs = reversed(rev_diffs)
            """


        while 'continue' in response:
            #print(response['continue']['rvcontinue'].split('|')[-1])
            start_id = response['continue']['rvcontinue'].split('|')[0]

            parameters = {'action': self.action,
                          'format': 'json',
                          'continue': '',
                          'titles': self.title,
                          'prop': 'revisions',
                          'rvprop': rvprops,
                          'rvlimit': 'max',
                          'rvstart': start_id}

            wp_call = requests.get(BASE_URL, params=parameters)
            response = wp_call.json()

            pages = response['query']['pages']
            page_id = list(pages.keys())[0]
            rev_info = pages[str(page_id)]

            #print(page_info.keys())
            revisions += rev_info['revisions']
            #print(len(revisions))
            #pass


        self.revisions_data = page_info
        self.revisions = page_info['revisions']
        self.rv_timestamps = [item['timestamp'] for item in page_info['revisions']]
        self.rv_users = [item['user'] for item in page_info['revisions']]
        return self.revisions_data

    #def revisions_content(self, props='revisions|pageviews|info', rvprops='user|timestamp|size|content', inprops='protection|watchers', **kwargs):




page = Wiki_Query(title='Ted Cruz')

