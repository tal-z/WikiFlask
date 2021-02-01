# WikiTools
Webapp tools for building Wikipedia literacy. Built with Flask, Jinja2, Bokeh, and various MediaWiki APIs.

## Tools:
- <b>PlotWikiRevisions:</b> A widget to plot the revisions to a given Wikipedia page over time.
- <b>PlotWikiEditors:</b> A widget to view the top ten editors by frequency for a given Wikipedia page over time.


## ToDo:
#### Structural Changes:
- Make wiki API call better:
  - have it return a JSON instead of a tuple
  - have it take rvprops as a list      
  - have it  return more page info (pageviews...

#### Sidebar Edits:
- Add average Edit Length


## Resources:
###### MediaWiki Action API Documentation
- https://www.mediawiki.org/wiki/API:Main_page
###### Bokeh Users Guide
- https://docs.bokeh.org/en/latest/docs/user_guide.html