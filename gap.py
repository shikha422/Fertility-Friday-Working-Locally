import json
import os
import vecs
from groq import Groq
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from backend_shared import model
load_dotenv()

# --- CONFIGURATION ---
GROQ_API_KEY = ""
DB_CONNECTION = ""

os.environ["HF_HUB_READ_TIMEOUT"] = "300"
groq_client = Groq(api_key=GROQ_API_KEY)
vx = vecs.create_client(DB_CONNECTION)

def generate_gap_analysis():
    docs = vx.get_or_create_collection(name="super_short_summaries", dimension=384)
    
    # --- FETCH ENTIRE TABLE ---
    try:
        print("--- Fetching all records from Supabase ---")
        all_points = docs.query(
            data=[0.0] * 384, 
            limit=100,  # Increased limit slightly to ensure you catch everything
            include_metadata=True
        )
        
        if not all_points:
            print("No records found in the collection.")
            return {"error": "Collection is empty."}
            
    except Exception as e:
        return {"error": f"Failed to fetch table: {str(e)}"}

    # --- FORMAT SPECIFIC SECTIONS ---
    existing_topics = ""
    # Define the whitelist of sections you want to include
    target_sections = ["Episode Overview", "Key Topics Covered", "Listener Takeaways"]

    for res in all_points:
        meta = res[1]
        if meta:
            ep_range = meta.get('episodes_covered', 'Unknown Batch')
            
            # Start building the batch string
            batch_string = f"### DATA BATCH ({ep_range}):\n"
            has_relevant_data = False

            # Check for each target section in the metadata
            # We check both the 'section' key and if the specific names are keys themselves
            for section in target_sections:
                # Scenario A: If metadata has a 'section' key and a 'content' key
                if meta.get('section') == section:
                    content = meta.get('content') or meta.get('summary_content')
                    batch_string += f"**{section}**: {content}\n"
                    has_relevant_data = True
                
                # Scenario B: If the sections are stored as their own keys in the dictionary
                elif section in meta:
                    content = meta.get(section)
                    batch_string += f"**{section}**: {content}\n"
                    has_relevant_data = True

            # Only add to the final prompt if we actually found one of the three sections
            if has_relevant_data:
                existing_topics += batch_string + "\n"

    print(f"--- Processing analysis for {len(all_points)} records (Filtered for specific sections) ---")
    
    # --- THE COMPREHENSIVE PROMPT ---
    analysis_prompt = f"""
    You are the Chief Content Strategist for Fertility Friday.
    
    I have provided the FULL summary of our entire podcast library below, organized by episode batches.
    
    LIBRARY DATA:
    {existing_topics}
 
    TASK:
    1. ANALYZE: Review every batch provided above.
    2. CATEGORIZE: Define 4-5 core content pillars that represent this entire body of work.
    3. GAP ANALYSIS: Identify 3 specific, advanced topics in fertility, hormones, or women's health that have NOT been covered in detail across these 39 batches.
    4. STRATEGY: Propose 3 new episode titles to fill these gaps.
 
    OUTPUT RULES:
    - Respond ONLY with a valid JSON object.
    - JSON structure:
    {{
        "summary": "Key insights about the library in 1-2 sentences",
        "gaps": [
            {{
                "trend": "Topic name",
                "status": "Existing or Gap",
                "match": {{"EP_NUMBER": "XXX or N/A"}}
            }}
        ],
        "topics": [
            {{
                "topic": "Strategic Pillar Name",
                "ideas": [
                    {{
                        "title": "Episode Title",
                        "angle": "Content angle",
                        "details": "Specific details about the idea",
                        "value": "Why this is valuable"
                    }}
                ]
            }}
        ]
    }}
    """

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a strategic analyst. You have a perfect memory for the data provided in the prompt."},
                {"role": "user", "content": analysis_prompt},
            ],
            model="llama-3.1-8b-instant", 
            response_format={"type": "json_object"},
            temperature=0.4 # Lower temperature for higher accuracy/less rambling
        )

        raw_result = json.loads(completion.choices[0].message.content)

        # Mapping Shim: Ensure the returned dictionary always contains the required keys for the UI
        # We also handle some common variations in key names
        return {
            "summary": raw_result.get("summary", raw_result.get("synopsis", "Analysis complete.")),
            "gaps": raw_result.get("gaps", raw_result.get("gap_analysis", [])),
            "topics": raw_result.get("topics", raw_result.get("strategy_pillars", raw_result.get("strategy", [])))
        }
    except Exception as e:
        print(f"LLM Processing Error: {e}")
        return {"error": f"LLM Processing Error: {e}"}

'''
if __name__ == "__main__":
    result = generate_gap_analysis()
    
    # Save to a file so you can read the full analysis easily
    with open("full_gap_analysis.json", "w") as f:
        json.dump(result, f, indent=4)
        
    print("\n--- ANALYSIS COMPLETE ---")
    print("Results saved to 'full_gap_analysis.json'")
    print(json.dumps(result, indent=4))
'''