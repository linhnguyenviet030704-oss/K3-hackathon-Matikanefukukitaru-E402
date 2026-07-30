from typing import TypedDict, Optional, List, Annotated
from langchain_core.documents import Document

def update_history(old_history: List[dict], new_history: List[dict]) -> List[dict]:
    """
    Reducer để cộng gộp lịch sử chat và chỉ giữ lại 5 câu gần nhất 
    (1 câu gồm 1 lượt hỏi của user + 1 lượt trả lời của bot = 2 messages -> 5 câu = 10 messages)
    """
    if old_history is None:
        old_history = []
    if new_history is None:
        new_history = []
    
    combined = old_history + new_history
    # Giữ lại 10 messages cuối (tương đương 5 lượt hội thoại)
    return combined[-10:]

class AgentState(TypedDict):
    user_query: str
    image_path: Optional[str]
    image_description: Optional[str]
    combined_context: Optional[str]
    retrieved_docs: List[Document]
    final_answer: str
    chat_history: Annotated[List[dict], update_history]
