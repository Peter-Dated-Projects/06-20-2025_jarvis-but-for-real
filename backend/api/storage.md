

# /storage/status

**Method:** `GET`  
**Description:**  
Check that the MongoDB server is reachable and responding to commands.

**Response:**  
- **200 OK**  
  ```json
  { "status": "ok" }
  ```
- **500 Internal Server Error**  
  ```json
  {
    "status": "error",
    "message": "<error message>"
  }
  ```


---

# /storage/upload

**Method:** `POST`  
**Description:**  
Insert one or more JSON documents into the named collection. If the collection does not exist it will be created.

**Request Body (JSON):**  
```json
{
  "collection": "myCollection",
  "object": {                  
    "first_name": "Alice",
    "last_name": "Smith",
    "age": 29
  }
}
```

- **collection** `(string, required)`  
  The name of the MongoDB collection to write to.  
- **object** `(object or array, required)`  
  A single JSON document or an array of documents to insert.

**Response:**  
- **200 OK**  
  ```json
  { "status": "ok" }
  ```
- **400 Bad Request**  
  ```json
  {
    "status": "error",
    "message": "No data provided"            
  }
  ```
- **500 Internal Server Error**  
  ```json
  {
    "status": "error",
    "message": "Failed to insert object"
  }
  ```


---

# /storage/delete

**Method:** `DELETE`  
**Description:**  
Delete either entire collections or individual documents matching a filter.

**Request Body (JSON):**  
- **To drop a whole collection**  
  ```json
  {
    "type": "collection",
    "collection": "myCollection"
  }
  ```
- **To delete matching documents**  
  ```json
  {
    "type": "object",
    "collection": "myCollection",
    "filter": {
      "age": { "$lt": 18 }
    }
  }
  ```

- **type** `(string, required)`  
  - `"collection"`: drop the named collection (removes all documents & indexes).  
  - `"object"`: delete only documents matching the filter.  
- **collection** `(string, required)`  
  The name of the collection to operate on.  
- **filter** `(object, required when type="object")`  
  A MongoDB query object. All documents matching this filter will be removed. Use `{}` to delete all documents but keep the collection.

**Response:**  
- **200 OK**  
  - For `"collection"`:  
    ```json
    { "status": "ok" }
    ```
  - For `"object"`:  
    ```json
    {
      "status": "ok",
      "message": "Deleted <n> objects"
    }
    ```
- **400 Bad Request**  
  ```json
  {
    "status": "error",
    "message": "No target type provided"
  }
  ```
- **500 Internal Server Error**  
  ```json
  {
    "status": "error",
    "message": "<error message>"
  }
  ```


---

# /storage/get_objects

**Method:** `GET`  
**Description:**  
Retrieve documents from the named collection that match the provided filter.

**Request Body (JSON):**  
```json
{
  "collection": "myCollection",
  "filter": {
    // MongoDB query object
  }
}
```

- **collection** `(string, required)`  
  The name of the collection to query.  
- **filter** `(object, required)`  
  A MongoDB query object specifying which documents to retrieve.

**Response:**  
- **200 OK**  
  ```json
  {
    "status": "ok",
    "object": [
      {
        // Retrieved document fields...
      }
    ]
  }
  ```
- **400 Bad Request**  
  ```json
  {
    "status": "error",
    "message": "No data provided"
  }
  ```  
  or  
  ```json
  {
    "status": "error",
    "message": "No collection name provided"
  }
  ```  
  or  
  ```json
  {
    "status": "error",
    "message": "No filter criteria provided"
  }
  ```
- **500 Internal Server Error**  
  ```json
  {
    "status": "error",
    "message": "<error message>"
  }
  ```