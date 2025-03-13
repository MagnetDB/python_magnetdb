from django.core.paginator import Paginator
from django.db.models import Q
from fastapi import Depends, APIRouter, Query

from ..serializers import model_serializer
from ....dependencies import get_user
from ....models.audit_log import AuditLog

router = APIRouter()


@router.get("/api/admin/audit_logs")
def index(user=Depends(get_user('admin')), page: int = 1, per_page: int = Query(default=25, lte=100),
         query: str = Query(None), sort_by: str = Query(None), sort_desc: bool = Query(False)):
    db_query = AuditLog.objects.select_related('user')
    if query is not None and query.strip() != '':
        db_query = db_query.filter(Q(message__icontains=query) | Q(message__icontains=query))
    if sort_by is not None:
        order_field = f"-{sort_by}" if sort_desc else sort_by
        db_query = db_query.order_by(order_field)
    paginator = Paginator(db_query.all(), per_page)
    items = [model_serializer(site) for site in paginator.get_page(page).object_list]
    return {
        "current_page": page,
        "last_page": paginator.num_pages,
        "total": paginator.count,
        "items": items,
    }
