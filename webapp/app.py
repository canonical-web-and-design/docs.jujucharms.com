# Core
from urllib.parse import urlparse, urlunparse, unquote

# Third-party
import flask
from canonicalwebteam.yaml_responses.flask_helpers import (
    prepare_deleted,
    prepare_redirects,
)
from canonicalwebteam.discourse_docs import DiscourseAPI, DiscourseDocs
from canonicalwebteam.discourse_docs.parsers import parse_index


app = flask.Flask(__name__)
app.template_folder = "../templates"
app.static_folder = "../static"
app.url_map.strict_slashes = False

discourse_index_id = 1087

discourse_api = DiscourseAPI(base_url="https://discourse.jujucharms.com/")
discourse_docs = DiscourseDocs(
    api=discourse_api,
    index_topic_id=discourse_index_id,
    category_id=22,
    document_template="document.html",
)
discourse_docs.init_app(app, url_prefix="/")

# Parse redirects.yaml and permanent-redirects.yaml
app.before_request(prepare_redirects())


def deleted_callback(context):
    index = parse_index(discourse_api.get_topic(discourse_index_id))

    return (
        flask.render_template(
            "410.html", navigation=index["navigation"], **context
        ),
        410,
    )


app.before_request(prepare_deleted(view_callback=deleted_callback))


@app.errorhandler(404)
def page_not_found(e):
    index = parse_index(discourse_api.get_topic(discourse_index_id))

    return (
        flask.render_template("404.html", navigation=index["navigation"]),
        404,
    )


@app.errorhandler(410)
def deleted(e):
    return deleted_callback({})


@app.errorhandler(500)
def server_error(e):
    return flask.render_template("500.html"), 500


@app.before_request
def clear_trailing():
    """
    Remove trailing slashes from all routes
    We like our URLs without slashes
    """

    parsed_url = urlparse(unquote(flask.request.url))
    path = parsed_url.path

    if path != "/" and path.endswith("/"):
        new_uri = urlunparse(parsed_url._replace(path=path[:-1]))

        return flask.redirect(new_uri)


# Remove homepage route so we can redefine it
for url in app.url_map._rules:
    if url.rule == '/':
        app.url_map._rules.remove(url)


@app.route("/")
def homepage():
    """
    Show the custom homepage
    """

    index = parse_index(discourse_api.get_topic(discourse_index_id))

    return flask.render_template(
        "homepage.html", navigation=index["navigation"]
    )


@app.route("/commands")
def commands():
    """
    Show the static commands page
    """

    index = parse_index(discourse_api.get_topic(discourse_index_id))

    return flask.render_template(
        "commands.html", navigation=index["navigation"]
    )
