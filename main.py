from flask import Flask, render_template, request, url_for
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

def user_edits(title=str):
    stamps_users = get_revision_timestamps_and_users(title)
    user_freqs = {tup[0]:[item[1] for item in stamps_users if item[0]==tup[0]] for tup in stamps_users}
    return dict(sorted(user_freqs.items(), key=lambda x: len(x[1])))


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

app = Flask(__name__)

@app.route("/")
def index():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))


    return render_template('site-map.html', links=links)
    # links is now a list of url, endpoint tuples



@app.route('/PlotWikiRevisions')
def PlotWikiRevisions():
    return render_template('PlotWikiRevisions.html')


@app.route('/plot_wiki_revisions')
def plot_wiki_revisions():
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



        stream = BytesIO()
        plt.savefig(stream, format='png')
        stream.seek(0)

        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += b64encode(stream.getvalue()).decode('utf8')

        return render_template('PlotWikiRevisions.html', image=pngImageB64String)

    except:
        return render_template('PlotWikiRevisions.html', image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg')


@app.route('/PlotWikiEditors')
def PlotWikiEditors():
    return render_template('PlotWikiEditors.html')


@app.route('/plot_wiki_editors')
def plot_wiki_editors():
    page_title = request.args.get('page_title')
    page_title = page_title[0].upper() + page_title[1:]
    try:
        user_edits_list = user_edits(page_title).items()
        user_edits_list_len = len(user_edits_list)
        count = 0
        color_count = 0
        colors = [ '#320E3B', '#FF499E', '#A480CF', '#1E2EDE', '#47A8BD',  '#53FF45',  '#EFCA08',  '#FB6107', '#EC0B43', '#89043D']
        plt.clf()
        plt.title(f'Most Frequent Editors of the "{page_title.title()}" Wikipedia Page (Top 10)', wrap=True)
        plt.xlabel('Time')
        plt.ylabel('Revisions count')
        plt.xticks(rotation=60)

        for entry in user_edits_list:
            timestamps = entry[1]
            timestamps.reverse()

            dates = [datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ') for d in timestamps]

            plt.plot()

            if count >= user_edits_list_len - 10:
                plt.plot_date(dates, range(len(dates)), linestyle='solid', marker='.', markersize=1.25, label=entry[0], color=colors[color_count])
                color_count += 1
            else:
                plt.plot_date(dates, range(len(dates)), linestyle='solid', marker='.', markersize=1.25, label='_nolegend_', color='#D8DDDE')

            count += 1

        handles, labels = plt.gca().get_legend_handles_labels()
        plt.legend(handles[::-1], labels[::-1], loc='upper left', ncol=1, bbox_to_anchor=(1.05, 1), borderaxespad=0.)


        plt.tight_layout()
        plt.gcf().subplots_adjust(top=.8)


        stream = BytesIO()
        plt.savefig(stream, format='png')
        stream.seek(0)

        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += b64encode(stream.getvalue()).decode('utf8')

        return render_template('PlotWikiEditors.html', image=pngImageB64String)
    except:
        return render_template('PlotWikiEditors.html', image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg')



@app.route('/PlotWikiEditors_JINJA')
def PlotWikiEditors_JINJA():
    return render_template('PlotWikiEditors_JINJA.html')

@app.route('/plot_wiki_editors_JINJA')
def plot_wiki_editors_JINJA():
    page_title = request.args.get('page_title')
    page_title = page_title[0].upper() + page_title[1:]
    try:
        title = f'Most Frequent Editors of the "{page_title.title()}" Wikipedia Page (Top 10)'
        user_edits_list = user_edits(page_title).items()
        user_edits_list_len = len(user_edits_list)
        count = 0
        color_count = 0
        colors = [ '#320E3B', '#FF499E', '#A480CF', '#1E2EDE', '#47A8BD',  '#53FF45',  '#EFCA08',  '#FB6107', '#EC0B43', '#89043D']
        plt.clf()

        plt.xlabel('Time')
        plt.ylabel('Revisions count')
        plt.xticks(rotation=60)
        user_colors = []

        for entry in user_edits_list:
            timestamps = entry[1]
            timestamps.reverse()

            dates = [datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ') for d in timestamps]

            plt.plot()

            if count >= user_edits_list_len - 10:
                plt.plot_date(dates, range(len(dates)), linestyle='solid', marker='.', markersize=1.25, label=entry[0], color=colors[color_count])
                user_colors.append((entry[0], colors[color_count]))
                color_count += 1
            else:
                plt.plot_date(dates, range(len(dates)), linestyle='solid', marker='.', markersize=1.25, label='_nolegend_', color='#D8DDDE')

            count += 1

        #handles, labels = plt.gca().get_legend_handles_labels()
        #plt.legend(handles[::-1], labels[::-1], loc='upper left', ncol=1, bbox_to_anchor=(1.05, 1), borderaxespad=0.)


        plt.tight_layout()
        #plt.gcf().subplots_adjust(top=.8)


        stream = BytesIO()
        plt.savefig(stream, format='png')
        stream.seek(0)

        pngImageB64String = "data:image/png;base64,"
        pngImageB64String += b64encode(stream.getvalue()).decode('utf8')

        print(user_colors)

        return render_template('PlotWikiEditors_JINJA.html', image=pngImageB64String, user_colors=reversed(user_colors), title=title)
    except:
        return render_template('PlotWikiEditors_JINJA.html', image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg', user_colors=reversed(user_colors), title=title)


if __name__ == "__main__":
    app.run(debug=True)