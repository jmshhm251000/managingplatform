# ManagingPlatform

## Overview

ManagingPlatform is a Flask-based web application integrating Instagram APIs with a chatbot powered by Large Language Models (LLMs) using the `llama_index` and `Ollama` framework. The app supports secure user login, message history analytics, and knowledge base management with NLP features.

---

## Features

- User authentication with OAuth integration  
- Access and display Instagram insights and messaging analytics  
- MongoDB backend for storing chat history and user data  
- Chatbot implementation with LLM-powered retrieval-augmented generation (RAG)  
- API routes modularized under `/api` namespace  
- Docker support for containerized deployment  

---

## TODO

- Refactor `db.py` and `webhooks.py` to use **MongoDB Atlas (cloud)** instead of local MongoDB
  - Update database connection strings to MongoDB Atlas URI
  - Configure authentication and connection pooling for Atlas
  - Test database operations with cloud DB

- Modularize API routes following the **single-responsibility principle**
  - Break down APIs so each endpoint has one clear purpose, for example:
    - Authentication/login API
    - Instagram insights API
    - Message handling/webhooks API
    - Chatbot query API
    - Knowledge base management API
  - Organize routes using Flask Blueprints or similar modular structures

- Improve **error handling and logging** in all API modules
  - Add detailed error messages for MongoDB Atlas connection issues
  - Log webhook requests and responses with identifiers for tracing
  - Implement retry logic on transient database failures

- Enhance **security** for cloud deployment
  - Secure environment variables and database credentials
  - Add rate limiting and authentication on critical endpoints if missing
  - Validate and sanitize all user inputs

- Update **documentation**
  - Reflect MongoDB Atlas changes and new API structure in README and code comments
  - Document required environment variables explicitly
  - Provide example usage for each new API endpoint

---

## Prerequisites

- Python 3.9 or later  
- MongoDB instance (local or cloud)  
- Access to Google and Meta APIs with appropriate credentials  
- Docker (optional, for container deployment)  

---

## Setup

1. Clone the repository

```bash
git clone <repo_url>
cd managingplatform-main
```

2. install dependencies

pip install -r requirements.txt

3. Create .env and Configure environment variables

MONGO_URI=,
ACCESS_KEY=,
DOCUMENT_ID=,
SCOPES=,
VERIFY_TOKEN =,
and etc.

4. Run the flask app

On CommandLine:
```zsh
python main.py
python3 main.py
```

With Docker:
```zsh
docker-compose up --build
```