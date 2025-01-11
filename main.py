from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List, Optional


# Database configuration
MONGO_URL = "mongodb+srv://user:obm4iuIHW4B6WOtG@cluster0.m6nax.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_URL)
db = client.my_library
coll = db.books
print("Connected to MongoDB:", db.name)


app = FastAPI()


# Base models
class Book(BaseModel):
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    genre: List[str] = Field(..., description="Genre should be the list of strings")
    rating: int = Field(default=1, ge=1, le=5, description="The rating. Could be from 1 to 5")
    pages: int = Field(..., ge=0, description="Pages must be a positive number")
    status: str = Field(..., pattern="^(available|borrowed)$", description="Status must be 'available' or 'borrowed'")

class UpdateBookStatus(BaseModel):
    status: str = Field(..., pattern="^(available|borrowed)$", description="Status must be 'available' or 'borrowed'")



# To return JSON friendly object
def format_object_id(doc):
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def main_page():
    return {"message" : "This is main page"}


# Get All Books: GET /books/
@app.get("/books/", response_description="Get all books", response_model=List[Book])
async def get_all_books():
    books = []
    async for book in coll.find():
        books.append(format_object_id(book))
    if books:
        return books
    else:
        return {'Message':'The database is empty'}


# Add a New Book: POST /books/
@app.post("/books/", response_description="Add new books", response_model=Book)
async def add_new_book(book: Book):
    book_data = jsonable_encoder(book)
    result = await coll.insert_one(book_data)
    created_book = await coll.find_one({"_id": result.inserted_id})
    return JSONResponse(status_code=201, content=format_object_id(created_book))



# Get Book by ID: GET /books/{book_id}
@app.get("/books/{book_id}", response_description="Getting book by ID", response_model=Book)
async def getting_book_by_id(book_id : str):
    try:
        obj_id = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    book = await coll.find_one({"_id": obj_id})
    if book is not None:
        return format_object_id(book)
    raise HTTPException(status_code=404, detail="Book not found")



# Update Book Status: PUT /books/{book_id}
@app.put("/books/{book_id}", response_description="Updatig the status of the book", response_model=Book)
async def updating_book(book_id : str, updated_book: UpdateBookStatus):
    try:
        obj_id = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    result = await coll.update_one({"_id": obj_id}, {"$set": updated_book.dict()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_document = await coll.find_one({"_id": obj_id})
    return format_object_id(updated_document)



# Delete a Book: DELETE /books/{book_id}
@app.delete("/books/{book_id}", response_description="Deleting book by id")
async def delete_book_by_id(book_id : str):
    try:
        obj_id = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")
    result = await coll.delete_one({"_id": obj_id})
    if result.deleted_count == 1:
        return {"message": "Book successfully deleted"}
    raise HTTPException(status_code=404, detail="Book not found")