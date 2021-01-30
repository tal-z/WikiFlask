

#for removal
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

#I think for removal
def user_edits(title=str):
    stamps_users = get_revision_timestamps_and_users(title)
    user_freqs = {tup[0]:[item[1] for item in stamps_users if item[0]==tup[0]] for tup in stamps_users}
    return dict(sorted(user_freqs.items(), key=lambda x: len(x[1])))


#for removal
@app.route('/PlotWikiRevisions')
def PlotWikiRevisions():
    return render_template('PlotWikiRevisions.html')

#for removal
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

#for removal
@app.route('/PlotWikiEditors')
def PlotWikiEditors():
    return render_template('PlotWikiEditors.html')

#for removal
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



@app.route('/PlotWikiRevFreqs_JINJA')
def PlotWikiRevFreqs_JINJA():
    html =  '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
    title = "Search Revisions on Wikipedia Over Time"
    num_revisions = ''
    num_editors = ''
    return render_template('PlotWikiRevFreqs_JINJA.html', html=html, title=title, num_revisions=num_revisions, num_editors=num_editors)


@app.route('/plot_wiki_rev_freqs_JINJA')
def plot_wiki_rev_freqs_JINJA():
    try:
        page_title = request.args.get('page_title')
        page_title = page_title[0].upper() + page_title[1:]
        title = f'Frequency of Revisions to the "<a href="https://en.wikipedia.org/wiki/{page_title}">{page_title}</a>" Wikipedia Page'

        timestamps_and_users = get_revision_timestamps_and_users(page_title)
        timestamps = [item[1] for item in timestamps_and_users]
        timestamps.reverse()
        num_revisions = len(timestamps)

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

        days_str = days
        days = [datetime.combine(day, datetime.min.time()) for day in days]



        source = ColumnDataSource(data=dict(x_values=days,
                                            y_values=date_freqs,
                                            desc=days_str,
                                            yy_values=[d-1 for d in date_freqs],
                                            color=['#0072B2' for d in days],
                                            color2=['red' for d in days],
                                            ))

        def get_width():
            mindate = min(source.data['x_values'])
            maxdate = max(source.data['x_values'])
            return 0.8 * (maxdate - mindate).total_seconds() * 1000 / len(source.data['x_values'])

        p = figure(title=page_title, x_axis_label='Time In Days', y_axis_label='Revisions Per Day', x_axis_type='datetime',
                   tools="pan,wheel_zoom,box_zoom,undo,redo,reset,save")

        # add a line renderer with legend and line thickness
        p.line('x_values', 'y_values', name=page_title, color='red', source=source, alpha=0)

        # Note that there is a bug with vertical bars and hovertools. A fix is in the works per GitHub.
        p.vbar(x='x_values', width=get_width(), color='color', top='y_values', bottom=0, source=source)
        #p.vbar(x='x_values', width=1 / len(days), color='color2', top='yy_values', bottom=0, source=source)

        #band = Band(base='x_values', upper='y_values', source=source, level='underlay',
         #           fill_alpha=0.2, fill_color='#55FF88')
        #p.add_layout(band)



        # add some interactive tools to the visual
        p.add_tools(LassoSelectTool())
        p.add_tools(HoverTool(tooltips=[("Date", "@desc"), ("# Revisions", "@y_values")], mode='vline'))

        p.toolbar.logo = None

        p.background_fill_color = "#eeeeee"
        p.xaxis.axis_line_color = "#bcbcbc"
        p.yaxis.axis_line_color = "#bcbcbc"
        #p.legend.visible = False




        html = file_html(p, CDN, page_title)

        return render_template('PlotWikiRevFreqs_JINJA.html', html=html, page_title=page_title, title=title, num_revisions=num_revisions, num_editors=num_editors)

    except:
        print(len(page_title))
        if len(page_title) == 0:
            num_revisions = ''
            num_editors = ''
            title = "Search Revisions on Wikipedia Over Time"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='static/W_mark.png'" alt="Click below"/></div>'''
            return render_template('PlotWikiRevisions_JINJA.html', html=html, page_title=page_title, image='static/W_mark.png', title=title, num_revisions=num_revisions, num_editors=num_editors)
        else:
            num_revisions = 0
            num_editors = 0
            title = "Search Revisions on Wikipedia Over Time"
            html = '''<div id="chart"><img class="about" src="{{image}}" onerror="this.onerror=null; this.src='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg'" alt="Click below"/></div>'''
            return render_template('PlotWikiRevisions_JINJA.html', html=html, page_title=page_title, image='https://upload.wikimedia.org/wikipedia/commons/a/a0/Font_Awesome_5_regular_frown.svg', title=title, num_revisions=num_revisions, num_editors=num_editors)



