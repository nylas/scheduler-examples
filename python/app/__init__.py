# Imports from the Python standard library
import os
import sys
import textwrap
import requests
from flask import Flask, session, request, render_template, redirect, url_for, flash
from flask_talisman import Talisman
from werkzeug.contrib.fixers import ProxyFix
from nylas import APIClient

# This example uses Flask, a micro web framework written in Python.
# For more information, check out the documentation: http://flask.pocoo.org
# Create a Flask app, and load the configuration file.
app = Flask(__name__)
app_settings = os.getenv("APP_SETTINGS", "app.config.DevelopmentConfig")
app.config.from_object(app_settings)

# force SSL, enable HTTP Strict Transport Security
csp = {"default-src": "'self' 'unsafe-inline' *.nylas.com maxcdn.bootstrapcdn.com" }
Talisman(app, content_security_policy=csp)

# Check for dummy configuration values.
# If you are building your own application based on this example,
# you can remove this check from your code.
cfg_needs_replacing = [
    key
    for key, value in app.config.items()
    if isinstance(value, str) and value.startswith("replace me")
]
if cfg_needs_replacing:
    message = textwrap.dedent(
        """
        This example will only work if you replace the fake configuration
        values in `config.json` with real configuration values.
        The following config values need to be replaced:
        {keys}
        Consult the README.md file in this directory for more information.
    """
    ).format(keys=", ".join(cfg_needs_replacing))
    print(message, file=sys.stderr)
    sys.exit(1)

# Teach Flask how to find out that it's behind an ngrok proxy
app.wsgi_app = ProxyFix(app.wsgi_app)

redirect_url = "https://nylas-customer-example.herokuapp.com/login_callback"
client = APIClient(app.config["NYLAS_OAUTH_CLIENT_ID"],
                   app.config["NYLAS_OAUTH_CLIENT_SECRET"])


# Define what Flask should do when someone visits the root URL of this website.
@app.route("/", methods=['GET'])
def index():
    # If the user has already connected to Nylas via OAuth,
    # `nylas.authorized` will be True. Otherwise, it will be False.
    if session.get('access_token') is not None:
        # If we've gotten to this point, then the user has already connected
        # to Nylas via OAuth. Let's set up the SDK client with the OAuth token:
        client.access_token = session['access_token']

        # We'll use the Nylas client to fetch information from Nylas
        # about the current user, and pass that to the template.
        try:
            account = client.account
        except requests.HTTPError:
            # The user's token may be invalid - log them out.
            return redirect("/logout")

        # Server-side scheduling page integration: fetch the list of pages that
        # include the current user's API token
        response = requests.get('https://schedule.api.nylas.com/manage/pages',
            headers=dict(Authorization="Bearer " + session['access_token']),
        )
        pages = response.json()
        return render_template("after_authorized.html", account=account, pages=pages)

    # OAuth requires HTTPS. The template will display a handy warning,
    # unless we've overridden the check.
    login_callback_var = client.authentication_url(redirect_url)

    return render_template(
        "before_authorized.html", login_callback_var=login_callback_var
    )

@app.route("/", methods=['POST'])
def index_create_page():
    if session.get('access_token') is None:
        return redirect(url_for('index'))

    json = {
        "name": request.form["name"],
        "slug": request.form["slug"],
        "config": {
            # You can provide as few or as many page configuration options as you like.
            # Check out the Scheduling Page documentation for a full list of settings.
            "event": {
                "title": request.form["event_title"],
            },
        },
        "api_tokens": [session['access_token']]
    }

    response = requests.post('https://schedule.api.nylas.com/manage/pages', json=json)
    if response.status_code != 201:
        flash(response.json()['error'])
    return redirect(url_for('index'))

@app.route("/login_callback")
def login_callback():
    if 'error' in request.args:
        return "Login error: {0}".format(request.args['error'])

    # Exchange the authorization code for an access token
    code = request.args.get('code')
    session['access_token'] = client.token_for_code(code)
    print(session['access_token'])
    return redirect("/")


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    del session['access_token']
    return redirect("/")

def ngrok_url():
    """
    If ngrok is running, it exposes an API on port 4040. We can use that
    to figure out what URL it has assigned, and suggest that to the user.
    https://ngrok.com/docs#list-tunnels
    """
    try:
        ngrok_resp = requests.get("http://localhost:4040/api/tunnels")
    except requests.ConnectionError:
        # I guess ngrok isn't running.
        return None
    ngrok_data = ngrok_resp.json()
    secure_urls = [
        tunnel["public_url"]
        for tunnel in ngrok_data["tunnels"]
        if tunnel["proto"] == "https"
    ]
    return secure_urls[0]


# When this file is executed, run the Flask web server.
if __name__ == "__main__":
    url = ngrok_url()
    if url:
        print(" * Visit {url} to view this Nylas example".format(url=url))

    app.run()
