import logging
from graph.state import AgentState
from rag.vectorstore import load_vectorstore

logger = logging.getLogger(__name__)

# Cache vectorstore ở mức global (module-level) để không phải load lại nhiều lần
_cached_vectorstore = None

def get_cached_vectorstore():
    global _cached_vectorstore
    if _cached_vectorstore is None:
        logger.info("Đang nạp Vectorstore và Embedding model lần đầu...")
        _cached_vectorstore = load_vectorstore()
    return _cached_vectorstore

def retrieve_documents(state: AgentState) -> dict:
    """
    RAG Pipeline Node
    Retrieves relevant medical documents from ChromaDB based on the combined user context.
    """
    context = state.get("combined_context") or state.get("user_query")
    
    try:
        vs = get_cached_vectorstore()
        # Lấy top k document (mặc định lấy theo config, thường là 5)
        docs = vs.similarity_search(query=context)
        logger.info(f"Retrieved {len(docs)} documents.")
    except FileNotFoundError:
        # Nếu vectorstore chưa được build
        logger.warning("Vectorstore chưa tồn tại. Vui lòng chạy rag/build_kb.py trước để tạo knowledge base.")
        docs = []
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        docs = []
    
    return {"retrieved_docs": docs}
