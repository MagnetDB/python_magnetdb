import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'python_magnetdb.settings')

import django
django.setup()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.api.attachments import router as api_attachments_router
from .routes.api.simulations import router as api_simulations_router
from .routes.api.magnet_parts import router as api_magnet_parts_router
from .routes.api.magnets import router as api_magnets_router
from .routes.api.materials import router as api_materials_router
from .routes.api.parts import router as api_parts_router
from .routes.api.sessions import router as api_sessions_router
from .routes.api.site_magnets import router as api_site_magnets_router
from .routes.api.sites import router as api_sites_router
from .routes.api.records import router as api_records_router
from .routes.api.servers import router as api_servers_router
from .routes.api.user import router as api_user_router
from .routes.api.visualisations import router as api_visualisations_router
from .routes.api.cad_attachments import router as api_cad_attachments
from .routes.api.mesh_attachments import router as api_mesh_attachments
from .routes.api.admin.config import router as api_admin_config_router
from .routes.api.admin.audit_logs import router as api_admin_audit_logs_router
from .routes.api.admin.users import router as api_admin_users_router
from .routes.api.home import router as api_home_router

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(api_materials_router)
app.include_router(api_simulations_router)
app.include_router(api_parts_router)
app.include_router(api_magnets_router)
app.include_router(api_sites_router)
app.include_router(api_attachments_router)
app.include_router(api_magnet_parts_router)
app.include_router(api_site_magnets_router)
app.include_router(api_sessions_router)
app.include_router(api_records_router)
app.include_router(api_servers_router)
app.include_router(api_cad_attachments)
app.include_router(api_mesh_attachments)
app.include_router(api_user_router)
app.include_router(api_visualisations_router)
app.include_router(api_admin_config_router)
app.include_router(api_admin_audit_logs_router)
app.include_router(api_admin_users_router)
app.include_router(api_home_router)
