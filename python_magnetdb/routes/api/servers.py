from django.core.paginator import Paginator
from django.db.models import Q
from fastapi import Depends, APIRouter, HTTPException, Query, Form

from .serializers import model_serializer
from ...actions.generate_server_key_pairs import generate_server_key_pairs
from ...dependencies import get_user
from ...models import Server, AuditLog

router = APIRouter()


@router.get("/api/servers")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query('created_at'), sort_desc: bool = Query(False)):
    db_query = Server.objects.filter(user_id=user.id)
    if query is not None and query.strip() != '':
        db_query = db_query.filter(Q(name__icontains=query))
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


@router.post("/api/servers")
def create(name: str = Form(...), host: str = Form(...), username: str = Form(...),
           image_directory: str = Form(...), type: str = Form(None), smp: bool = Form(None),
           multithreading: bool = Form(None), cores: int = Form(None),
           job_manager: str = Form(None), mesh_gems_directory: str = Form(None),
           user=Depends(get_user('create'))):
    private_key, public_key = generate_server_key_pairs()
    server = Server(
        name=name,
        host=host,
        username=username,
        image_directory=image_directory,
        private_key=private_key,
        public_key=public_key,
        user=user
    )
    if type is not None:
        server.type = type
    if smp is not None:
        server.smp = smp
    if multithreading is not None:
        server.multithreading = multithreading
    if cores is not None:
        server.cores = cores
    if job_manager is not None:
        server.job_manager = job_manager
    if mesh_gems_directory is not None:
        server.mesh_gems_directory = mesh_gems_directory
    server.save()
    AuditLog.log(user, "Server created", resource=server)
    return model_serializer(server)


@router.get("/api/servers/{id}")
def show(id: int, user=Depends(get_user('read'))):
    server = Server.objects.filter(user_id=user.id).get(id=id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return model_serializer(server)


@router.patch("/api/servers/{id}")
def update(id: int, name: str = Form(...), host: str = Form(...), username: str = Form(...),
           image_directory: str = Form(...), type: str = Form(...), smp: bool = Form(...),
           multithreading: bool = Form(...), cores: int = Form(...),
           job_manager: str = Form(...), mesh_gems_directory: str = Form(...), user=Depends(get_user('update'))):
    server = Server.objects.filter(user_id=user.id).get(id=id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.name = name
    server.host = host
    server.username = username
    server.image_directory = image_directory
    server.type = type
    server.smp = smp
    server.multithreading = multithreading
    server.cores = cores
    server.job_manager = job_manager
    server.mesh_gems_directory = mesh_gems_directory
    server.save()
    AuditLog.log(user, "Server updated", resource=server)
    return model_serializer(server)


@router.delete("/api/servers/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    server = Server.objects.filter(user_id=user.id).get(id=id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server.delete()
    AuditLog.log(user, "Server deleted", resource=server)
    return model_serializer(server)
