import os
import re
import json

def process_podcast_data(input_files):
    # Your required sections
    sections = [
        "Podcast Host",
        "Episode Overview",
        "Key Topics Covered",
        "Listener Takeaways",
        "Key Moments (Timestamps & Detailed Summaries)",
        "Resources Mentioned",
        "Related Podcast Episodes",
        "Share this"
    ]

    # Mapping internal text headers to your required section names 
    # (Since actual text headers vary slightly, e.g., "Episode Summary" vs "Episode Overview")
    header_mapping = {
        "Your Podcast Host": "Podcast Host",
        "Episode Summary": "Episode Overview",
        "Episode Overview": "Episode Overview",
        "Key Topics Covered": "Key Topics Covered",
        "Topics discussed in today’s episode": "Key Topics Covered",
        "Listener Takeaways": "Listener Takeaways",
        "Timestamped Breakdown": "Key Moments (Timestamps & Detailed Summaries)",
        "Timestamps": "Key Moments (Timestamps & Detailed Summaries)",
        "Peer-Reviewed Research & Resources Mentioned": "Resources Mentioned",
        "Resources and Mentions": "Resources Mentioned",
        "Related Fertility Friday Podcast Episodes": "Related Podcast Episodes",
        "Related Podcast Episodes": "Related Podcast Episodes",
        "Share this": "Share this"
    }

    # Create base output directory
    output_base = "chunked_all"
    os.makedirs(output_base, exist_ok=True)

    for file_path in input_files:
        print(f"Reading {file_path}...")
        
        # 1. Open with UTF-8 to prevent charmap/Unicode errors
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            title = entry.get('title', 'Untitled')
            text = entry.get('main_text', '')

            # Extract Episode ID for folder name (e.g., "Episode 610" or "609")
            ep_match = re.search(r"(\d+)", title)
            ep_id = f"Ep_{ep_match.group(1)}" if ep_match else "Unknown_Ep"
            
            ep_folder = os.path.join(output_base, ep_id)
            os.makedirs(ep_folder, exist_ok=True)

            # 2. Split text based on known headers
            # This regex splits by any key in our mapping, keeping the header in the result
            pattern = "|".join([re.escape(k) for k in header_mapping.keys()])
            parts = re.split(f"({pattern})", text)

            # 3. Assign content to sections
            organized_content = {s: "Section not found in this episode." for s in sections}
            
            for i in range(1, len(parts), 2):
                header_found = parts[i].strip()
                content_found = parts[i+1].strip() if (i+1) < len(parts) else ""
                
                # Map the text header to your official section name
                official_name = header_mapping.get(header_found)
                if official_name:
                    organized_content[official_name] = content_found

            # 4. Save each section to a separate file
            for section_name, content in organized_content.items():
                file_safe_name = section_name.replace(" ", "_").lower().split("(")[0].strip("_")
                filename = os.path.join(ep_folder, f"{file_safe_name}.txt")
                
                with open(filename, 'w', encoding='utf-8') as out_f:
                    # Write Header Metadata in every file as requested
                    out_f.write(f"EPISODE: {ep_id}\n")
                    out_f.write(f"TITLE: {title}\n")
                    out_f.write(f"SECTION: {section_name}\n")
                    out_f.write("-" * 40 + "\n\n")
                    out_f.write(content)

    print("Done! All chunks are stored in the 'chunked_episodes' folder.")

# List your 5 files here
my_files = ["all_epi/new0.json", "all_epi/new1.json", "all_epi/new3.json", "all_epi/new4.json", "all_epi/new5.json"]
process_podcast_data(my_files)