import os
from urllib.parse import quote_plus
import os
import vecs
from backend_shared import model, docs

# --- CONFIGURATION (Managed in backend_shared) ---

def upload_to_supabase(base_directory):
    records = []

    for root, _, files in os.walk(base_directory):
        for file in files:
            if not file.endswith(".txt"):
                continue

            file_path = os.path.join(root, file)
            ep_id = os.path.basename(root)
            section = file.replace(".txt", "")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            vector = model.encode(content).tolist()

            records.append((
                f"{ep_id}_{section}",
                vector,
                {
                    "episode_id": ep_id,
                    "section": section,
                    "preview": content
                }
            ))

    docs.upsert(records)
    print(f"Stored {len(records)} vectors in Supabase")


# Run the upload only if executed directly
if __name__ == "__main__":
    upload_to_supabase('./chunked_all')