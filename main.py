import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS strings (
            id TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            length INTEGER,
            is_palindrome BOOLEAN,
            unique_characters INTEGER,
            word_count INTEGER,
            sha256_hash TEXT,
            char_freq TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class StringInput(BaseModel):
    value: str

class StringResponse(BaseModel):
    id: str
    value: str
    properties: dict
    created_at: str

class StringsListResponse(BaseModel):
    data: List[StringResponse]
    count: int
    filters_applied: dict

class NaturalLanguageResponse(BaseModel):
    data: List[StringResponse]
    count: int
    interpreted_query: dict

# Helper functions
def calculate_properties(text: str) -> Dict:
    # Length
    length = len(text)
    
    # Is palindrome (case-insensitive)
    is_palindrome = text.lower() == text.lower()[::-1]
    
    # Unique characters
    unique_characters = len(set(text))
    
    # Word count
    words = text.split()
    word_count = len(words)
    
    # SHA-256 hash
    sha256_hash = hashlib.sha256(text.encode()).hexdigest()
    
    # Character frequency map
    char_freq = {}
    for char in text:
        char_freq[char] = char_freq.get(char, 0) + 1
    
    return {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha256_hash,
        "character_frequency_map": char_freq
    }

def parse_natural_language(query: str) -> Dict:
    query = query.lower().strip()
    filters = {}
    
    # Handle single word palindromic strings
    if "single word palindromic" in query:
        filters["word_count"] = 1
        filters["is_palindrome"] = True
    
    # Handle length requirements
    length_match = re.search(r'longer than (\d+)', query)
    if length_match:
        filters["min_length"] = int(length_match.group(1)) + 1
    
    # Handle palindrome requirement
    if "palindromic" in query and "single word palindromic" not in query:
        filters["is_palindrome"] = True
    
    # Handle contains character
    char_match = re.search(r'contains the letter (\w)', query)
    if char_match:
        filters["contains_character"] = char_match.group(1)
    elif "first vowel" in query:
        filters["contains_character"] = "a"
    
    return filters

# Endpoints
@app.post("/strings", response_model=StringResponse, status_code=201)
async def create_string(data: StringInput):
    if not isinstance(data.value, str):
        raise HTTPException(status_code=422, detail="Value must be a string")
    
    if not data.value:
        raise HTTPException(status_code=400, detail="Value field is required")
    
    properties = calculate_properties(data.value)
    id = properties["sha256_hash"]
    
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    
    # Check if string exists
    c.execute("SELECT id FROM strings WHERE id = ?", (id,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="String already exists")
    
    # Store in database
    created_at = datetime.utcnow().isoformat() + "Z"
    c.execute('''
        INSERT INTO strings (id, value, length, is_palindrome, unique_characters, word_count, sha256_hash, char_freq, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        id,
        data.value,
        properties["length"],
        properties["is_palindrome"],
        properties["unique_characters"],
        properties["word_count"],
        properties["sha256_hash"],
        str(properties["character_frequency_map"]),
        created_at
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "id": id,
        "value": data.value,
        "properties": properties,
        "created_at": created_at
    }

@app.get("/strings/{string_value}", response_model=StringResponse)
async def get_string(string_value: str):
    hash_value = hashlib.sha256(string_value.encode()).hexdigest()
    
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    c.execute("SELECT * FROM strings WHERE id = ?", (hash_value,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="String not found")
    
    return {
        "id": result[0],
        "value": result[1],
        "properties": {
            "length": result[2],
            "is_palindrome": bool(result[3]),
            "unique_characters": result[4],
            "word_count": result[5],
            "sha256_hash": result[6],
            "character_frequency_map": eval(result[7])
        },
        "created_at": result[8]
    }

@app.get("/strings", response_model=StringsListResponse)
async def get_all_strings(
    is_palindrome: Optional[bool] = Query(None),
    min_length: Optional[int] = Query(None, ge=0),
    max_length: Optional[int] = Query(None, ge=0),
    word_count: Optional[int] = Query(None, ge=0),
    contains_character: Optional[str] = Query(None, min_length=1, max_length=1)
):
    query = "SELECT * FROM strings WHERE 1=1"
    params = []
    
    filters_applied = {}
    
    if is_palindrome is not None:
        query += " AND is_palindrome = ?"
        params.append(is_palindrome)
        filters_applied["is_palindrome"] = is_palindrome
    
    if min_length is not None:
        query += " AND length >= ?"
        params.append(min_length)
        filters_applied["min_length"] = min_length
    
    if max_length is not None:
        query += " AND length <= ?"
        params.append(max_length)
        filters_applied["max_length"] = max_length
    
    if word_count is not None:
        query += " AND word_count = ?"
        params.append(word_count)
        filters_applied["word_count"] = word_count
    
    if contains_character is not None:
        query += " AND value LIKE ?"
        params.append(f"%{contains_character}%")
        filters_applied["contains_character"] = contains_character
    
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    
    data = [
        {
            "id": row[0],
            "value": row[1],
            "properties": {
                "length": row[2],
                "is_palindrome": bool(row[3]),
                "unique_characters": row[4],
                "word_count": row[5],
                "sha256_hash": row[6],
                "character_frequency_map": eval(row[7])
            },
            "created_at": row[8]
        } for row in results
    ]
    
    return {
        "data": data,
        "count": len(data),
        "filters_applied": filters_applied
    }

@app.get("/strings/filter-by-natural-language", response_model=NaturalLanguageResponse)
async def natural_language_filter(query: str = Query(...)):
    try:
        filters = parse_natural_language(query)
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to parse natural language query")
    
    # Validate filters
    if not filters:
        raise HTTPException(status_code=422, detail="Query resulted in no valid filters")
    
    query_str = "SELECT * FROM strings WHERE 1=1"
    params = []
    
    if "is_palindrome" in filters:
        query_str += " AND is_palindrome = ?"
        params.append(filters["is_palindrome"])
    
    if "min_length" in filters:
        query_str += " AND length >= ?"
        params.append(filters["min_length"])
    
    if "word_count" in filters:
        query_str += " AND word_count = ?"
        params.append(filters["word_count"])
    
    if "contains_character" in filters:
        query_str += " AND value LIKE ?"
        params.append(f"%{filters['contains_character']}%")
    
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    c.execute(query_str, params)
    results = c.fetchall()
    conn.close()
    
    data = [
        {
            "id": row[0],
            "value": row[1],
            "properties": {
                "length": row[2],
                "is_palindrome": bool(row[3]),
                "unique_characters": row[4],
                "word_count": row[5],
                "sha256_hash": row[6],
                "character_frequency_map": eval(row[7])
            },
            "created_at": row[8]
        } for row in results
    ]
    
    return {
        "data": data,
        "count": len(data),
        "interpreted_query": {
            "original": query,
            "parsed_filters": filters
        }
    }

@app.delete("/strings/{string_value}", status_code=204)
async def delete_string(string_value: str):
    hash_value = hashlib.sha256(string_value.encode()).hexdigest()
    
    conn = sqlite3.connect('strings.db')
    c = conn.cursor()
    c.execute("SELECT id FROM strings WHERE id = ?", (hash_value,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="String not found")
    
    c.execute("DELETE FROM strings WHERE id = ?", (hash_value,))
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=204, content={})

if __name__ = "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)