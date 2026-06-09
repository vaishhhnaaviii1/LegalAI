

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession

# Define generic types to strictly enforce that we only pass valid models and schemas
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        # Stores the specific table so the class knows what to query
        self.model = model 

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        # THE SCALAR EXPLANATION:
        # Databases return data as raw "rows" (which act like tuples/grids). 
        # scalars() just strips away that tuple wrapping, leaving you with the pure Python object.
        # first() grabs the object, or returns None if the UUID doesn't exist.
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        # all() extracts all the objects and we wrap it in list() for strict type hinting
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        # SIMPLIFICATION: SQLModel has 'model_validate'.
        # This one line instantly converts your Pydantic schema into a database object.
        # You no longer need to manually dump to a dictionary and unpack it.
        db_obj = self.model.model_validate(obj_in) 
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj) # Grabs newly generated DB values (like timestamps/IDs)
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        # 1. Format the incoming data
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        
        # SIMPLIFICATION: SQLModel has 'sqlmodel_update'.
        # This completely replaces your manual "for field in obj_data:" loop. 
        # It cleanly applies the dictionary to the database object.
        db_obj.sqlmodel_update(update_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: uuid.UUID) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        db_obj = result.scalars().first()
        
        if db_obj:
            # SOFT DELETE
            if hasattr(db_obj, "is_deleted"):
                db_obj.is_deleted = True  # Standard Python property assignment
                db.add(db_obj)
            # HARD DELETE
            else:
                await db.delete(db_obj)
                
            # CRITICAL: You must commit the transaction for the delete to save!
            await db.commit() 
            
        return db_obj