from flask import Flask, render_template, request
import requests
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from base64 import b64encode


# define a function that will get all of the revision timestamps for a given article
# The function takes a string of the correctly-spelled article title as its argument

def get_revision_timestamps(TITLE):
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
                      'rvprop': 'ids|userid|timestamp',
                      'rvlimit': '500'}
        # make the call
        wp_call = requests.get(BASE_URL, params=parameters)
        # get the response
        response = wp_call.json()

        # now we parse the response.
        query = response['query']
        pages = query['pages']
        page_id_list = list(pages.keys())
        page_id = page_id_list[0]
        page_info = pages[str(page_id)]
        revisions = page_info['revisions']

        # Now that the response has been parsed and we can access the revision timestamps, add them to our revision_list.
        for entry in revisions:
            revision_list.append(entry['timestamp'])
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
                          'rvprop': 'ids|userid|timestamp',
                          'rvlimit': '500',
                          'rvstart': start_id}

            # same as before
            wp_call = requests.get(BASE_URL, params=parameters)
            response = wp_call.json()

            query = response['query']
            pages = query['pages']
            page_id_list = list(pages.keys())
            page_id = page_id_list[0]
            page_info = pages[str(page_id)]
            revisions = page_info['revisions']

            for entry in revisions:
                revision_list.append(entry['timestamp'])

    # end by returning a list of revision timestamps
    return revision_list



app = Flask(__name__)

@app.route('/')
def PlotWikiRevisions():
    return render_template('PlotWikiRevisions.html')


@app.route('/plot')
def plot():
    page_title = request.args.get('page_title')
    page_title = page_title[0].upper() + page_title[1:]
    print(page_title)
    try:
        timestamps = get_revision_timestamps(page_title)
        timestamps.reverse()

        dates = []
        for stamp in timestamps:
            d = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ')
            dates.append(d)

        plt.style.use('bmh')
        plt.clf()
        plt.plot()
        plt.plot_date(dates, range(len(dates)), color="green")
        plt.title(f'Revisions to the "{page_title.title()}" Wikipedia Page', wrap=True)
        plt.xlabel('Time')
        plt.ylabel('Revisions count')
        plt.xticks(rotation=60)
        plt.gcf().subplots_adjust(bottom=.2)



        stream = BytesIO()
        plt.savefig(stream, format='png')
        stream.seek(0)

        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += b64encode(stream.getvalue()).decode('utf8')

        return render_template('PlotWikiRevisions.html', image=pngImageB64String)

    except:
        return render_template('PlotWikiRevisions.html', image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg')


if __name__ == "__main__":
    app.run()