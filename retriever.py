from database import init_db

def retrieve_context(user_query, n_results=5, category_filter=None, topic_filter=None, year_filter=None, month_filter=None):
    collection = init_db()
    
    conditions = []
    
    if category_filter:
        conditions.append({"category": category_filter})
    if topic_filter:
        conditions.append({"topic": topic_filter})
    if year_filter:
        conditions.append({"year": str(year_filter)})
    if month_filter:
        conditions.append({"month": month_filter})
        
    where_clause = None
    if len(conditions) == 1:
        where_clause = conditions[0]
    elif len(conditions) > 1:
        where_clause = {"$and": conditions}

    results = collection.query(
        query_texts=[user_query],
        n_results=n_results,
        where=where_clause
    )
    
    context_blocks = []
    
    if results and results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            doc_text = results['documents'][0][i]
            doc_meta = results['metadatas'][0][i]
            
            source = doc_meta.get('source', 'Internal DB')
            exact_date = doc_meta.get('exact_date', 'Static')
            topic = doc_meta.get('topic', 'General')
            
            block = f"[Source: {source} | Date: {exact_date} | Category: {topic}]\n{doc_text}\n"
            context_blocks.append(block)
            
    if not context_blocks:
        return "[System Note: No relevant information found in the database.]"
        
    return "\n".join(context_blocks)

if __name__ == "__main__":
    print("\n--- Testing Retrieval Module ---")
    
    print("\n[Test 1] Dynamic query:")
    print(retrieve_context("What do we know about Silksong player count or success?", n_results=2))
    
    print("\n[Test 2] Static DB query (studio_games filter):")
    print(retrieve_context("Our Game Jam achievements and awards", n_results=2, category_filter="studio_games"))
    
    print("\n[Test 3] Team query (team_cv filter):")
    print(retrieve_context("Embedded systems, C++, and ECU Logger expertise", n_results=1, category_filter="team_cv"))
    
    print("\n[Test 4] Topic query (Company News filter):")
    print(retrieve_context("Layoffs, studio closures, financial crises in the game industry", n_results=2, topic_filter="Company News"))