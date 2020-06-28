
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
    if not ts:
        return ''
    ts = datetime.datetime.fromisoformat(ts)
    return timeago.format(ts, datetime.datetime.now())