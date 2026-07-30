from graph.state import AgentState

def build_context(state: AgentState) -> dict:
    """
    Combines user's text question, image description, and chat history.
    """
    query = state.get("user_query")
    image_description = state.get("image_description")
    chat_history = state.get("chat_history", [])
    
    # Format history
    history_str = ""
    if chat_history:
        history_str = "--- Chat History ---\n"
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_str += f"{role}: {msg['content']}\n"
        history_str += "--------------------\n"
        
    combined = history_str
    if image_description:
        combined += f"Image Context: {image_description}\n"
        
    combined += f"Question: {query}"
        
    return {"combined_context": combined}
