from sqlmodel import Field, SQLModel

class DocumentBase(SQLModel):
  title: str = Field(default="Untitled", index=True)
  content: str | None = Field(default=None)

class Document(DocumentBase, table=True):
  id: int | None = Field(default=None, primary_key=True)

class DocumentPublic(DocumentBase):
  id: int

class DocumentCreate(DocumentBase): pass

class DocumentUpdate(DocumentBase):
  title: str = Field(default="Untitled")
  content: str | None = None