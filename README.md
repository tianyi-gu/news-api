## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download required models:
   ```bash
   python scripts/download_models.py
   ```



# notes to myself during the development
(RAG + openai)
openai
flax
torch
tensorflow

llama 2(7B)
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip install transformers accelerate

pip install python-dotenv
pip install farm-haystack
pip install openai
pip install fastapi

# uvicorn is an ASGI server required to run your FastAPI application.

pip install uvicorn

front end
expo init frontExpo
cd frontExpo
npm install axios

npm install @react-navigation/native
npm install @react-navigation/stack
expo install react-native-screens react-native-safe-area-context react-native-gesture-handler react-native-reanimated react-native-vector-icons

production plan:

1. Document Store Limitations:

# Current setup (temporary/testing)

document_store = InMemoryDocumentStore(use_bm25=True)

# Production alternatives:

# 1. Elasticsearch

from haystack.document_stores import ElasticsearchDocumentStore
document_store = ElasticsearchDocumentStore(
host="your_elasticsearch_host",
port=9200,
username="elastic",
password="your_password",
index="news_articles"
)

# 2. Or FAISS for vector search

from haystack.document_stores import FAISSDocumentStore
document_store = FAISSDocumentStore(
faiss_index_path="news_faiss",
faiss_config_path="news_faiss_config"
)

2. Deployment Options:
   Cloud Platforms:
   AWS (Amazon Web Services)
   Google Cloud Platform
   Azure
   Server Options:
   Docker containers for easy deployment
   Kubernetes for scaling
   Load balancing for handling multiple requests
   Example Docker Setup:

3. Example Docker Setup:
   FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

4. Database Considerations:
   PostgreSQL for structured data
   Elasticsearch for full-text search
   Redis for caching
   MongoDB for document storage
5. Architecture Changes Needed:

# Configuration management

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
elasticsearch_host: str
elasticsearch_port: int
elasticsearch_user: str
elasticsearch_password: str
model_path: str

    class Config:
        env_file = ".env"

settings = Settings()

# Document store initialization

document_store = ElasticsearchDocumentStore(
host=settings.elasticsearch_host,
port=settings.elasticsearch_port,
username=settings.elasticsearch_user,
password=settings.elasticsearch_password
)

# Model handling

model_storage = CloudStorage() # AWS S3 or similar

6. Scaling Considerations:
   Multiple server instances
   Load balancing
   Caching layer
   API rate limiting
   Error handling and logging
   Monitoring and analytics
   Here's a basic production-ready structure:

project/
├── app/
│ ├── api/
│ │ ├── **init**.py
│ │ ├── endpoints.py
│ │ └── models.py
│ ├── core/
│ │ ├── **init**.py
│ │ ├── config.py
│ │ └── security.py
│ ├── services/
│ │ ├── **init**.py
│ │ ├── document_store.py
│ │ └── qa_pipeline.py
│ └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

For your news application, I would recommend:

1. Start with Elasticsearch for document storage (good for text search)
2. Deploy on AWS or similar cloud platform
3. Use Docker for containerization
4. Implement proper monitoring and logging
5. Set up automated backups
6. Consider implementing a caching layer
7. Add authentication and rate limiting

First, install Elasticsearch locally for testing:
# For Windows, download and install from:

# https://www.elastic.co/downloads/elasticsearch

# For Mac with Homebrew:

brew install elasticsearch

# For Linux:

curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update
sudo apt install elasticsearch



elasticsearch costs $100/month. let's try MongoDB.
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create a free cluster
3. Create a user and password: mi40T4YJ45prI0l3
4. Create a connection string: mongodb+srv://tianyievans:mi40T4YJ45prI0l3@phillipian.ggmbs.mongodb.net/?retryWrites=true&w=majority&appName=Phillipian
5. Install the MongoDB driver for Python
6. Connect to the MongoDB cluster
7. Store the documents in the MongoDB collection
8. Use the MongoDB document store in your Haystack pipeline

1. In Security menu, click "Database Access"
2. Add New Database User
   - Authentication Method: Password
   - Username: your_username
   - Password: your_secure_password
   - Built-in Role: "Read and write to any database"
3. Click "Add User"
1. In Security menu, click "Network Access"
2. Click "Add IP Address"
3. For development, you can click "Allow Access from Anywhere" (0.0.0.0/0)
   (Note: For production, you'll want to restrict this)
4. Click "Confirm"
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy the connection string
   It looks like: 
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

Get your connection string:
Update your project:
First, install the required packages:
pip install pymongo dnspython haystack-ai
