# from fastapi import FastAPI, Depends
# from fastapi.middleware.cors import CORSMiddleware


import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from typing import Union

app = FastAPI()

class Category(Enum):
    TOOLS = "tools"
    CONSUMABLES = "consumables"

class Item(BaseModel):
    name: str
    price: float
    count : int
    id: int
    category: Category


items = {
         0: Item(name="test", price=1.0, count=1, id=1, category=Category.TOOLS),
         1: Item(name="test2", price=2.0, count=2, id=2, category=Category.CONSUMABLES),
         2: Item(name="test3", price=3.0, count=3, id=3, category=Category.TOOLS)
         }

@app.get("/")
def index() -> dict[str, dict[int, Item]]:
    return {"items": items}


@app.get("/items/{item_id}")
def query_item_by_id(item_id: int) -> Item:
    if item_id not in items:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return items[item_id]

Selection = dict[str, Union[str, float, int, Category, None]]


@app.get("/items/")
def query_item_by_parameters(
    name: str = None, 
    price: float = None,
    category: Category = None,
    count: int = None,
    ) -> dict[str, Selection]:
    def check_item(item: Item) -> bool:
        return all(
            (
                name is None or item.name == name,
                price is None or item.price == price,
                category is None or item.category == category,
                count is None or item.count == count,
            )
        )
        
    selection = [item for item in items.values() if check_item(item)]

    return {"query": {"name": name, "price": price, "category": category, "count": count}, "selection": selection}