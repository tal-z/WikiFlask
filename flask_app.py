from datetime import datetime
import requests
import numpy as np
from flask import Flask, render_template, request, url_for, session
from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import LassoSelectTool, HoverTool, ColumnDataSource
from bokeh.models.widgets import Panel, Tabs
import urllib.parse
import ast
import hmac
import hashlib
import os
try:
    from pip._internal.vcs import git
except:
    import git



""" 8) """

def dictify(some_list=list):
    result = {}
    for k, v in some_list:
        result.setdefault(k, []).append(v)
    return result

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
            #print(len(revisions))
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

            #print(len(revisions))
            #pass


        self.revisions_data = page_info
        self.revisions = page_info['revisions']
        self.rv_timestamps = [item['timestamp'] for item in page_info['revisions'] if 'timestamp' in item]
        self.rv_users = [item['user'] for item in page_info['revisions'] if 'user' in item]
        return self

    #def revisions_content(self, props='revisions|pageviews|info', rvprops='user|timestamp|size|content', inprops='protection|watchers', **kwargs):


def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

app = Flask(__name__)



@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method == 'POST':
        github_secret_token = os.getenv('github_secret_token')
        x_hub_signature = request.headers.get('X-Hub-Signature')
        if is_valid_signature(x_hub_signature, request.data, github_secret_token):
            repo = git.Repo('WikiTools/WikiTools')
            origin = repo.remotes.origin
            origin.pull()
            return ('Updated PythonAnywhere successfully', 200)
        else:
            return ('Signature not validated', 400)
    else:
        return ('Wrong event type', 400)

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
        page_title = page_title.title()

        try:
            print("trying")
            users_and_timestamps = urllib.parse.unquote(request.args.get('chart_data'))
            users_and_timestamps = ast.literal_eval(users_and_timestamps)
            print("success!")
        except:
            print('fail')
            rv_data = Wiki_Query(page_title).revisions_data()
            users_and_timestamps = [(a, b) for a, b in zip(rv_data.rv_users, rv_data.rv_timestamps)]
            print('done failing')

        timestamps = [item[1] for item in users_and_timestamps]
        timestamps.reverse()
        num_revisions = len(timestamps)

        orig_author = users_and_timestamps[-1][0]
        editors = set(item[0] for item in users_and_timestamps)
        num_editors = len(editors)

        user_edits_dict = dictify(users_and_timestamps)
        user_edits_dict = dict(sorted(user_edits_dict.items(), key=lambda x: len(x[1])))
        user_edits_list = list(user_edits_dict.items())
        user_edits_list_len = len(user_edits_list)

        color_count = 0
        colors = ['#348ABD', '#A60628', '#7A68A6', '#467821', '#D55E00', '#CC79A7', '#56B4E9', '#009E73', '#F0E442',
                  '#0072B2']
        users_colors = []

        p = figure(title=page_title,
                   x_axis_label='Time',
                   y_axis_label='Count of Revisions',
                   x_axis_type='datetime',
                   tools="pan,wheel_zoom,box_zoom,undo,redo,reset,save")

        for entry in user_edits_list[-10:]:
            ts = entry[1]
            ts.reverse()

            dates = [datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ') for d in ts]

            p.line(dates, range(len(dates)), name=entry[0], line_width=2, color=colors[color_count])

            users_colors.append((entry[0], colors[color_count]))
            color_count += 1

        # add some interactive tools to the visual
        p.add_tools(LassoSelectTool())
        p.add_tools(HoverTool(tooltips=[('Name', "$name"), ('Revision #', "$index")], mode='mouse'))

        p.toolbar.logo = None

        p.background_fill_color = "#eeeeee"
        p.xaxis.axis_line_color = "#bcbcbc"
        p.yaxis.axis_line_color = "#bcbcbc"

        html = file_html(p, CDN, "my plot")
        title = f'Editors of the "<a href="https://en.wikipedia.org/wiki/{page_title}">{page_title}</a>" Wikipedia Page (Top 10)'
        chart_data = urllib.parse.urlencode({'chart_data': users_and_timestamps})
        return render_template('PlotWikiEditors_JINJA.html',
                               html=html,
                               user_colors=reversed(users_colors),
                               title=title,
                               page_title=page_title,
                               num_revisions=num_revisions,
                               num_editors=num_editors,
                               orig_author=orig_author,
                               chart_data=chart_data)

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
        page_title = page_title.title()
        title = f'Revisions to the "<a href="https://en.wikipedia.org/wiki/{page_title}">{page_title}</a>" Wikipedia Page Over Time'

        try:
            users_and_timestamps = urllib.parse.unquote(request.args.get('chart_data'))
            users_and_timestamps = ast.literal_eval(users_and_timestamps)

        except:
            rv_data = Wiki_Query(page_title).revisions_data()
            users_and_timestamps = [(a, b) for a, b in zip(rv_data.rv_users, rv_data.rv_timestamps)]


        timestamps = [item[1] for item in users_and_timestamps]
        timestamps.reverse()
        num_revisions = len(timestamps)
        orig_author = users_and_timestamps[-1][0]

        editors = set(item[0] for item in users_and_timestamps)
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

        tab2 = Panel(child=p2, title='Cumulative')

        tabs = Tabs(tabs=[tab1, tab2])

        html = file_html(tabs, CDN, page_title)

        chart_data = urllib.parse.urlencode({'chart_data':users_and_timestamps})
        return render_template('PlotWikiRevisions_JINJA.html',
                               html=html,
                               page_title=page_title,
                               title=title,
                               num_revisions=num_revisions,
                               num_editors=num_editors,
                               orig_author=orig_author,
                               chart_data=chart_data)

    except:
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