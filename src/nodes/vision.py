from graph.state import AgentState

def process_image(state: AgentState) -> dict:
    """
    Qwen2.5-VL Vision Node (Mocked)
    Converts uploaded skin image into a structured description.
    """
    image_path = state.get("image_path")
    if image_path:
        # Giả lập Qwen2.5-VL
        return {"image_description": f"[MOCKED] Detailed description of the skin condition in {image_path}"}
    return {"image_description": None}
