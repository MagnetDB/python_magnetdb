from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Form
from uuid import uuid4 as uuid

from python_magnetdb.actions.security import generate_user_token, front_authorization_server, authorization_server, \
    authorization_host_server, client_id, client_secret
from python_magnetdb.models import User, AuditLog

router = APIRouter()


@router.post("/api/sessions/authorization_url")
def generate_authorization_url(redirect_uri: str = Form(...)):
    params = {
        "response_type": "code",
        "scope": "openid profile email",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    return {"url": f"{front_authorization_server}/oauth2/authorize?{urlencode(params)}"}


@router.post("/api/sessions")
def create(code: str = Form(...), redirect_uri: str = Form(...)):
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {}
    if authorization_host_server is not None:
        headers["Host"] = authorization_host_server
    token_req = requests.post(f"{authorization_server}/oauth2/token", data=payload, headers=headers, verify=False)
    token_data = token_req.json()

    headers["Authorization"] = f"{token_data['token_type']} {token_data['access_token']}"
    userinfo_req = requests.get(f"{authorization_server}/oauth2/userinfo", headers=headers, verify=False)
    userinfo_data = userinfo_req.json()

    try:
        user = User.objects.get(username=userinfo_data['sub'])
    except User.DoesNotExist:
        user = User(username=userinfo_data['sub'], api_key=str(uuid()).replace('-', ''))
    user.email = userinfo_data['email']
    user.name = userinfo_data['name']
    user.save()
    AuditLog.log(user, "User logged", resource=user)
    return {"token": generate_user_token(user)}

