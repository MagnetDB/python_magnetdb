from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...actions.compute_bmap_2d_chart import prepare_bmap_2d_chart_params, compute_bmap_2d_chart
from ...actions.compute_bmap_chart import compute_bmap_chart, prepare_bmap_chart_params
from ...actions.compute_stress_map_chart import (
    prepare_stress_map_chart_params,
    compute_stress_map_chart,
)
from ...actions.object_geometries import get_magnet_data, get_site_data
from ...dependencies import get_user

router = APIRouter()


class BMapPayload(BaseModel):
    resource_type: str
    resource_id: int
    i_h: float = None
    i_b: float = None
    i_s: float = None
    n: int = None
    r0: float = None
    z0: float = None
    r: List[float] = None
    z: List[float] = None
    pkey: str = None
    command: str = None


@router.post("/api/visualisations/bmap")
def bmap(payload: BMapPayload, user=Depends(get_user("read"))):
    if payload.resource_type == "magnet":
        data = get_magnet_data(payload.resource_id)
    elif payload.resource_type == "site":
        data = get_site_data(payload.resource_id)
    else:
        raise HTTPException(status_code=400, detail="The resource type supplied is invalid")

    (i_h, i_b, i_s, n, r0, z0, r, z, pkey, command, allowed_currents) = prepare_bmap_chart_params(
        data,
        payload.i_h,
        payload.i_b,
        payload.i_s,
        payload.n,
        payload.r0,
        payload.z0,
        payload.r,
        payload.z,
        payload.pkey,
        payload.command,
    )
    return {
        "params": {
            "i_h": i_h,
            "i_b": i_b,
            "i_s": i_s,
            "n": n,
            "r0": r0,
            "z0": z0,
            "r": r,
            "z": z,
            "pkey": pkey,
            "command": command,
        },
        "allowed_currents": allowed_currents,
        "results": compute_bmap_chart(data, i_h, i_b, i_s, n, r0, z0, r, z, pkey, command),
    }


class StressMapPayload(BaseModel):
    resource_type: str
    resource_id: int
    i_h: float = None
    i_b: float = None
    i_s: float = None
    magnet_type: str = None


@router.post("/api/visualisations/stress_map")
def stress_map(payload: StressMapPayload, user=Depends(get_user("create"))):
    if payload.resource_type == "magnet":
        data = get_magnet_data(payload.resource_id)
    elif payload.resource_type == "site":
        data = get_site_data(payload.resource_id)
    else:
        raise HTTPException(status_code=400, detail="The resource type supplied is invalid")

    (i_h, i_b, i_s, allowed_currents, magnet_type) = prepare_stress_map_chart_params(
        data, payload.i_h, payload.i_b, payload.i_s, payload.magnet_type
    )
    return {
        "params": {
            "i_h": i_h,
            "i_b": i_b,
            "i_s": i_s,
            "magnet_type": magnet_type,
        },
        "allowed_currents": allowed_currents,
        "results": compute_stress_map_chart(data, i_h, i_b, i_s, magnet_type),
    }


class BMap2DPayload(BaseModel):
    resource_type: str
    resource_id: int
    i_h: float = None
    i_b: float = None
    i_s: float = None
    nr: int = None
    r0: float = None
    r1: float = None
    nz: int = None
    z0: float = None
    z1: float = None
    pkey: str = None


@router.post("/api/visualisations/bmap_2d")
def bmap_2d(payload: BMap2DPayload, user=Depends(get_user("create"))):
    if payload.resource_type == "magnet":
        data = get_magnet_data(payload.resource_id)
    elif payload.resource_type == "site":
        data = get_site_data(payload.resource_id)
    else:
        raise HTTPException(status_code=400, detail="The resource type supplied is invalid")

    (i_h, i_b, i_s, nr, r0, r1, nz, z0, z1, pkey, allowed_currents) = prepare_bmap_2d_chart_params(
        data,
        payload.i_h,
        payload.i_b,
        payload.i_s,
        payload.nr,
        payload.r0,
        payload.r1,
        payload.nz,
        payload.z0,
        payload.z1,
        payload.pkey,
    )
    return {
        "params": {
            "i_h": i_h,
            "i_b": i_b,
            "i_s": i_s,
            "nr": nr,
            "r": [r0, r1],
            "nz": nz,
            "z": [z0, z1],
            "pkey": pkey,
        },
        "allowed_currents": allowed_currents,
        "results": compute_bmap_2d_chart(data, i_h, i_b, i_s, nr, r0, r1, nz, z0, z1, pkey),
    }
