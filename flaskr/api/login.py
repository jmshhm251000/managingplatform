import os
import requests
import logging
from flask import redirect, request, url_for, render_template, session, Blueprint,  current_app
from urllib.parse import urlencode


logger = logging.getLogger(__name__)
client_id = os.getenv("CLIENT_ID")
redirect_uri = os.getenv("REDIRECT_URI")


ig_login_api = Blueprint("ig_login", __name__, url_prefix='/login')

@ig_login_api.route('/instagram')
def instagram_login():
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "pages_show_list,business_management,instagram_basic,instagram_manage_insights",
        "auth_type": "rerequest"
    }
    auth_url = f"https://www.facebook.com/v22.0/dialog/oauth?{urlencode(params)}"
    logger.debug("Redirecting to Instagram OAuth endpoint: %s", auth_url)
    return redirect(auth_url)


@ig_login_api.route('/instagram/callback')
def instagram_callback():
    code = request.args.get('code')
    if not code:
        logger.warning("Instagram callback called without code parameter")
        return "Authorization failed.", 400

    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        'client_id': os.getenv("CLIENT_ID"),
        'client_secret': os.getenv("CLIENT_SECRET"),
        'redirect_uri': redirect_uri,
        'code': code
    }
    logger.debug("Exchanging code for token at %s with params: %s", token_url, params)
    response = requests.get(token_url, params=params)
    token_data = response.json()
    logger.debug("Token response payload: %s", token_data)

    access_token = token_data.get('access_token')
    if access_token:
        session['access_token'] = access_token
        logger.info("Stored access token in session; redirecting to dashboard")
        return redirect(url_for('ig_login.dashboard'))
    else:
        error_msg = token_data.get('error', token_data)
        logger.error("Failed to retrieve access token: %s", error_msg)
        return f"Failed to retrieve access token. Details: {token_data}", 400


@ig_login_api.route('/dashboard')
def dashboard():
    access_token = session.get('access_token')
    if not access_token:
        logger.warning("No access_token in session; redirecting to gate")
        return redirect(url_for('gate'))

    # Fetch Facebook Pages
    pages_url = "https://graph.facebook.com/v18.0/me/accounts"
    pages_params = {
        'fields': 'id,name,instagram_business_account{id}',
        'access_token': access_token
    }
    logger.debug("Requesting user pages with params: %s", pages_params)
    pages_response = requests.get(pages_url, params=pages_params).json()
    logger.debug("Pages response payload: %s", pages_response)

    data = pages_response.get('data', [])
    if not data:
        logger.error("No linked Facebook pages found in response: %s", pages_response)
        return "No linked Facebook pages found.", 400

    # Find IG Business Account ID
    ig_account_id = None
    for page in data:
        ig_edge = page.get('instagram_business_account')
        if ig_edge and 'id' in ig_edge:
            ig_account_id = ig_edge['id']
            logger.info("Found Instagram Business Account ID %s for page %s",
                        ig_account_id, page.get('id'))
            break

    if not ig_account_id:
        logger.error("No Instagram Business account linked on any page: %s", data)
        return "No linked Instagram Business account found.", 400

    # Fetch Insights
    insights_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/insights"
    insights_params = {
        'metric': 'accounts_engaged,reach,profile_views',
        'period': 'day',
        'metric_type': 'total_value',
        'access_token': access_token
    }
    logger.debug("Requesting insights at %s with params: %s", insights_url, insights_params)
    insights_response = requests.get(insights_url, params=insights_params).json()
    logger.debug("Insights response payload: %s", insights_response)

    # Render
    logger.info("Rendering dashboard for IG account %s", ig_account_id)
    return render_template(
        'dashboard.html',
        ig_account_id=ig_account_id,
        insights_response=insights_response
    )