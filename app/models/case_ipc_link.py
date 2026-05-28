from sqlmodel import SQLModel, Field


 #class CaseIPCLink(SQLModel, table=True):
#     __tablename__ = "case_ipc_link"

#     case_id: int = Field(
#         foreign_key="cases.id",
#         primary_key=True
#     )

#     ipc_id: int = Field(
#         foreign_key="ipc_sections.id",
#         primary_key=True
#     )