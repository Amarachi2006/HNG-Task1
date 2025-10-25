# String Analyzer Service

A RESTful API service for analyzing strings and storing their properties. This service is intended as a demonstration of a simple FastAPI application.

## Features

*   **String Analysis**: Get detailed properties of a string, including length, palindrome status, unique characters, word count, and character frequency.
*   **Filtering**: Filter strings based on their properties, such as palindrome status, length, and word count.
*   **Natural Language Filtering**: Use natural language queries to filter strings.
*   **Persistence**: Strings and their properties are stored in a SQLite database (`strings.db`), which is created automatically.

## Getting Started

### Prerequisites

*   Python 3.7+
*   pip

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <repo-name>
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Run the application locally:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

## API Endpoints

The base URL for all endpoints is `http://localhost:8000`.

### Create a String

*   `POST /strings`

Creates a new string. The `id` of the string is its SHA256 hash.

**Request Body:**

```json
{
  "value": "hello world"
}
```

**Example Request:**

```bash
curl -X POST http://localhost:8000/strings \
-H "Content-Type: application/json" \
-d '{"value": "hello world"}'
```

**Example Response (`201 Created`):**

```json
{
  "id": "b94d27...",
  "value": "hello world",
  "properties": {
    "length": 11,
    "is_palindrome": false,
    "unique_characters": 7,
    "word_count": 2,
    "sha256_hash": "b94d27...",
    "character_frequency_map": {"h":1,"e":1,"l":3,"o":2," ":1,"w":1,"r":1,"d":1}
  },
  "created_at": "2024-07-28T12:34:56.789Z"
}
```

### Get a String

*   `GET /strings/{string_value}`

Retrieves a specific string by its value.

**Example Request:**

```bash
curl http://localhost:8000/strings/hello%20world
```

**Example Response (`200 OK`):**

```json
{
  "id": "b94d27...",
  "value": "hello world",
  "properties": {
    "length": 11,
    "is_palindrome": false,
    "unique_characters": 7,
    "word_count": 2,
    "sha256_hash": "b94d27...",
    "character_frequency_map": {"h":1,"e":1,"l":3,"o":2," ":1,"w":1,"r":1,"d":1}
  },
  "created_at": "2024-07-28T12:34:56.789Z"
}
```

### Get All Strings

*   `GET /strings`

Retrieves a list of strings, with optional filters.

**Query Parameters:**

*   `is_palindrome` (boolean): Filter by palindrome status.
*   `min_length` (integer): Filter by minimum length.
*   `max_length` (integer): Filter by maximum length.
*   `word_count` (integer): Filter by word count.
*   `contains_character` (string): Filter strings containing a specific character.

**Example Request:**

```bash
curl "http://localhost:8000/strings?is_palindrome=true&min_length=5"
```

**Example Response (`200 OK`):**

```json
{
  "data": [
    {
      "id": "d82494f05d6917ba02f7aaa29689ccb444bb73f20380876ac02819ca58581585",
      "value": "racecar",
      "properties": { ... },
      "created_at": "..."
    }
  ],
  "count": 1,
  "filters_applied": {
    "is_palindrome": true,
    "min_length": 5
  }
}
```

### Natural Language Filtering

*   `GET /strings/filter-by-natural-language`

Filters strings using a natural language query.

**Query Parameters:**

*   `query` (string): The natural language query.

**Example Request:**

```bash
curl "http://localhost:8000/strings/filter-by-natural-language?query=single%20word%20palindromic%20strings"
```

**Example Response (`200 OK`):**

```json
{
  "data": [
    {
      "id": "38d3cde42c4b8101031a123681427a17723933939618a3359876d28991d7fb89",
      "value": "level",
      "properties": { ... },
      "created_at": "..."
    }
  ],
  "count": 1,
  "interpreted_query": {
    "original": "single word palindromic strings",
    "parsed_filters": {
      "word_count": 1,
      "is_palindrome": true
    }
  }
}
```

### Delete a String

*   `DELETE /strings/{string_value}`

Deletes a string from the database.

**Example Request:**

```bash
curl -X DELETE http://localhost:8000/strings/hello%20world
```

**Example Response:**

A successful deletion returns a `204 No Content` status code.
