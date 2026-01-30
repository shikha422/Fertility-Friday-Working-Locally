import os
import vecs
from groq import Groq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# --- CONFIGURATION ---
GROQ_API_KEY = "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"
DB_CONNECTION = "postgresql://postgres.tmfypdknuwrnsaoojxqo:YZ^vYmXo4eJ16&rR@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

print("--- Initializing Shared Resources ---")

# 1. Initialize Groq Client
groq_client = Groq(api_key=GROQ_API_KEY)
print("Groq Client Initialized")

# 2. Initialize Embedding Model (HEAVY OPERATION - Run Once)
print("Loading SentenceTransformer Model... (This may take a moment)")
import time
from huggingface_hub import snapshot_download

def download_model_with_retry(model_name, retries=3, delay=5):
    for i in range(retries):
        try:
            print(f"Attempting to download model (Attempt {i+1}/{retries})...")
            # Download model first to cache
            snapshot_download(repo_id=model_name)
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            if i < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Could not download model.")
                raise e

model_name = 'sentence-transformers/all-MiniLM-L6-v2'
download_model_with_retry(model_name)
model = SentenceTransformer(model_name)
print("Model Loaded")

# 3. Initialize Database
vx = vecs.create_client(DB_CONNECTION)
docs = vx.get_or_create_collection(name="episode_vectors", dimension=384)
print("Database Connection Established")

print("--- Shared Resources Ready ---")


