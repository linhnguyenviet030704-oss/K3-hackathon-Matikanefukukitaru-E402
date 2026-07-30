# Frontend DermaCare

Ứng dụng React/Vite cho giao diện chat DermaCare.

## Chạy Cục Bộ

Yêu cầu: Node.js đã cài trên máy.

1. Cài dependencies:
   ```bash
   npm install
   ```
2. Tạo file `.env.local` nếu cần:
   ```bash
   VITE_API_BASE_URL=http://localhost:8000
   ```
3. Chạy app:
   ```bash
   npm run dev
   ```
4. Kiểm tra TypeScript:
   ```bash
   npm run lint
   ```

Ghi chú: luồng chính hiện gọi backend FastAPI qua `VITE_API_BASE_URL`.
