import json
import logging
import time
import re
from backend_shared import vx, docs, groq_client, model

# --- 1. SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("summary_debug.log"), logging.StreamHandler()]
)

def generate_super_summaries():
    try:
        super_docs = vx.get_or_create_collection(name="super_short_summaries", dimension=384)
        logging.info("Connected to Supabase 'super_short_summaries' collection.")
    except Exception as e:
        logging.error(f"Failed to connect to Supabase: {e}")
        return

    # 2. FETCH ALL METADATA TO SEE WHAT WE HAVE
    logging.info("Fetching a broad sample of chunks to identify labels...")
    # Fetch 1000 chunks without any filter
    raw_results = docs.query(data=[0.1] * 384, limit=1000, include_metadata=True)
    
    if not raw_results:
        logging.error("The 'docs' collection is empty! Run your embedder first.")
        return

    # 3. DYNAMIC FILTERING (Finds 'overview' or 'topics' regardless of case or underscores)
    episodes_dict = {}
    found_labels = set()

    for res in raw_results:
        meta = res[1]
        # We check both 'section' and 'Section' just in case
        section_val = str(meta.get('section', meta.get('Section', ''))).lower()
        found_labels.add(meta.get('section', meta.get('Section', 'Unknown')))
        
        # If the label contains 'overview' or 'topic'
        if 'overview' in section_val or 'topic' in section_val:
            eid = meta.get('episode_id', 'Unknown')
            preview = meta.get('preview', '')
            
            if eid not in episodes_dict:
                episodes_dict[eid] = []
            if preview not in episodes_dict[eid]:
                episodes_dict[eid].append(preview)

    if not episodes_dict:
        logging.warning(f"No overview/topic sections found. Available labels in DB: {found_labels}")
        return

    # 4. SORTING AND BATCHING
    def get_num(text):
        match = re.search(r'\d+', str(text))
        return int(match.group()) if match else 0

    sorted_ids = sorted(episodes_dict.keys(), key=get_num)
    logging.info(f"Successfully grouped {len(sorted_ids)} unique episodes using labels: {found_labels}")

    batch_size = 10
    for i in range(0, len(sorted_ids), batch_size):
        batch_ids = sorted_ids[i : i + batch_size]
        combined_text = ""
        for eid in batch_ids:
            combined_text += f"\n--- {eid} ---\n" + "\n".join(episodes_dict[eid]) + "\n"

        logging.info(f"--- Processing Batch: {batch_ids[0]} to {batch_ids[-1]} ---")
        
        try:
            response = groq_client.chat.completions.create(
                messages=[{"role": "system", "content": "Summarize these 10 podcast episodes into one paragraph of 25 words of key fertility insights.Keep key pointers and dont repeat any content."},
                          {"role": "user", "content": combined_text}],
                model="llama-3.1-8b-instant"
            )
            
            summary_text = response.choices[0].message.content
            summary_embedding = model.encode(summary_text).tolist()
            
            super_docs.upsert(records=[(
                f"summary_{batch_ids[0]}_{batch_ids[-1]}", 
                summary_embedding,
                {"episodes_covered": ", ".join(batch_ids), "summary_content": summary_text}
            )])
            logging.info(f"Stored summary for {batch_ids[0]}.")
            
        except Exception as e:
            logging.error(f"Batch failed: {e}")

    logging.info("Map-Reduce summarization complete.")

if __name__ == "__main__":
    generate_super_summaries()