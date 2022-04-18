from fastapi import APIRouter, HTTPException, Depends, Form, Query

from ...actions.generate_simulation_config import generate_simulation_config
from ...actions.run_simulation import run_simulation
from ...actions.run_simulation_setup import run_simulation_setup
from ...dependencies import get_user
from ...models.audit_log import AuditLog
from ...models.magnet import Magnet
from ...models.simulation import Simulation
from ...models.site import Site

router = APIRouter()


@router.get("/api/simulations")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          sort_by: str = Query(None), sort_desc: bool = Query(False)):
    simulations = Simulation.with_('resource')
    if sort_by is not None:
        simulations = simulations.order_by(sort_by, 'desc' if sort_desc else 'asc')
    simulations = simulations.paginate(per_page, page)
    return {
        "current_page": simulations.current_page,
        "last_page": simulations.last_page,
        "total": simulations.total,
        "items": simulations.serialize(),
    }


@router.post("/api/simulations")
def create(resource_type: str = Form(...), resource_id: int = Form(...), method: str = Form(...),
           model: str = Form(...), geometry: str = Form(...), cooling: str = Form(...),
           static: bool = Form(...), non_linear: bool = Form(...), user=Depends(get_user('create'))):
    if resource_type == 'magnet':
        resource = Magnet.find(resource_id)
    elif resource_type == 'site':
        resource = Site.find(resource_id)

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    simulation = Simulation(method=method, model=model, geometry=geometry, cooling=cooling,
                            static=static, non_linear=non_linear)
    simulation.resource().associate(resource)
    simulation.save()
    AuditLog.log(user, "Simulation created", resource=simulation)
    return simulation.serialize()


@router.get("/api/simulations/{id}/config.json")
def config(id: int, user=Depends(get_user('read'))):
    simulation = Simulation.find(id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return generate_simulation_config(simulation)


@router.post("/api/simulations/{id}/run_setup")
def run_setup(id: int, user=Depends(get_user('update'))):
    simulation = Simulation.with_('resource').find(id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    AuditLog.log(user, "Simulation setup started", resource=simulation)
    run_simulation_setup(simulation)
    return simulation.serialize()


@router.post("/api/simulations/{id}/run")
def run(id: int, user=Depends(get_user('update'))):
    simulation = Simulation.with_('resource').find(id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    AuditLog.log(user, "Simulation started", resource=simulation)
    run_simulation(simulation)
    return simulation.serialize()
