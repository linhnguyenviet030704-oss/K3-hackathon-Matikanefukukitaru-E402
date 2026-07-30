import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import AgentState

def generate_response(state: AgentState) -> dict:
    """
    OpenRouter LLM Node
    Generates a response grounded in retrieved evidence.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    chat_model = os.getenv("CHAT_MODEL", "openai/gpt-4o-mini") # Fallback model
    
    # Kiểm tra API key
    if not api_key:
        final_answer = "Lỗi: OPENROUTER_API_KEY chưa được thiết lập. Vui lòng cấu hình trong file .env"
    else:
        # Khởi tạo model qua OpenRouter
        llm = ChatOpenAI(
            model=chat_model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Đưa các tài liệu đã truy xuất vào prompt
        retrieved_docs = state.get("retrieved_docs", [])
        docs_text = "\n\n".join(
            [f"--- Source: {doc.metadata.get('source', 'Unknown')} ---\n{doc.page_content}" for doc in retrieved_docs]
        )
        
        system_prompt = (
            "You are an AI Dermatology Assistant. Your role is to help users understand common skin conditions.\n"
            "DISCLAIMER: Always remind the user that you provide information for educational purposes and they should consult a doctor for actual medical diagnoses.\n\n"
            "Use the following retrieved medical documents to answer the user's question accurately. If the information is not in the documents, rely on your knowledge but state that clearly.\n\n"
            f"=== RETRIEVED DOCUMENTS ===\n{docs_text}\n===========================\n"
        )
        
        # combined_context đã chứa lịch sử chat, mô tả ảnh và câu hỏi hiện tại từ node `context`
        context_str = state.get("combined_context") or state.get("user_query", "")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_str)
        ]
        
        try:
            response = llm.invoke(messages)
            final_answer = response.content
        except Exception as e:
            final_answer = f"Lỗi khi gọi API OpenRouter: {str(e)}"
    
    # Tạo cặp hội thoại mới nhất để reducer cập nhật vào history
    new_turn = [
        {"role": "user", "content": state.get("user_query")},
        {"role": "assistant", "content": final_answer}
    ]
    
    return {
        "final_answer": final_answer,
        "chat_history": new_turn
    }
