from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from graph.state import AgentState

from nodes.vision import process_image
from nodes.context import build_context
from nodes.retrieval import retrieve_documents
from nodes.generation import generate_response

def create_pipeline():
    """
    Creates the LangGraph workflow for the AI Dermatology Assistant.
    """
    # Khởi tạo graph với AgentState
    workflow = StateGraph(AgentState)
    
    # Định nghĩa các nodes
    workflow.add_node("process_image", process_image)
    workflow.add_node("build_context", build_context)
    workflow.add_node("retrieve_documents", retrieve_documents)
    workflow.add_node("generate_response", generate_response)
    
    # Thiết lập luồng chạy
    workflow.set_entry_point("process_image")
    workflow.add_edge("process_image", "build_context")
    workflow.add_edge("build_context", "retrieve_documents")
    workflow.add_edge("retrieve_documents", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Sử dụng MemorySaver để lưu trữ trạng thái (lịch sử chat) theo thread
    memory = MemorySaver()
    
    # Biên dịch pipeline kèm checkpointer
    app = workflow.compile(checkpointer=memory)
    
    return app
