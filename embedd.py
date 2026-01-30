import os
from sentence_transformers import SentenceTransformer
from backend_shared import model

# 1. Load the model (This will download it on the first run)
# 'all-MiniLM-L6-v2' is great for general purpose text

def create_embeddings_from_files(base_directory):
    processed_data = []

    # 2. Walk through the episode folders we created
    for root, dirs, files in os.walk(base_directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 3. Create the embedding
                # This turns your text into a vector (e.g., [0.12, -0.05, 0.88...])
                embedding = model.encode(content)

                # Store the metadata alongside the vector
                processed_data.append({
                    "filename": file,
                    "episode_id": os.path.basename(root),
                    "vector": embedding.tolist(), # Convert numpy array to list for JSON/DB
                    "text_chunk": content
                })
                
    print(f"Successfully created {len(processed_data)} embeddings.")
    print(embedding)
    return processed_data

# Run the process

all_embeddings = create_embeddings_from_files('./chunked_all')