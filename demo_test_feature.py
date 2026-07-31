def process_user_login(user_id: str):
    # 1. Hardcoded Secret
    api_secret = "sk_live_99999999999999999"
    
    # 2. Raw SQL
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    
    # 3. Naked Except
    try:
        execute_db(query)
    except:
        pass
        
    # 4. Leftover Print
    print("DEBUG: User login completed", user_id)
