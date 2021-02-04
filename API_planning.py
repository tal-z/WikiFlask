from datetime import datetime, timedelta
import requests
import numpy as np
from flask import Flask, render_template, request, url_for
from bokeh.plotting import figure, show, output_file
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import LassoSelectTool, HoverTool, ColumnDataSource
from bokeh.models.widgets import Panel, Tabs
import urllib.parse
import ast
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
            print("revisions queried:", len(revisions))
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
            print("revisions queried:", len(revisions))

            #print(len(revisions))
            #pass


        self.revisions_data = page_info
        self.revisions = page_info['revisions']
        self.rv_timestamps = [item['timestamp'] for item in page_info['revisions'] if 'timestamp' in item]
        self.rv_users = [item['user'] for item in page_info['revisions'] if 'user' in item]
        return self

    #def revisions_content(self, props='revisions|pageviews|info', rvprops='user|timestamp|size|content', inprops='protection|watchers', **kwargs):

def get_revision_timestamps_and_users(TITLE=str):
    # base URL for API call
    BASE_URL = "http://en.wikipedia.org/w/api.php"

    # empty list to hold our timestamps once retrieved.
    revision_list = []

    # first API call. This loop persists while revision_list is empty
    while not revision_list:
        # set parameters for API call
        parameters = {'action': 'query',
                      'format': 'json',
                      'continue': '',
                      'titles': TITLE,
                      'prop': 'revisions',
                      'rvprop': 'ids|user|timestamp',
                      'rvlimit': '500'}
        # make the call
        wp_call = requests.get(BASE_URL, params=parameters)
        # get the response
        response = wp_call.json()

        # now we parse the response.
        pages = response['query']['pages']
        page_id = list(pages.keys())[0]
        page_info = pages[str(page_id)]
        revisions = page_info['revisions']

        # Now that the response has been parsed and we can access the revision timestamps, add them to our revision_list.
        for entry in revisions:
            try:
                revision_list.append((str(entry['user']), entry['timestamp']))
            except:
                revision_list.append(('None', entry['timestamp']))

        # revision_list is no longer empty, so this loop breaks.


    ## next series of passes, until you're done.
    ## this makes calls until the limit of 500 results per call is no longer reached.
    else:
        while str(len(revisions)) == parameters['rvlimit']:
            start_id = revision_list[-1]
            parameters = {'action': 'query',
                          'format': 'json',
                          'continue': '',
                          'titles': TITLE,
                          'prop': 'revisions',
                          'rvprop': 'ids|user|timestamp',
                          'rvlimit': '500',
                          'rvstart': start_id}

            # same as before
            wp_call = requests.get(BASE_URL, params=parameters)
            response = wp_call.json()

            pages = response['query']['pages']
            page_id = list(pages.keys())[0]
            page_info = pages[str(page_id)]
            revisions = page_info['revisions']

            for entry in revisions:
                try:
                    revision_list.append((str(entry['user']), entry['timestamp']))
                except:
                    revision_list.append(('None', entry['timestamp']))

    # end by returning a list of revision timestamps
    return revision_list

def dictify(some_list=list):
    result = {}
    for k, v in some_list:
        result.setdefault(k, []).append(v)
    return result


page_title = 'Robinhood (company)'
# page_title = page_title[0].upper() + page_title[1:]
page_title = page_title.title()

rv_data = Wiki_Query(page_title).revisions_data()
users_and_timestamps = [(a,b) for a,b in zip(rv_data.rv_users, rv_data.rv_timestamps)]

timestamps = rv_data.rv_timestamps
timestamps.reverse()

num_revisions = len(timestamps)

editors = set(rv_data.rv_users)
num_editors = len(editors)
anonymous_edits_count = sum([1 for item in rv_data.revisions if 'anon' in item])
registered_edits_count = num_revisions - anonymous_edits_count
orig_author = rv_data.rv_users[-1]

pageviews = rv_data.revisions_data['pageviews']
pv_dates = [datetime.strptime(d, '%Y-%m-%d') for d in pageviews.keys()]
pv_counts = [item for item in pageviews.values() ]

for c,d in zip(pv_counts,pv_dates):
    print(type(c), c, d)
avg_pageviews_60 = np.around(np.average(pv_counts),decimals=2)


print(pv_dates)
print(pv_counts)


source = ColumnDataSource(data=dict(days=pv_dates,
                                    views=pv_counts,
                                    days_str=[str(d.date()) for d in pv_dates],
                                    color=['#0072B2' for item in rv_data.revisions_data['pageviews']]
                                    ))



p1 = figure(title=page_title,
            x_axis_label='Time In Days',
            y_axis_label='Views Per Day',
            x_axis_type='datetime',
            tools="pan,wheel_zoom,box_zoom,undo,redo,reset,save")

# add a line renderer for Hovertool tracking.
#p1line = p1.line('days', 'views', name=page_title, source=source, alpha=0.)
# Add vbar for data display
p1.vbar(x='days', width=timedelta(days=.8), top='views', source=source)

# add an interactive tools to the visual
p1.add_tools(HoverTool(tooltips=[("Date", "@days_str"), ("# views", "@views")],
                       mode='vline',
                       point_policy='follow_mouse'
                       #renderers=[p1line]
                       ))

p1.toolbar.logo = None

p1.background_fill_color = "#eeeeee"
p1.xaxis.axis_line_color = "#bcbcbc"
p1.yaxis.axis_line_color = "#bcbcbc"
p1.left[0].formatter.use_scientific = False


output_file('APItest.html')

show(p1)




print("Total anonymous edits:", anonymous_edits_count)
print("Total registered edits:", registered_edits_count)
print("daily average pageviews (last 60 days):", avg_pageviews_60)

