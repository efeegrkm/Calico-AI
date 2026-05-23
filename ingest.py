import hashlib
import json
from database import init_db

def generate_id_from_meta(meta_dict):
    meta_string = json.dumps(meta_dict, sort_keys=True)
    return hashlib.sha256(meta_string.encode('utf-8')).hexdigest()

def ingest_static_data():
    collection = init_db()
    
    documents = []
    metadatas = []
    ids = []
    
    # -------------------------------------------------------------------
    # 1. KATEGORİ: TAKIM VE CV BİLGİLERİ
    # -------------------------------------------------------------------
    team_data = [
        {
            "text": "Efe Görkem Akkanat: TOBB ETÜ Bilgisayar Mühendisliği 4. sınıf öğrencisidir. Havelsan'da uzun dönem staj tecrübesine sahiptir. C++, Unity, Qt/QML ve Python dillerinde ileri seviye uzmanlığı vardır. İlgi alanları arasında modüler yazılım mimarisi, RAG sistemleri ve telemetri (ECUMaster EMU Black) bulunur. İngilizce (B2), Almanca (A2) ve İspanyolca (A1) bilmektedir.",
            "meta": {"category": "team_cv", "person": "Efe Görkem Akkanat"}
        },
        {
            "text": "Team Calico Çekirdek Kadrosu: Görkem Altıntaş ve Efe Görkem Akkanat yaratıcı ve profesyonel bir partnerlik yürüterek stüdyonun belkemiğini oluşturmaktadır. Projelerde modüler kod mimarisi ve oyun tasarımı süreçleri ortaklaşa yönetilmektedir.",
            "meta": {"category": "team_cv", "person": "Core Team"}
        }
    ]

    # -------------------------------------------------------------------
    # 2. KATEGORİ: STÜDYO PROJELERİ VE BAŞARILAR
    # -------------------------------------------------------------------
    games_data = [
        {
            "text": "MirrorBlade: Team Calico tarafından geliştirilen aksiyon-roguelike türünde bir oyundur. Aydın Game Jam'de jüri oylamasıyla 1.lik ödülü kazanmıştır.",
            "meta": {"category": "studio_games", "game": "MirrorBlade", "award": "1st Place Aydın Game Jam"}
        },
        {
            "text": "Not a piece of cake: Team Calico tarafından geliştirilen oyundur. Rakun Game Jam yarışmasında 2.lik ve 'Best Sound Design' (En İyi Ses Tasarımı) ödüllerini stüdyoya kazandırmıştır.",
            "meta": {"category": "studio_games", "game": "Not a piece of cake", "award": "2nd Place Rakun Game Jam"}
        }
    ]

    # -------------------------------------------------------------------
    # 3. KATEGORİ: GELECEK VİZYONU VE TEKNİK ALTYAPI
    # -------------------------------------------------------------------
    vision_data = [
        {
            "text": "Calico AI Projesi: Ollama, vektör veritabanları ve otomatik web scraping (kazıma) sistemleri entegre edilerek oluşturulan bir Agentic (Ajan tabanlı) iş akışıdır. Amacı stüdyo içi süreçleri hızlandırmak ve dinamik oyun dünyası verilerini işlemektir.",
            "meta": {"category": "studio_vision", "project": "Calico AI"}
        }
    ]

    all_data = team_data + games_data + vision_data
    
    for item in all_data:
        documents.append(item["text"])
        metadatas.append(item["meta"])
        
        stable_id = generate_id_from_meta(item["meta"])
        ids.append(stable_id)
        
    print("\n[*] Static data writing to the database.")
    
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"[+] {len(documents)} documents successfully updated/added to the database.")

if __name__ == "__main__":
    ingest_static_data()