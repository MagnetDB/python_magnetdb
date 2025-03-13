from os import getenv

from fastapi import Depends, APIRouter

from ....dependencies import get_user
from python_magnetdb.actions.security import authorization_server, client_id, client_secret

router = APIRouter()


@router.get("/api/admin/config")
def show(user=Depends(get_user('admin'))):
    return {
        'SECURITY_AUTHORIZATION_SERVER': authorization_server,
        'SECURITY_CLIENT_ID': client_id,
        'SECURITY_CLIENT_SECRET': client_secret,
        'S3_ENDPOINT': getenv('S3_ENDPOINT'),
        'S3_ACCESS_KEY': getenv('S3_ACCESS_KEY'),
        'S3_SECRET_KEY': getenv('S3_SECRET_KEY'),
    }
