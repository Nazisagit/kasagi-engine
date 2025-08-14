from typing import Annotated

from fastapi import APIRouter, Request, Query, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlmodel import select

import json

from app.models.document import *
from app.db import SessionDep
from app.ws import DocumentConnectionManager

router = APIRouter(tags=["Documents"])
doc_con_mgr = DocumentConnectionManager()
templates = Jinja2Templates(directory="app/templates")

@router.get("/",response_class=HTMLResponse)
def get_documents(
  request: Request,
  session: SessionDep,
  offset: int = 0,
  limit: Annotated[int, Query(le=100)] = 100
):
  documents = session.exec(select(Document).offset(offset).limit(limit)).all()
  return templates.TemplateResponse(
    request=request, name="documents/index.html", context={"documents": documents}
  )

@router.post("/", response_model=DocumentPublic, response_class=RedirectResponse)
def create_document(request: Request, session: SessionDep, title: str = "Untitled", content: str = ""):
  db_document = Document.model_validate(DocumentCreate(title=title, content=content))
  session.add(db_document)
  session.commit()
  session.refresh(db_document)
  return RedirectResponse(request.url_for('get_document', document_id=db_document.id), status_code=status.HTTP_302_FOUND)

@router.patch("/{document_id}", response_model=DocumentPublic)
async def update_document(document_id: int, document: DocumentUpdate, session: SessionDep):
  db_document = session.get(Document, document_id)
  if not db_document:
    raise HTTPException(status_code=404, detail="Document not found")
  document_data = document.model_dump(exclude_unset=True)
  db_document.sqlmodel_update(document_data)
  session.add(db_document)
  session.commit()
  session.refresh(db_document)
  return db_document

@router.get("/{document_id}", response_model=DocumentPublic, response_class=HTMLResponse)
def get_document(request: Request, document_id: int, session: SessionDep):
  db_document = session.get(Document, document_id)
  if not db_document:
    raise HTTPException(status_code=404, detail="Document not found")
  return templates.TemplateResponse(
    request=request, name="documents/show.html", context={"db_document": db_document}
  )

@router.delete("/{document_id}")
def delete_document(document_id: int, session: SessionDep):
  document = session.get(Document, document_id)
  if not document:
    raise HTTPException(status_code=404, detail="Document not found")
  session.delete(document)
  session.commit()
  return { "ok": True }

@router.websocket("/ws/{document_id}")
async def document_websocket(websocket: WebSocket, document_id: int):
  await doc_con_mgr.connect(websocket, document_id)
  try:
    while True:
      data = await websocket.receive_json()
      await doc_con_mgr.broadcast_to_document(json.dumps(data), document_id)
  except WebSocketDisconnect:
    doc_con_mgr.disconnect(websocket, document_id)
