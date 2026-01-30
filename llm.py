import json
import vecs
from groq import Groq
from sentence_transformers import SentenceTransformer
from backend_shared import model
from dotenv import load_dotenv
GROQ_API_KEY=""
DB_CONNECTION=""  
# Load environment variables
load_dotenv()

# Use the same model you used for embedding

# Initialize Clients
groq_client = Groq(api_key=GROQ_API_KEY)
vx = vecs.create_client(DB_CONNECTION)
docs = vx.get_collection(name="episode_vectors")

def generate_podcast_draft(topic_title):
    # 1. SEARCH DATABASE: Create embedding for the new topic title
    query_vector = model.encode(topic_title)
    
    # Retrieve top 5 relevant chunks to give the LLM enough "past episode" context
    search_results = docs.query(
        data=query_vector,
        limit=10,
        include_metadata=True
    )


    # Format the retrieved context for the prompt
    past_insights = ""
    target_section = "Key Topics Covered"
    '''
    if search_results:
        for res in search_results:
            meta = res[1] # This is the metadata dictionary
            
            # Use .get() to avoid KeyErrors. 
            # It will return 'No text found' if the key doesn't exist.
            ep_id = meta.get('episode_id', 'Unknown ID')
            section = meta.get('section', 'General')
            content = meta.get('content', meta.get('main_text', 'No content available'))
            
            past_insights += f"\n- Episode {ep_id} ({section}): {content}\n"
    else:
        past_insights = "No specific past episodes found."
    '''
    if search_results:
        for res in search_results:
            meta = res[1]  # The metadata dictionary
            section = meta.get('section', '')

            # ONLY proceed if the section matches exactly
            if section == target_section:
                ep_id = meta.get('episode_id', 'Unknown ID')
                content = meta.get('content', meta.get('main_text', 'No content available'))
                
                past_insights += f"\n- Episode {ep_id}: {content}\n"

    # Final check if anything survived the filter
    if not past_insights:
        past_insights = f"No data found specifically under the '{target_section}' section."

    print(f"Context filtered for: {target_section}")
    print("Available metadata keys:", search_results[0][1].keys())

    # 2. PROMPT TEMPLATE (Using your specific structure)
    prompt = f"""
    You are the Senior Content Researcher for the Fertility Friday podcast.

    TASK:
    Generate a comprehensive content draft for this topic: {topic_title}

    DATABASE INSTRUCTION:
    1. Search the attached Vector Database for any past episodes related to this topic.
    2. If found, reference the specific insights or guest names in the "takeaways" or "outline".
    3. If no past episodes exist, use your general expertise in fertility and hormonal health to create a fresh, science-backed perspective.

    ATTACHED VECTOR DATABASE CONTEXT:
    {past_insights}

    TONE:
    Empathetic, scientific, and authoritative (aligned with Fertility Friday's brand).

    OUTPUT RULES:
    - Respond ONLY with raw JSON.
    - Ensure the outline is detailed (at least 3 paragraphs).
    - JSON structure: {{"title": "", "outline": "", "key_takeaways": [], "referenced_episodes": []}}
    """

    # 3. CALL GROQ
    completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant that outputs only raw JSON."},
            {"role": "user", "content": prompt},
        ],
        model="llama-3.1-8b-instant", # Using 70b for better reasoning/JSON following
        response_format={"type": "json_object"}, # Ensures Groq returns valid JSON
        temperature=0.2 # Lower temperature for strictly structured output
    )

    try:
        raw_content = json.loads(completion.choices[0].message.content)
        
        # Ensure outline is a string
        outline = raw_content.get("outline", "")
        if isinstance(outline, list):
            outline = "\n\n".join(outline)
        elif isinstance(outline, dict):
            # Flatten dict into a readable string
            flat_outline = []
            for key, val in outline.items():
                if isinstance(val, dict):
                    section_text = val.get("text", "")
                    subpoints = val.get("subpoints", [])
                    flat_outline.append(f"### {key}\n{section_text}")
                    if subpoints:
                        flat_outline.append("\n".join([f"- {s}" for s in subpoints]))
                else:
                    flat_outline.append(f"### {key}\n{val}")
            outline = "\n\n".join(flat_outline)
        
        # Flatten takeaways if they are objects
        takeaways = raw_content.get("key_takeaways", raw_content.get("takeaways", []))
        if isinstance(takeaways, list):
            processed_takeaways = []
            for t in takeaways:
                if isinstance(t, dict):
                    # Check for various key combinations
                    title = t.get("title", t.get("header", ""))
                    desc = t.get("description", t.get("text", t.get("insight", t.get("takeaway", ""))))
                    
                    if title and desc:
                        processed_takeaways.append(f"**{title}**: {desc}")
                    elif title:
                        processed_takeaways.append(title)
                    elif desc:
                        processed_takeaways.append(desc)
                    else:
                        processed_takeaways.append(str(t))
                else:
                    processed_takeaways.append(str(t))
            takeaways = processed_takeaways

        # SHIM: Map new structure to old UI expectations
        return {
            "title": raw_content.get("title", topic_title),
            "hook": raw_content.get("hook", raw_content.get("tagline", f"Discover the secrets of {topic_title}.")), 
            "takeaways": takeaways,
            "outline": outline,
            "call_to_action": raw_content.get("call_to_action", "Subscribe for more insights.") 
        }
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {"error": "Failed to generate valid JSON content."}
'''
if __name__ == "__main__":
    output = generate_podcast_draft("What is ovulation and why is it important?")
    print(json.dumps(output, indent=2))
'''