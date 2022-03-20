from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Form

from ...models.audit_log import AuditLog
from ...models.user import User
from ...security import generate_user_token, authorization_server, client_id, client_secret

router = APIRouter()


@router.post("/api/sessions/authorization_url")
def generate_authorization_url(redirect_uri: str = Form(...)):
    params = {
        "response_type": "code",
        "scope": "openid profile email",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    return {"url": f"{authorization_server}/oauth2/authorize?{urlencode(params)}"}


@router.post("/api/sessions")
def create(code: str = Form(...), redirect_uri: str = Form(...)):
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    token_req = requests.post(f"{authorization_server}/oauth2/token", data=payload)
    token_data = token_req.json()

    userinfo_req = requests.get(f"{authorization_server}/oauth2/userinfo",
                                headers={"Authorization": f"{token_data['token_type']} {token_data['access_token']}"})
    userinfo_data = userinfo_req.json()

    user = User.where('username', userinfo_data['sub']).first()
    if not user:
        user = User(username=userinfo_data['sub'])
    user.email = userinfo_data['email']
    user.name = userinfo_data['name']
    user.save()
    AuditLog.log(user, "User logged", resource=user)
    return {"token": generate_user_token(user)}
