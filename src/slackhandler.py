import json
import logging
import os
import jwt
import itertools
from threading import Thread

from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
from slack_sdk.oauth import OpenIDConnectAuthorizeUrlGenerator, RedirectUriPageRenderer
from slack_sdk.oauth.state_store import FileOAuthStateStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class slackHandler(object):

    def __init__(self, arg):
        # Insights class object in arg
        self.arg = arg
        self.create_app(arg)
    
    # :hiddes:
    def create_app(self, arg):
        from flask import Flask, request, make_response, Response

        client_id = os.environ["SLACK_CLIENT_ID"]
        client_secret = os.environ["SLACK_CLIENT_SECRET"]
        signing_secret = os.environ["SLACK_SIGNING_SECRET"]
        redirect_uri = os.environ["SLACK_REDIRECT_URI"]
        slack_token = os.environ["SLACK_BOT_TOKEN"]

        scopes = ["openid", "email", "profile"]
        self.arg = arg

        state_store = FileOAuthStateStore(expiration_seconds=300)

        authorization_url_generator = OpenIDConnectAuthorizeUrlGenerator(
            client_id=client_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
        )
        redirect_page_renderer = RedirectUriPageRenderer(
            install_path="/slack/install",
            redirect_uri_path="/slack/oauth_redirect",
        )

        #instantiating slack client
        slack_client = WebClient(slack_token)

        app = Flask(__name__)
        app.debug = True

        # I know inception ugglyness, refactor to use Factory pattern maybe
        @app.route("/slack/install", methods=["GET"])
        def oauth_start():
            state = state_store.issue()
            url = authorization_url_generator.generate(state=state)
            return (
                '<html><head><link rel="icon" href="data:,"></head><body>'
                f'<a href="{url}">'
                f'<img alt=""Add to Slack"" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>'
                "</body></html>"
            )

        # OAUTH Flask impl python-slack-sdk
        @app.route("/slack/oauth_redirect", methods=["GET"])
        def oauth_callback():
            # Retrieve the auth code and state from the request params
            if "code" in request.args:
                state = request.args["state"]
                if state_store.consume(state):
                    code = request.args["code"]
                    try:
                        token_response = WebClient().openid_connect_token(
                            client_id=client_id, client_secret=client_secret, code=code
                        )
                        logger.info(f"openid.connect.token response: {token_response}")
                        id_token = token_response.get("id_token")
                        claims = jwt.decode(
                            id_token, options={"verify_signature": False}, algorithms=["RS256"]
                        )
                        logger.info(f"claims (decoded id_token): {claims}")

                        user_token = token_response.get("access_token")
                        user_info_response = WebClient(
                            token=user_token
                        ).openid_connect_userInfo()
                        logger.info(f"openid.connect.userInfo response: {user_info_response}")
                        return f"""
                    <html>
                    <head>
                    <style>
                    body h2 {{
                    padding: 10px 15px;
                    font-family: verdana;
                    text-align: center;
                    }}
                    </style>
                    </head>
                    <body>
                    <h2>OpenID Connect Claims</h2>
                    <pre>{json.dumps(claims, indent=2)}</pre>
                    <h2>openid.connect.userInfo response</h2>
                    <pre>{json.dumps(user_info_response.data, indent=2)}</pre>
                    </body>
                    </html>
                    """

                    except Exception:
                        logger.exception("Failed to perform openid.connect.token API call")
                        return redirect_page_renderer.render_failure_page(
                            "Failed to perform openid.connect.token API call"
                        )
                else:
                    return redirect_page_renderer.render_failure_page(
                        "The state value is already expired"
                    )

            error = request.args["error"] if "error" in request.args else ""
            return make_response(
                f"Something is wrong with the installation (error: {error})", 400
            )

        @app.route("/")
        def event_hook(request):
            json_dict = json.loads(request.body.decode("utf-8"))
            if json_dict["token"] != VERIFICATION_TOKEN:
                return {"status": 403}

            if "type" in json_dict:
                if json_dict["type"] == "url_verification":
                    response_dict = {"challenge": json_dict["challenge"]}
                    return response_dict
            return {"status": 500}
            return


        slack_events_adapter = SlackEventAdapter(
            signing_secret, "/slack/events", app
        )  

        @slack_events_adapter.on("app_mention")
        def handle_message(event_data):
            logger.info(f"APP_MENTION")
            def send_reply(value):
                event_data = value
                message = event_data["event"]
                if message.get("subtype") is None:
                    command = message.get("text")
                    channel_id = message["channel"]
                    if command.split()[1] == 'azure':
                        function = command.split()[2]
                        function_args = command.split()[2:]
                        message = (
                            f":robot_face: running Azure Insight function {function} with args{function_args}:"
                        )
                    
                        slack_client.chat_postMessage(channel=channel_id, text=message)
                        if function == 'subscriptions':
                            message = (
                            f"{self.arg.getRoleAssignments()}"
                            )
                            slack_client.chat_postMessage(channel=channel_id, text=message)

            thread = Thread(target=send_reply, kwargs={"value": event_data})
            thread.start()
            return Response(status=200)

        @slack_events_adapter.on("file_shared")
        def handle_message(event_data):
            logger.info(f"FILE_SHARED {event_data}")
            def send_reply(value):
                event_data = value
                message = event_data["event"]
                if message.get("subtype") is None:
                    command = message.get("text")
                    channel_id = message["channel_id"]
                    slack_client.chat_postMessage(channel=channel_id, text="asadas")
            thread = Thread(target=send_reply, kwargs={"value": event_data})
            thread.start()
            return Response(status=200)


        app.run("localhost", 5000)


    
