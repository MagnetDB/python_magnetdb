from typing import Optional

from datetime import datetime

import pandas as pd
from django.core.paginator import Paginator
from django.db.models import Q
from pydantic import BaseModel
from fastapi import APIRouter, Query, HTTPException, Form, UploadFile, File, Depends

from .serializers import model_serializer
from ...dependencies import get_user
from ...models import Record, Site, StorageAttachment, AuditLog
from ...utils.record_visualization import columns as columns_with_name

router = APIRouter()


@router.get("/api/records")
def index(user=Depends(get_user('read')), page: int = 1, per_page: int = Query(default=25, lte=100),
          query: str = Query(None), sort_by: str = Query('created_at'), sort_desc: bool = Query(False)):
    db_query = Record.objects
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


@router.post("/api/records")
def create(user=Depends(get_user('create')), name: str = Form(...), description: str = Form(None),
           site_id: str = Form(...), attachment: UploadFile = File(...)):
    site = Site.objects.get(id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    record = Record(name=name, description=description)
    record.attachment = StorageAttachment.upload(attachment)
    record.site = site
    record.save()
    AuditLog.log(user, f"Record created {attachment.filename}", resource=record)
    return model_serializer(record)


class RecordPayload(BaseModel):
    name: str
    description: Optional[str]
    site_id: int
    attachment_id: int


@router.post("/api/clirecords")
def clicreate(payload: RecordPayload, user=Depends(get_user('create'))):
    print(f'record/clicreate: name={payload.name}, attachment_id={payload.attachment_id}')
    site = Site.objects.get(id=payload.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    print(f'site: {site}')

    attachment = StorageAttachment.objects.get(id=payload.attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    print(f'attachment: {attachment}')

    record = Record(name=payload.name, description=payload.description)
    record.attachment = attachment
    print(f'record/clicreate: associate attachment done')
    record.site = site
    print(f'record/clicreate: associate site done')
    record.save()
    AuditLog.log(user, f"Record cli created {payload.name}", resource=record)
    return model_serializer(record)

@router.get("/api/records/{id}")
def show(id: int, user=Depends(get_user('read'))):
    record = Record.objects.prefetch_related('attachment', 'site').get(id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    return model_serializer(record)


@router.get("/api/records/{id}/visualize")
def visualize(id: int, user=Depends(get_user('read')),
              x: str = Query(None), y: str = Query(None), auto_sampling: bool = Query(False),
              x_min: float = Query(None), x_max: float = Query(None),
              y_min: float = Query(None), y_max: float = Query(None)):
    record = Record.objects.prefetch_related('attachment').get(id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # data prep
    time_format = "%Y.%m.%d %H:%M:%S"
    data = pd.read_csv(record.attachment.download(), sep=r'\s+', skiprows=1)
    # cleanup: remove empty columns
    data = data.loc[:, (data != 0.0).any(axis=0)]
    t0 = datetime.strptime(data['Date'].iloc[0] + " " + data['Time'].iloc[0], time_format)
    data["t"] = data.apply(
        lambda row: (datetime.strptime(row.Date + " " + row.Time, time_format) - t0).total_seconds(),
        axis=1
    )
    data["timestamp"] = data.apply(lambda row: datetime.strptime(row.Date + " " + row.Time, time_format), axis=1)

    result = {}
    sampling_enabled = False
    if x is not None and y is not None:
        y = y.split(',')

        # to handle chart resizing
        if x_min is not None and x_max is not None and y_min is not None and y_max is not None:
            data = data[(data[x] >= x_min) & (data[x] <= x_max)]
            for y_value in y:
                data = data[(data[y_value] >= y_min) & (data[y_value] <= y_max)]

        # compute if sampling is required
        sampling_enabled = auto_sampling is True and len(data) > 500
        sampling_factor = round(data['timestamp'].count() / 500) if sampling_enabled else 1

        # rendering values and applying sampling factor is needed
        for (index, values) in enumerate(data[[x] + y].values):
            if index % sampling_factor == 0:
                result[values[0]] = values[1:].tolist()

    columns = {}
    for column in data.columns.tolist():
        columns[column] = columns_with_name[column]

    return {'result': result, 'columns': columns, 'sampling_enabled': sampling_enabled}


@router.patch("/api/records/{id}")
def update(id: int, user=Depends(get_user('update')), name: str = Form(...), description: str = Form(None),
           site_id: str = Form(...)):
    record = Record.objects.get(id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    site = Site.objects.get(id=site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    record.name = name
    record.description = description
    record.site = site
    record.save()
    AuditLog.log(user, "Record updated", resource=record)
    return model_serializer(record)


@router.delete("/api/records/{id}")
def destroy(id: int, user=Depends(get_user('delete'))):
    record = Record.objects.get(id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record.delete()
    AuditLog.log(user, "Record deleted", resource=record)
    return model_serializer(record)
