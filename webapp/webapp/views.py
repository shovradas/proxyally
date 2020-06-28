"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, redirect, url_for
from webapp import app
import requests
from config import API_ROOT


@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About'
    )

@app.route('/privacy')
def privacy():
    """Renders the privacy page."""
    return render_template(
        'privacy.html',
        title='Privacy Policy',
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact'
    )

@app.route('/error')
def error():
    """Renders the about page."""
    return render_template(
        'error.html',
        title='Error',
        message='An error occurred while processing your request'
    )

################################################################################

# region login

@app.route('/login', methods=["GET", "POST"])
def login():
    """Renders the login page."""
    return render_template(
        'login.html',
        form=form,
        title='Login',
    )

# endregion


# region proxy_views

@app.route('/proxy/details/<id>')
def proxy_details(id):
    """Renders the about page."""
    resp = requests.get(f'{API_ROOT}/proxies/{id}?embed=True')
    proxy=resp.json()

    return render_template(
        'proxy/details.html',
        title='Proxy Detail',
        proxy = proxy
    )

# endregion

################################################################################

# region provider_views

@app.route('/provider')
def provider_index():
    """Renders the provider list page."""
    resp = requests.get(f'{API_ROOT}/providers?embed=True')
    providers=resp.json()

    return render_template(
        'provider/index.html',
        title='Manage Providers',
        message='List of proxy list provider',
        providers=providers
    )


@app.route('/provider/details/<id>')
def provider_details(id):
    """Renders the provider detail page."""
    resp = requests.get(f'{API_ROOT}/providers/{id}?embed=True')
    provider=resp.json()

    return render_template(
        'provider/details.html',
        title='Provider Details',
        provider=provider
    )

# endregion

################################################################################

# region testurl_views

@app.route('/testurl')
def testurl_index():
    """Renders the testurl list page."""
    resp = requests.get(f'{API_ROOT}/testurls')
    testurls=resp.json()

    return render_template(
        'testurl/index.html',
        title='Manage Testurls',
        testurls=testurls
    )


@app.route('/testurl/details/<id>')
def testurl_details(id):
    """Renders the testurl detail page."""
    resp = requests.get(f'{API_ROOT}/testurls/{id}?embed=True')
    testurl=resp.json()

    return render_template(
        'testurl/details.html',
        title='Testurl Details',
        testurl = testurl
    )
# endregion

################################################################################

