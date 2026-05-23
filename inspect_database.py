import json
from database import init_db

def inspect_database():
    collection = init_db()
    
    # Inside ChromaDB, collection.get() without arguments fetches all records
    results = collection.get()
    
    ids = results.get('ids', [])
    documents = results.get('documents', [])
    metadatas = results.get('metadatas', [])
    
    total_count = len(ids)
    print("\n" + "="*60)
    print(f" DATABASE INSPECTION REPORT | Total Records: {total_count}")
    print("="*60)
    
    if total_count == 0:
        print("[-] The database is completely empty.")
        return
        
    # Categorize items in memory to show a neat summary first
    categories = {}
    for meta in metadatas:
        cat = meta.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
        
    print("\n--- Storage Breakdown ---")
    for cat, count in categories.items():
        print(f" * Category [{cat}]: {count} records")
        
    print("\n--- Detailed Records ---")
    for i in range(total_count):
        print(f"\n[Record #{i+1}] | ID: {ids[i]}")
        
        # Format the metadata dictionary into a pretty string
        meta_pretty = json.dumps(metadatas[i], indent=4)
        print(f"Metadata:\n{meta_pretty}")
        
        # Truncate text if it's too long, just for cleaner console view
        text_preview = documents[i] if len(documents[i]) < 200 else documents[i][:200] + "..."
        print(f"Content Preview: {text_preview}")
        print("-" * 40)

if __name__ == "__main__":
    inspect_database()