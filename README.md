# WikiTools
Webapp tools for building Wikipedia literacy. Built with Flask, Jinja2, Bokeh, and various MediaWiki APIs.

## Tools:
- <b>PlotWikiRevisions:</b> A widget to plot the revisions to a given Wikipedia page over time.
- <b>PlotWikiEditors:</b> A widget to view the top ten editors by frequency for a given Wikipedia page over time.


## ToDo:
#### Structural Changes:
- Build Loading Screen
  - https://stackoverflow.com/questions/50400733/in-flask-can-i-show-one-template-while-a-function-runs-and-redirect-to-another
- Create 404 redirect, and rules on when to call it. (i.e. not when an API call returns an error.)

- Make wiki API call better:
  -[x] have it return a JSON instead of a tuple
  -[x] have it take rvprops as a list      
  -[x] have it  return more page info (pageviews, other stuff...)

- Pass data in url instead of re-querying Wikipedia:
  -[x] Pass existing users_and_timestamps variable
  - pass rv_data object instead, so that sidebar data is available also

#### Sidebar Edits:
-[x] Add original author
- Add avg. pageviews (last 60 days)
  - create new route for plot
  -[x] Design Bokeh plot for pageviews
- add percent of anonymous user edits


#### New Routes to make:
- Add revision length graphics.
    (can only query 50 revisions at a time.)
- User landing pages.
  - get more input first.


## Resources:
###### MediaWiki Action API Documentation
- https://www.mediawiki.org/wiki/API:Main_page

###### MediaWiki REST API Documentation
- https://wikimedia.org/api/rest_v1/

###### WMF Analytics APIs
- https://wikitech.wikimedia.org/wiki/Analytics_Engineering#Datasets


##### Sticking with Action for now, but may consider REST for profile pages.
- Analytics API may be useful for a rich pageviews experience.

###### Bokeh User Guide
- https://docs.bokeh.org/en/latest/docs/user_guide.html
