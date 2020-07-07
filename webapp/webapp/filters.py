
from webapp import app
import datetime
import jinja2
import timeago


@app.template_filter()
def timeago_fromiso(ts=False):
    if not ts:
        return ''
    ts = datetime.datetime.fromisoformat(ts)
    return timeago.format(ts, datetime.datetime.now())


@app.template_filter()
def duration_fromiso(ts=False):
    ts = datetime.datetime.fromisoformat(ts)
    return datetime.datetime.now() - ts


@app.template_filter()
def is_up_to_date(ts, max_weeks):
    ts = datetime.datetime.fromisoformat(ts)
    duration = datetime.datetime.now() - ts
    max_weeks = datetime.timedelta(weeks=max_weeks)
    print(max_weeks, duration)
    return duration < max_weeks


@app.template_filter()
def AttemptType(type=False):
    if type=='fetch':
        return 'Fetch'
    elif type=='funcTest':
        return 'Functionality Test'
    elif type=='syncDB_fetch':
        return 'Fetched & Saved'
    elif type=='syncDB_funcTest':
        return 'Tested & Synced'
    else:
        return ''

@app.template_filter()
def AttemptTypePassive(type=False):
    if type=='fetch':
        return 'fetched'
    elif type=='funcTest':
        return 'tested'
    elif type=='syncDB_fetch':
        return 'synced'
    elif type=='syncDB_funcTest':
        return 'synced'
    else:
        return ''