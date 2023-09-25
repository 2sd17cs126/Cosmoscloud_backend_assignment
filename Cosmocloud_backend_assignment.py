from fastapi import FastAPI, HTTPException, Query, Path, Body,Response
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List
from fastapi.responses import JSONResponse 
from datetime import datetime
from bson import ObjectId 
import json 

app = FastAPI()

# Initialize the MongoDB client

#connecting to MongoDb client using connection string as parameter to MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client["System_info"]
#collection for orders
orders_collection = db["orders"]
#collection for Products
products_collection=db["Products"]




# defining Models of what structure it has and its typeof its elemrnt and later it will be used to validate for request and response data
class Product(BaseModel):
    name: str
    price: float
    available_quantity: int

class Item(BaseModel):
    product_id: str
    bought_quantity: int
    total_amount: float

class UserAddress(BaseModel):
    city: str
    country: str
    zip_code: str

class Order(BaseModel):
    timestamp: str
    items: List[Item]
    user_address: UserAddress


#Defining the Api endpoints 


#APi with end point http://localhost:8000/products/ and its a post request for creating Products in the system
@app.post("/products/", response_model=Product)
def create_product(product: Product):
    product_data = {
        "name": product.name,
        "price": product.price,
        "available_quantity": product.available_quantity
    }
    
    # Insert the product into the products collection
    product_id = products_collection.insert_one(product_data).inserted_id
    
    # Get the inserted product document
    inserted_product = products_collection.find_one({"_id": ObjectId(product_id)})
    #checking if the Product has not been inserted and raising HttpException with status code 500
    if not inserted_product:
        raise HTTPException(status_code=500, detail="Failed to create product")
    
    # Convert ObjectId to string in the response
    inserted_product["_id"] = str(inserted_product["_id"])
    #Return the Response once the API call is successful with status code of 200
    return Response(content=json.dumps(inserted_product), status_code=200, media_type="application/json")

#API with end point http://localhost:8000/orders/{order_id} to look for a particular order in the system with order_id
@app.get("/orders/{order_id}", response_model=Order)
def fetch_order_by_id(order_id: str = Path(..., title="The Order ID")):
    #making query to the orders_collection with _id and checking if there orders with _id equals to orders_id
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    #if no order found then return Order not found
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Convert the MongoDB document to a Pydantic model
    order["_id"] = str(order["_id"])  # Convert ObjectId to string
    #returning the fetched order with _id equals order_id
    return Response(content=json.dumps(order), status_code=200, media_type="application/json")


#API with endpoint http://localhost:8000/orders/ and its get request to get all orders from the system
@app.get("/orders/", response_model=List[Order])
def fetch_orders_with_pagination(limit: int = Query(10, ge=1), offset: int = Query(0, ge=0)):
    #fetching the orders data with offset
    orders = list(orders_collection.find().skip(offset).limit(limit))
    
    # Convert ObjectId to string for each order
    formatted_orders = []
    for order in orders:
        formatted_order = order.copy()
        formatted_order["_id"] = str(order["_id"])
        formatted_orders.append(formatted_order)
    #returning the fetched orders 
    return Response(content=json.dumps(formatted_orders), status_code=200, media_type="application/json")


#API with end point http://localhost:8000/orders/ and its post request to create new order into the system
@app.post("/orders/", response_model=Order)
def create_order(order:Order):
    
    # Extract and reformat items for readability
    items_data = []
    print(order)
    for item in order.items:
        item_data = {
            "productId": item.product_id,
            "boughtQuantity": item.bought_quantity,
            "Total amount": item.total_amount
        }
        items_data.append(item_data)
    
    order_data = {
        "timestamp": str(datetime.now()),
        "items": items_data,
        "user_address": order.user_address.dict()
    }
    #inserting the order into orders_collection
    order_id = orders_collection.insert_one(order_data).inserted_id
    
    order_data["_id"] = str(order_id)  # Convert ObjectId to string
    #Returning the response 
    return Response(content=json.dumps(order_data), status_code=201, media_type="application/json")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
