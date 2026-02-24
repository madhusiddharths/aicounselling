
import os
import time
from typing import Dict, List
import google.generativeai as genai
from mongodb_fetcher import client, db_name

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
model = genai.GenerativeModel('gemini-2.5-flash')

def get_user_summary(clerk_user_id: str) -> str:
    """Fetch the current user profile summary from MongoDB."""
    db = client[db_name]
    user = db["users"].find_one({"clerk_user_id": clerk_user_id}, {"profile_summary": 1})
    if user and "profile_summary" in user:
        return user["profile_summary"]
    return "No prior memory."

def update_user_summary(clerk_user_id: str, new_summary: str):
    """Update the user's profile summary in MongoDB."""
    db = client[db_name]
    db["users"].update_one(
        {"clerk_user_id": clerk_user_id},
        {"$set": {"profile_summary": new_summary}}
    )

def summarize_session(clerk_user_id: str, history_text: str, current_summary: str) -> str:
    """
    Generate a new summary based on the old summary and recent conversation.
    This condenses the user's long-term profile.
    """
    
    prompt = f"""
    You are an expert mental health memory system. 
    Your goal is to maintain a concise but deep psychological profile of the user based on their conversations.

    ### Current User Profile:
    {current_summary}

    ### Recent Conversation:
    {history_text}

    ### Task:
    Update the User Profile to incorporate new insights from the recent conversation. 
    - Retain key long-term facts (names, major trauma, diagnosis).
    - Update current emotional state and struggles.
    - Note any progress or regression.
    - Discard trivial details (e.g., "User said hello").
    - If the recent conversation adds nothing new, return the Current User Profile as is.

    **Format**:
    Return ONLY the updated profile text. Keep it structured (e.g., Core Issues, Current State, key Facts).
    """

    try:
        response = model.generate_content(prompt)
        new_summary = response.text.strip()
        
        # Safety check: if response is empty or weird, keep old
        if not new_summary or len(new_summary) < 10:
            return current_summary
            
        return new_summary
    except Exception as e:
        print(f"Error summarizing session: {e}")
        return current_summary

def update_memory_lazily(clerk_user_id: str, history_list: List[Dict]):
    """
    Call this occasionally (e.g. every 5 messages) or at session end.
    """
    # 1. format recent history
    history_text = ""
    for h in history_list:
        role = "User" if h.get('user_msg') else "Assistant"
        txt = h.get('user_msg') if role == "User" else h.get('assistant_msg')
        history_text += f"\n{role}: {txt}"
    
    # 2. get current
    current = get_user_summary(clerk_user_id)

    # 3. generate new
    new_summary = summarize_session(clerk_user_id, history_text, current)

    # 4. save
    update_user_summary(clerk_user_id, new_summary)
    print(f"Updated memory for {clerk_user_id}")
