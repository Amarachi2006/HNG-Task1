# HNG-Task1
String Analyzer Service
A RESTful API service for analyzing strings and storing their properties.
Setup Instructions

Clone the repository:

git clone <your-repo-url>
cd <repo-name>


Create a virtual environment and install dependencies:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt


Run the application locally:

uvicorn main:app --host 0.0.0.0 --port 8000

Dependencies

FastAPI: Web framework
Uvicorn: ASGI server
Pydantic: Data validation
SQLite3: Database (included with Python)

Environment Variables
None required. The application uses SQLite (strings.db) for persistence.
Testing

Run the application
Use tools like Postman or curl to test endpoints
Example requests:

# Create string
curl -X POST http://localhost:8000/strings -H "Content-Type: application/json" -d '{"value": "hello world"}'

# Get string
curl http://localhost:8000/strings/hello%20world

# Get all strings with filters
curl "http://localhost:8000/strings?is_palindrome=true&min_length=5"

# Natural language filter
curl "http://localhost:8000/strings/filter-by-natural-language?query=single%20word%20palindromic%20strings"

# Delete string
curl -X DELETE http://localhost:8000/strings/hello%20world"

Deployment
Deployed on [Railway/Heroku/AWS/PXXL App] at: [Your API base URL]
