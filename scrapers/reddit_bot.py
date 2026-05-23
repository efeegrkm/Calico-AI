import requests
import json
import hashlib
import os
import sys
import time
from datetime import datetime

# Adjusting system path to import database.py from the parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import init_db

def evaluate_with_ollama(text):
    """
    Sends the raw text to the local Ollama instance.
    Forces the LLM to output a strict JSON object categorizing and summarizing the news.
    """
    url = "http://localhost:11434/api/generate"
    
    prompt = f"""You are a Lead Data Analyst for an independent game studio.
Analyze the following Reddit post. We ONLY care about macro industry news or high-level indie success data.

Respond STRICTLY with a valid JSON object. Do not include any markdown formatting, backticks, or extra text. Just the JSON.

Rules for JSON output:
1. If the post is irrelevant, a personal rant, a small devlog, or beginner advice, output exactly:
{{"status": "REJECT"}}

2. If the post is HIGH-VALUE (impacts indies, macro trends, engine news, major company shifts), output:
{{
    "status": "ACCEPT",
    "topic": "<CHOOSE ONE: Company News | Engine Update | Indie Success | Market Trend | AI Tech>",
    "summary": "<A 2-3 sentence objective summary focusing on data and facts>"
}}

RAW POST:
{text}
"""
    
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": 0
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        result_text = response.json().get("response", "").strip()
        return json.loads(result_text)
    except json.JSONDecodeError:
        print("[-] Error: Ollama did not return valid JSON.")
        return {"status": "REJECT"}
    except requests.exceptions.RequestException as e:
        print(f"[-] Ollama connection error: {e}")
        return {"status": "REJECT"}

def generate_stable_id(url):
    """Generates a stable SHA-256 hash based strictly on the unique URL."""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()

def scrape_reddit():
    print("[*] Temporal & Categorical Reddit Scraper Bot initialized...")
    
    target_configs = [
        {"sub": "Games", "limit": 70, "timeframe": "year", "scope": "yearly"},
        {"sub": "Games", "limit": 40, "timeframe": "month", "scope": "monthly"},
        {"sub": "Games", "limit": 5, "timeframe": "week", "scope": "weekly"},
        
        {"sub": "gamedev", "limit": 60, "timeframe": "year", "scope": "yearly"},
        {"sub": "gamedev", "limit": 40, "timeframe": "month", "scope": "monthly"},
        {"sub": "gamedev", "limit": 5, "timeframe": "week", "scope": "weekly"},
        
        {"sub": "Unity3D", "limit": 2, "timeframe": "month", "scope": "monthly"}
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CalicoBot/4.1'}
    collection = init_db()
    
    new_documents = []
    new_metadatas = []
    new_ids = []
    
    seen_ids_this_run = set()

    for config in target_configs:
        subreddit = config["sub"]
        print(f"\n[*] Fetching top {config['limit']} posts from r/{subreddit} (Past {config['timeframe']})")
        
        url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={config['limit']}&t={config['timeframe']}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            posts = data['data']['children']
        except Exception as e:
            print(f"[-] Failed to fetch data from r/{subreddit}: {e}")
            continue

        for post in posts:
            post_data = post['data']
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            post_url = post_data.get('url', '')
            created_utc = post_data.get('created_utc', 0)
            
            stable_id = generate_stable_id(post_url)
            
            # 1. KONTROL: Bu haberi az önceki döngüde (örn: yıllık taramada) zaten işledik mi?
            if stable_id in seen_ids_this_run:
                # Logu ekrana basmaya bile gerek yok, sessizce geç
                continue
                
            # 2. KONTROL: Bu haber daha önceki günlerde veritabanına yazılmış mı?
            existing_record = collection.get(ids=[stable_id])
            if existing_record and len(existing_record.get('ids', [])) > 0:
                print(f"[-] SKIP: Already in DB -> {title[:50]}...")
                seen_ids_this_run.add(stable_id)
                continue
            
            combined_content = f"{title}. {selftext}"
            
            if len(combined_content) > 30:
                print(f"\n[+] NEW POST: {title[:70]}...")
                print("[*] Editor LLM is classifying and extracting data...")
                
                raw_text = f"Title: {title}\nBody: {selftext}"
                
                llm_result = evaluate_with_ollama(raw_text)
                
                if llm_result.get("status") == "REJECT":
                    print("[-] REJECTED by LLM criteria.")
                    seen_ids_this_run.add(stable_id)
                    continue
                
                summary = llm_result.get("summary", "")
                topic = llm_result.get("topic", "General Industry")
                
                print(f"[+] ACCEPTED | Topic: {topic}")
                print(f"    Summary: {summary[:100]}...")
                
                post_date = datetime.fromtimestamp(created_utc)
                
                meta = {
                    "category": "dynamic_news",
                    "topic": topic,
                    "source": f"reddit_{subreddit}",
                    "title": title,
                    "url": post_url,
                    "fetch_scope": config["scope"],
                    "year": str(post_date.year),
                    "month": f"{post_date.year}-{post_date.month:02d}",
                    "exact_date": post_date.strftime('%Y-%m-%d')
                }
                
                new_documents.append(summary)
                new_metadatas.append(meta)
                new_ids.append(stable_id)
                
                seen_ids_this_run.add(stable_id)
                
        time.sleep(2)

    if new_documents:
        print(f"\n[*] Upserting {len(new_documents)} time-tagged, categorized articles into ChromaDB...")
        collection.upsert(documents=new_documents, metadatas=new_metadatas, ids=new_ids)
        print(f"[+] SUCCESS! {len(new_documents)} articles securely added without duplicates.")
    else:
        print("\n[-] Scan complete. No new data to insert.")

if __name__ == "__main__":
    scrape_reddit()