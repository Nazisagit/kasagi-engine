from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.routes import documents
from app.db import create_db_and_tables
from app.ws import ChatConnectionManager

@asynccontextmanager
async def lifespan(_: FastAPI):
  create_db_and_tables()
  yield
  pass

app = FastAPI(lifespan=lifespan, title="Kasagi Engine")
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"]
)
app.include_router(documents.router, prefix="/documents")

chat_con_mgr = ChatConnectionManager()
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
async def health_check():
  return { "status": "ok" }

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
  return templates.TemplateResponse(
    request=request, name="index.html"
  )

@app.websocket("/ws/{client_id}")
async def chat_websocket(websocket: WebSocket, client_id: int):
  await chat_con_mgr.connect(websocket)
  try:
    while True:
      data = await websocket.receive_text()
      await chat_con_mgr.send_personal_message(f"You wrote: {data}", websocket)
      await chat_con_mgr.broadcast(f"Client #{client_id} says: {data}")
  except WebSocketDisconnect:
    chat_con_mgr.disconnect(websocket)
    await chat_con_mgr.broadcast(f"Client #{client_id} left the chat")
