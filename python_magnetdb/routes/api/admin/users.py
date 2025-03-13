from django.core.paginator import Paginator
from django.db.models import Q
from fastapi import Depends, APIRouter, Query, HTTPException, Form

from ..serializers import model_serializer
from ....dependencies import get_user
from ....models.user import User

router = APIRouter()


@router.get("/api/admin/users")
def index(
    user=Depends(get_user('admin')), page: int = 1, per_page: int = Query(default=25, lte=100),
    query: str = Query(None), sort_by: str = Query(None), sort_desc: bool = Query(False)
):
    db_query = User.objects
    if query is not None and query.strip() != '':
        db_query = db_query.filter(Q(name__icontains=query) | Q(email__icontains=query))
    if sort_by is not None:
        order_field = f"-{sort_by}" if sort_desc else sort_by
        db_query = db_query.order_by(order_field)
    paginator = Paginator(db_query.all(), per_page)
    return {
        "current_page": page,
        "last_page": paginator.num_pages,
        "total": paginator.count,
        "items": [model_serializer(item) for item in paginator.get_page(page).object_list],
    }


@router.get("/api/admin/users/{id}")
def show(id: int, user=Depends(get_user('admin'))):
    user = User.objects.filter(id=id).get()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return model_serializer(user)


@router.patch("/api/admin/users/{id}")
def update(id: int, user=Depends(get_user('admin')), name: str = Form(...), role: str = Form(...)):
    user = User.objects.filter(id=id).get()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = name
    user.role = role
    user.save()
    return model_serializer(user)
