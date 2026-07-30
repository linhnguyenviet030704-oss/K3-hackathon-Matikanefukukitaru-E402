import sys
import os

# Ensure the src folder is in PYTHONPATH if run from elsewhere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph.workflow import create_pipeline

def main():
    print("=" * 50)
    print("   AI Dermatology Assistant (Interactive Chat)")
    print("=" * 50)
    print("Đang khởi tạo LangGraph workflow...")
    
    # Tạo pipeline
    app = create_pipeline()
    
    # Cấu hình thread_id mặc định để lưu lịch sử hội thoại
    config = {"configurable": {"thread_id": "interactive_session_1"}}
    
    print("\nChào mừng bạn! Hãy đặt câu hỏi về các bệnh lý da liễu.")
    print("(Gõ 'quit' hoặc 'exit' để thoát)\n")
    
    while True:
        try:
            # Nhận đầu vào từ người dùng
            user_input = input("[Bạn]: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nKết thúc phiên chat. Tạm biệt!")
                break
                
            # Đóng gói trạng thái
            # Ở bản console loop này, chúng ta mặc định không truyền ảnh (image_path=None). 
            # Bạn có thể tuỳ biến thêm cơ chế kéo/thả link ảnh nếu muốn.
            initial_state = {
                "user_query": user_input,
                "image_path": None 
            }
            
            print("Đang suy nghĩ...")
            
            # Thực thi graph
            result = app.invoke(initial_state, config=config)
            
            # Lấy kết quả
            final_answer = result.get('final_answer')
            
            # Trình bày kết quả
            print(f"\n[AI Assistant]:\n{final_answer}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nKết thúc phiên chat. Tạm biệt!")
            break
        except Exception as e:
            print(f"\n[Lỗi hệ thống]: {e}\n")

if __name__ == "__main__":
    main()
