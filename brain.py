import requests
import json
from retriever import retrieve_context

def analyze_intent(user_input):
    url = "http://localhost:11434/api/generate"
    
    system_prompt = f"""Analyze the user prompt. 
If it's casual chat/greeting, set intent to "chat". 
If it asks for information, news, stats, or industry data, set intent to "search" and provide English keywords.

User Prompt: "{user_input}"

Output ONLY a JSON object:
{{
    "intent": "chat" or "search",
    "keywords": "search keywords or empty string"
}}"""

    payload = {
        "model": "llama3", 
        "prompt": system_prompt,
        "stream": False,
        "format": "json",
        "keep_alive": 0 
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        return json.loads(response.json().get("response", "").strip())
    except Exception as e:
        print(f"[-] Intent analyzer error: {e}")
        return {"intent": "search", "keywords": user_input}

def compress_to_keywords(raw_context, search_keywords):
    if "System Note:" in raw_context:
        return ""

    url = "http://localhost:11434/api/generate"
    
    system_prompt = f"""You are a data extraction filter. 
The user is searching for: "{search_keywords}"
Here is the raw database output:
{raw_context}

TASK:
1. Ignore data NOT highly relevant to the search.
2. For relevant data, extract the core subject and descriptive keywords.
3. Output ONLY a JSON array of objects.

Format:
{{
    "relevant_developments": [
        {{"subject": "Game/Company Name", "keywords": "success, 1 million players, record breaking"}}
    ]
}}"""

    payload = {
        "model": "llama3",
        "prompt": system_prompt,
        "stream": False,
        "format": "json",
        "keep_alive": 0
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        result_json = json.loads(response.json().get("response", "").strip())
        
        developments = result_json.get("relevant_developments", [])
        if not developments:
            return ""
            
        keyword_list = []
        for dev in developments:
            keyword_list.append(f"- {dev.get('subject')}: {dev.get('keywords')}")
            
        return "\n".join(keyword_list)
        
    except Exception as e:
        print(f"[-] Keyword compressor error: {e}")
        return ""

def chat_with_calico_ai(user_prompt, keywords, intent):
    url = "http://localhost:11434/api/generate"
    
    if intent == "chat" or not keywords:
        final_prompt = f"""User Prompt: "{user_prompt}"
        
Respond naturally based on your core persona. Keep it concise. DO NOT overdo animal noises."""
    else:
        final_prompt = f"""The user asked: "{user_prompt}"

Here are the relevant industry developments extracted as keywords from our database:
{keywords}

CRITICAL INSTRUCTIONS:
1. BE CONCISE & DIRECT: Do not write long, empty, or rambling paragraphs. Get straight to the point.
2. NO PLACEHOLDERS OR HALLUCINATION: NEVER make up data or use placeholders like "[Insert game name]". If the keywords do not contain specific games, state explicitly that you lack specific data.
3. TONE RESTRAINT: You are a Senior Industry Analyst first. Restrain the mascot persona. Limit "meows" or "purrs". Be professional.
4. SYNTHESIS: Weave the keywords into an expert opinion. Respond in the same language as the user's prompt.

Response:"""

    payload = {
        "model": "calico-ai",
        "prompt": final_prompt,
        "stream": True
    }

    print("\n[CalicoAI]: ", end="", flush=True)
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"\n[-] HTTP Error: {response.status_code}")
                return
                
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "error" in chunk:
                        print(f"\n[-] Ollama Error: {chunk['error']}")
                        break
                    print(chunk.get("response", ""), end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n[-] Generation failed: {e}")
        
def start_terminal_chat():
    print("\n--- Calico AI Orchestrator ---")
    print("Type 'q' or 'quit' to exit.\n")

    while True:
        user_input = input("\n[You]: ")
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            break
        if not user_input.strip():
            continue

        print("[*] Analyzing intent...")
        intent_data = analyze_intent(user_input)
        intent = intent_data.get("intent", "search")
        keywords = intent_data.get("keywords", "")

        if intent == "chat":
            print("[-] Chat intent detected.")
            extracted_keywords = ""
        else:
            print(f"[*] Search intent detected. Keywords: '{keywords}'")
            raw_context = retrieve_context(keywords, n_results=15)
            
            print("[*] Compressing context...")
            extracted_keywords = compress_to_keywords(raw_context, keywords)
            
        chat_with_calico_ai(user_input, extracted_keywords, intent)

if __name__ == "__main__":
    start_terminal_chat()