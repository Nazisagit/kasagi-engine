from fastapi import WebSocket

class DocumentConnectionManager:
  def __init__(self):
      self.document_connections: dict[int, list[WebSocket]] = {}

  async def connect(self, websocket: WebSocket, document_id: int):
      await websocket.accept()
      if document_id not in self.document_connections:
          self.document_connections[document_id] = []
      self.document_connections[document_id].append(websocket)

  def disconnect(self, websocket: WebSocket, document_id: int):
      self.document_connections[document_id].remove(websocket)
      if not self.document_connections[document_id]:
          del self.document_connections[document_id]

  async def send_personal_message(self, message: str, websocket: WebSocket):
    await websocket.send_text(message)

  async def broadcast_to_document(self, message: str, document_id: int):
      if document_id in self.document_connections:
          for connection in self.document_connections[document_id]:
              await connection.send_text(message)

class ChatConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
