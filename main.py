from datetime import datetime
import requests
import numpy as np
from flask import Flask, render_template, request, url_for
from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import LassoSelectTool, HoverTool, ColumnDataSource
from bokeh.models.widgets import Panel, Tabs




## for improvement.
# Make it return a dictionary with values accessible by keyword
# instead of a tuple with values accessible by position.
# make it take a list of rvprops to return
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


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

app = Flask(__name__)




@app.route("/")
def Index():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))


    return render_template('site-map.html', links=links)
    # links is now a list of url, endpoint tuples


@app.route('/PlotWikiEditors_JINJA')
def PlotWikiEditors_JINJA():
    num_revisions = ''
    num_editors = ''
    title = "Search Editors on Wikipedia (Top 10)"
    html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
    return render_template('PlotWikiEditors_JINJA.html',
                           html=html,
                           image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg',
                           title=title,
                           num_revisions=num_revisions,
                           num_editors=num_editors)


@app.route('/plot_wiki_editors_JINJA')
def plot_wiki_editors_JINJA():
    try:
        page_title = request.args.get('page_title')
        page_title = page_title[0].upper() + page_title[1:]

        timestamps_and_users = get_revision_timestamps_and_users(page_title)
        timestamps = [item[1] for item in timestamps_and_users]
        timestamps.reverse()
        num_revisions = len(timestamps)
        orig_author = timestamps_and_users[-1][0]

        editors = set(item[0] for item in timestamps_and_users)
        num_editors = len(editors)

        user_freqs = {tup[0]: [item[1] for item in timestamps_and_users if item[0] == tup[0]] for tup in
                      timestamps_and_users}
        user_freqs = dict(sorted(user_freqs.items(), key=lambda x: len(x[1])))
        user_edits_list = user_freqs.items()
        user_edits_list_len = len(user_edits_list)

        count = 0
        color_count = 0
        colors = ['#348ABD', '#A60628', '#7A68A6', '#467821', '#D55E00', '#CC79A7', '#56B4E9', '#009E73', '#F0E442',
                  '#0072B2']
        user_colors = []

        p = figure(title=page_title,
                   x_axis_label='Time',
                   y_axis_label='Count of Revisions',
                   x_axis_type='datetime',
                   tools="pan,wheel_zoom,box_zoom,undo,redo,reset,save")

        for entry in user_edits_list:
            ts = entry[1]
            ts.reverse()

            dates = [datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ') for d in ts]

            if count >= user_edits_list_len - 10:
                p.line(dates, range(len(dates)), name=entry[0], line_width=2, color=colors[color_count])

                user_colors.append((entry[0], colors[color_count]))
                color_count += 1
            #else:
              #  p.line(dates, range(len(dates)), name=entry[0], line_width=2, color='#D8DDDE')

            count += 1

        # add some interactive tools to the visual
        p.add_tools(LassoSelectTool())
        p.add_tools(HoverTool(tooltips=[('Name', "$name"), ('Revision #', "$index")], mode='mouse'))

        p.toolbar.logo = None

        p.background_fill_color = "#eeeeee"
        p.xaxis.axis_line_color = "#bcbcbc"
        p.yaxis.axis_line_color = "#bcbcbc"
        #p.legend.visible = False

        html = file_html(p, CDN, "my plot")
        title = f'Editors of the "<a href="https://en.wikipedia.org/wiki/{page_title}">{page_title}</a>" Wikipedia Page (Top 10)'
        return render_template('PlotWikiEditors_JINJA.html',
                               html=html,
                               user_colors=reversed(user_colors),
                               title=title,
                               page_title=page_title,
                               num_revisions=num_revisions,
                               num_editors=num_editors,
                               orig_author=orig_author)

    except:
        if len(page_title) == 0:
            num_revisions = ''
            num_editors = ''
            title = "Search Editors on Wikipedia (Top 10)"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
            return render_template('PlotWikiEditors_JINJA.html',
                                   html=html,
                                   page_title=page_title,
                                   image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg',
                                   title=title,
                                   num_revisions=num_revisions,
                                   num_editors=num_editors)
        else:
            num_revisions = 0
            num_editors = 0
            title = "Search Editors on Wikipedia (Top 10)"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg'" alt="Click below"/></div>'''
            return render_template('PlotWikiEditors_JINJA.html',
                                   html=html,
                                   page_title=page_title,
                                   image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg',
                                   title=title,
                                   num_revisions=num_revisions,
                                   num_editors=num_editors)


@app.route('/PlotWikiRevisions_JINJA')
def PlotWikiRevisions_JINJA():
    html =  '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
    title = "Search Revisions on Wikipedia Over Time"
    num_revisions = ''
    num_editors = ''
    return render_template('PlotWikiRevisions_JINJA.html',
                           html=html,
                           title=title,
                           num_revisions=num_revisions,
                           num_editors=num_editors)


@app.route('/plot_wiki_revisions_JINJA')
def plot_wiki_revisions_JINJA():
    try:
        page_title = request.args.get('page_title')
        page_title = page_title[0].upper() + page_title[1:]
        title = f'Revisions to the "<a href="https://en.wikipedia.org/wiki/{page_title}">{page_title}</a>" Wikipedia Page Over Time'

        timestamps_and_users = get_revision_timestamps_and_users(page_title)
        timestamps = [item[1] for item in timestamps_and_users]
        timestamps.reverse()
        num_revisions = len(timestamps)
        orig_author = timestamps_and_users[-1][0]

        editors = set(item[0] for item in timestamps_and_users)
        num_editors = len(editors)

        dates = [datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ').date() for d in timestamps]
        days = sorted(list(set(dates)))

        date_freqs = {}
        for date in dates:
            if not str(date) in date_freqs:
                date_freqs[str(date)] = 1
            else:
                date_freqs[str(date)] += 1

        date_freqs = [item[1] for item in sorted(date_freqs.items(), key=lambda x: x[0])]
        cum_edits = np.cumsum(date_freqs)

        days_str = days
        days = [datetime.combine(day, datetime.min.time()) for day in days]

        source = ColumnDataSource(data=dict(x_values=days,
                                            y_values=date_freqs,
                                            desc=days_str,
                                            yy_values=[d - 1 for d in date_freqs],
                                            color=['#0072B2' for d in days],
                                            color2=['red' for d in days],
                                            cum_edits=cum_edits,
                                            ))

        def get_width():
            mindate = min(source.data['x_values'])
            maxdate = max(source.data['x_values'])
            return ((maxdate - mindate).total_seconds() * 1000 / len(source.data['x_values']))

        p1 = figure(title=page_title,
                    x_axis_label='Time In Days',
                    y_axis_label='Revisions Per Day',
                    x_axis_type='datetime',
                    tools="pan,wheel_zoom,box_zoom,undo,redo,reset,save")

        # add a line renderer for Hovertool tracking.
        p1line = p1.line('x_values', 'y_values', name=page_title, source=source, alpha=0)
        # Add vbar for data display
        p1.vbar(x='x_values', width=get_width(), color='color', top='y_values', bottom=0, source=source)

        # add an interactive tools to the visual
        p1.add_tools(HoverTool(tooltips=[("Date", "@desc"), ("# Revisions", "@y_values")],
                               mode='vline',
                               renderers=[p1line]))

        p1.toolbar.logo = None

        p1.background_fill_color = "#eeeeee"
        p1.xaxis.axis_line_color = "#bcbcbc"
        p1.yaxis.axis_line_color = "#bcbcbc"
        tab1 = Panel(child=p1, title='Frequency')

        p2 = figure(title=page_title,
                    x_axis_label='Time in Days',
                    y_axis_label='Count of Revisions',
                    x_axis_type='datetime',
                    tools="pan,wheel_zoom,box_zoom,reset,save")

        # add a line renderer for Hovertool tracking.
        p2line = p2.line('x_values', 'cum_edits', alpha=0, source=source)
        # Add vbar for data display
        p2.vbar(x='x_values', width=get_width(), color='color', top='cum_edits', bottom=0, source=source)

        # add some interactive tools to the visual
        p2.add_tools(HoverTool(tooltips=[("Date", "@desc"), ("# Revisions", "@cum_edits")],
                               mode='vline',
                               renderers=[p2line]))

        p2.toolbar.logo = None

        p2.background_fill_color = "#eeeeee"
        p2.xaxis.axis_line_color = "#bcbcbc"
        p2.yaxis.axis_line_color = "#bcbcbc"
        # p2.legend.visible = False
        tab2 = Panel(child=p2, title='Cumulative')

        tabs = Tabs(tabs=[tab1, tab2])

        html = file_html(tabs, CDN, page_title)

        return render_template('PlotWikiRevisions_JINJA.html',
                               html=html,
                               page_title=page_title,
                               title=title,
                               num_revisions=num_revisions,
                               num_editors=num_editors,
                               orig_author=orig_author)

    except:
        print(len(page_title))
        if len(page_title) == 0:
            num_revisions = ''
            num_editors = ''
            title = "Search Revisions on Wikipedia Over Time"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
            return render_template('PlotWikiRevisions_JINJA.html',
                                   html=html,
                                   page_title=page_title,
                                   image='static/W_mark.png',
                                   title=title,
                                   num_revisions=num_revisions,
                                   num_editors=num_editors)
        else:
            num_revisions = 0
            num_editors = 0
            title = "Search Revisions on Wikipedia Over Time"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg'" alt="Click below"/></div>'''
            return render_template('PlotWikiRevisions_JINJA.html',
                                   html=html,
                                   page_title=page_title,
                                   image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg',
                                   title=title,
                                   num_revisions=num_revisions,
                                   num_editors=num_editors)


if __name__ == "__main__":
    app.secret_key = 'helloworld'
    app.run(debug=True)