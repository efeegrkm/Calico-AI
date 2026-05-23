import json
import hashlib
import os
from database import init_db

def generate_stable_id(title, summary):
    unique_string = f"{title}_{summary}"
    return hashlib.sha256(unique_string.encode('utf-8')).hexdigest()

def ingest_gemini_data(json_file_path):
    print("\n--- Gemini Data Ingestor ---")
    
    if not os.path.exists(json_file_path):
        print(f"[-] Error: {json_file_path} not found.")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[-] JSON decode error: {e}")
        return

    collection = init_db()
    
    new_documents = []
    new_metadatas = []
    new_ids = []
    skipped_count = 0

    print(f"[*] Processing {len(data)} records...")

    for item in data:
        title = item.get("title", "Unknown Title")
        summary = item.get("summary", "")
        topic = item.get("topic", "General")
        keywords = item.get("keywords", "")
        
        stable_id = generate_stable_id(title, summary)
        
        existing_record = collection.get(ids=[stable_id])
        if existing_record and len(existing_record.get('ids', [])) > 0:
            skipped_count += 1
            continue
            
        meta = {
            "category": item.get("category", "dynamic_news"),
            "topic": topic,
            "source": "Gemini_Research",
            "title": title,
            "fetch_scope": item.get("scope", "yearly"),
            "keywords": keywords,
            "exact_date": "AI_Generated"
        }
        
        new_documents.append(summary)
        new_metadatas.append(meta)
        new_ids.append(stable_id)

    if new_documents:
        print(f"[*] Upserting {len(new_documents)} new records into ChromaDB...")
        collection.upsert(documents=new_documents, metadatas=new_metadatas, ids=new_ids)
        print("[+] Ingestion complete.")
    else:
        print("[-] No new records to ingest.")
        
    print(f"[*] Skipped (duplicates): {skipped_count}")

if __name__ == "__main__":
    ingest_gemini_data("gemini_ingestion_data.json")