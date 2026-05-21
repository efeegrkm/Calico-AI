import chromadb
import os

def init_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "chroma_data")
    
    client = chromadb.PersistentClient(path=db_path)
    
    collection = client.get_or_create_collection(
        name="calico_knowledge_base",
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"[*] Hedef Dizin: {db_path}")
    print(f"[*] Koleksiyon: {collection.name}")
    
    return collection

if __name__ == "__main__":
    col = init_db()
    print(f"[*] mevcut döküman sayısı: {col.count()}")