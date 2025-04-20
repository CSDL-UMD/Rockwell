from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Any
import logging

from app.core.config import settings
from app.db.session import get_store

from requests_oauthlib import OAuth1Session


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/login", response_class=HTMLResponse)
async def twitter_login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth1 login to twitter, to get access token for future requests
    """
    
    try:
        request_token = OAuth1Session(client_key=settings.TWITTER_API_KEY,client_secret=settings.TWITTER_API_SECRET_KEY)
        content = request_token.post(settings.TWITTER_REQUEST_TOKEN_URL, data = {"oauth_callback": settings.TWITTER_CALLBACK_URL})
        logging.info('Twitter access successfull')
    except Exception as error:
        print('Twitter access failed with error : '+str(error))
        logging.error('Twitter access failed with error : '+str(error))

    data_tokens = content.text.split("&")
    oauth_store = get_store("oauth_store")

    oauth_token = data_tokens[0].split("=")[1]
    oauth_token_secret = data_tokens[1].split("=")[1]
    oauth_store[oauth_token] = oauth_token_secret
    start_url = settings.TWITTER_AUTHORIZE_URL +"?oauth_token="+oauth_token
    return templates.TemplateResponse("YouGov.html", {"request": request, "start_url": start_url, "screenname": "###", "rockwell_url": "###"})
