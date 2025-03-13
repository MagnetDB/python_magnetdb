import jwt

from datetime import datetime
from os import getenv

authorization_server = getenv('SECURITY_AUTHORIZATION_SERVER') or "http://sso.lncmig.local"
front_authorization_server = getenv('FRONT_SECURITY_AUTHORIZATION_SERVER') or authorization_server
authorization_host_server = getenv('FRONT_SECURITY_AUTHORIZATION_HOST_SERVER')
client_id = getenv('SECURITY_CLIENT_ID') or "testid"
client_secret = getenv('SECURITY_CLIENT_SECRET') or "testsecret"
secret = getenv("SECRET") or "defaultsecretpleasechangeme"


def generate_user_token(user):
    return jwt.encode({"user_id": user.id, "created_at": datetime.now().utctimetuple()}, secret, algorithm="HS256")


def parse_user_token(token):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:
        return None
