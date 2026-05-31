import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession

# Define generic types
# TypeVar creates a "placeholder" or a variable for a data type.
ModelType = TypeVar("ModelType", bound=SQLModel)
# CreateSchemaType is a blank slot for your Pydantic input forms.
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)



class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model  #It saves that table into self.model so it knows which database table to query.


   
    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ModelType]:  #promises to return the specific table we asked for.
        statement = select(self.model).where(self.model.id == id) #select(self.model): SELECT * FROM [table_name] WHERE id = [id].
        result = await db.execute(statement)
        return result.scalars().first()
    # SQLAlchemy returns data in a complex, multi-layered grid. scalars() flattens that grid, and first() grabs the single Python object you asked for.

    # This fetches multiple rows with built-in Pagination.
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

   
    
    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump()  #pydantic data->python dictionary
        db_obj = self.model(**obj_in_data) #his takes that dictionary and "unpacks" it into the 
        # database model, instantly matching fields like email to the email column.
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj) #grabs newly generated values(UUID, created_at) attaches them to your Python object before returning it.
        return db_obj


    
    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = db_obj.model_dump()
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # for PATCH request:exclude_unset=True tells Pydantic to ignore any fields that weren't included in the update request, preventing accidental overwrites with null values.
            
    
        for field in obj_data:   #This loop checks each field in the existing database object. If that field is present in the update data, it updates the database object with the new value.
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> ModelType:
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        db_obj = result.scalars().first()
        
        if db_obj:
        # SOFT DELETE: Change the flag to True instead of destroying the row
            if hasattr(db_obj, "is_deleted"):
                setattr(db_obj, "is_deleted", True)
                db.add(db_obj)
            else:
                # HARD DELETE (Fallback): Used for tables like IPCSections if they don't have the flag
                await db.delete(db_obj)
        return db_obj
    
