from fastapi import Request, HTTPException

from .models.user import User
from python_magnetdb.actions.security import parse_user_token


def is_authorize(user: User, action: str) -> bool:
    if user.role == 'guest':
        return action in ['read']
    elif user.role == 'user':
        return action in ['read', 'update', 'delete']
    elif user.role == 'designer':
        return action in ['create', 'read', 'update', 'delete']
    elif user.role == 'admin':
        return action in ['create', 'read', 'update', 'delete', 'admin']
    return False


def get_user(action=False):
    def handler(request: Request) -> User:
        authorization = request.query_params.get('auth_token') or request.headers.get('authorization')
        if authorization is None:
            raise HTTPException(detail="Forbidden.", status_code=403)
        token = parse_user_token(authorization)
        user = User.objects.filter(id=token['user_id']).get() if token else User.objects.filter(api_key=authorization).get()
        if not (user is not None and (action is False or is_authorize(user, action))):
            raise HTTPException(detail="Forbidden.", status_code=403)
        return user

    return handler


def get_db():
    return None
