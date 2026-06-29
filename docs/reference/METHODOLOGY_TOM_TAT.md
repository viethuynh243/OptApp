# Tóm tắt Phương pháp Tối ưu hóa Móng Cọc

> **Mã:** OA-DOC-03b · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** METHODOLOGY.md


> Tóm tắt ngắn gọn thuật toán **hiện hành** của chương trình.
> Phương pháp chính: **NSGA-II (di truyền đa mục tiêu) + đánh giá MCOC chính xác**.
> (Bản tóm tắt cũ mô tả "Grid Search + bệ cứng" làm phương pháp chính nay **không còn đúng** —
> bệ cứng chỉ còn dùng để ước lượng nhanh / xem trước, không dùng để duyệt thiết kế.)

## 1. Mục tiêu

Tìm cấu hình cọc có **số lượng ít nhất** mà vẫn thỏa **tuyệt đối** các tiêu chuẩn chịu lực và thi công, trên kích thước bệ cho trước. Vì bài toán nhiều tiêu chí mâu thuẫn, lời giải là **mặt Pareto** các phương án đánh đổi, từ đó kiến nghị một phương án.

## 2. Mô hình hóa (biến – mục tiêu – ràng buộc)

- **Biến quyết định (genome):** `(type, nx, ny, sx, sy)` — kiểu lưới A (trực giao) / B (hoa mai), số cột/hàng (rời rạc), bước lưới `sx, sy ∈ [3d, 6d]` (liên tục). Đây là bài toán **hỗn hợp rời rạc–liên tục**. Tọa độ cọc sinh ra **luôn đối xứng quanh tâm bệ**.
- **Hai mục tiêu (đều cực tiểu):**
  - `f₁ = số cọc` (tiết kiệm vật liệu, thi công);
  - `f₂ = mục tiêu phụ` — **"bệ gọn"** (footprint nhỏ nhất, *mặc định*) hoặc **"an toàn"** (Pmax nhỏ nhất). Chọn trên giao diện.
- **Ràng buộc:** R3 `3d ≤ s ≤ 6d` (Kiểu B xét **đường chéo**); R4 cọc nằm trong bệ (`max|x|+SAFE_D ≤ Lx/2`); R5 `Pmax ≤ [Po]`; R5b `Pmin ≥ −[Ct]` (khi `Ct>0`); R6 `Mx,My ≤ [M]` (tùy chọn). R7 (lực ngang) / R8 (tương tác P–M) **đang tắt** theo đề bài R1–R6.

## 3. Thuật toán chính: NSGA-II (`core/nsga2_optimizer.py`)

Giải thuật di truyền đa mục tiêu (Deb et al., 2002), gồm 4 thành phần lõi:

1. **Fast non-dominated sorting** — xếp hạng quần thể thành các front Pareto.
2. **Crowding distance** — giữ đa dạng nghiệm dọc mặt Pareto.
3. **Crowded tournament selection** — chọn lọc (rank thấp hơn → thưa hơn).
4. **SBX crossover + đột biến đa thức + elitism (μ+λ)** — sinh con, gộp cha+con, giữ tinh hoa.

**Xử lý ràng buộc — "constrained-domination" (Deb):** mọi vi phạm được gộp thành chỉ số `CV` đã chuẩn hóa; khả thi luôn trội hơn bất khả thi, hai bất khả thi thì CV nhỏ hơn trội hơn, hai khả thi thì so Pareto trên `(f₁, f₂)`.

**Tiết kiệm lần gọi MCOC:** mỗi genome chỉ gọi MCOC **một lần** nhờ **cache theo lưới** (`spec_key`); tham số **`max_evals`** đặt trần số lần chạy MCOC để kiểm soát thời gian (GUI dùng `pop_size=16, n_gen=10, max_evals=50`).

## 4. Đánh giá nội lực — MCOC chính xác (mặc định)

Mỗi phương án được chấm bằng **hộp đen MCOC** (`MCOCBlackbox.make_real_evaluator` → `mcoc_writer` sinh file input → `mcoc_runner` chạy `MCOC_Batch.exe` → đọc `*_result.txt`). Kết quả **exact** (kể cả nền đàn hồi, lực ngang).

- **Bắt buộc** cấu hình MCOC Batch + file input gốc; thiếu thì chương trình **từ chối chạy** (không có đường xấp xỉ trong quyết định).
- **Tải trọng lấy từ giao diện là nguồn duy nhất:** khối tổ hợp tải trong file gốc bị **ghi đè** bằng tải nhập trên UI.

**Chính xác bắt buộc nhưng vẫn nhanh:** MCOC là oracle duy nhất; tốc độ đến từ việc *giảm số lần gọi MCOC* (cache theo lưới + `max_evals` + dẫn hướng bằng predictor rẻ) và *song song hóa* các lần gọi còn lại — **không** thay MCOC bằng xấp xỉ. 1 lần gọi ≈ 0.1–1 s; NSGA-II mặc định ≤ 50 lần gọi (~50 s tuần tự, ~7 s nếu song song 8 lõi). Chi tiết: `docs/BAO_CAO_THUAT_TOAN.md §2.6`.

**Ước lượng nhanh (không phải đường quyết định):** mô hình **bệ cứng + hệ số hiệu chỉnh K** (`core/rigid_cap.py`) cho Pmax tức thì (`P_i = N/n + (Mx−N·cy)(y_i−cy)/Ix + (My−N·cx)(x_i−cx)/Iy`, với `K = Pmax_MCOC/Pmax_bệ_cứng`). Dùng cho mock NSGA-II khi không có MCOC, tô màu heatmap, và **dự báo** trong engine tinh chỉnh tất định.

## 5. Đề xuất phương án

Trong số phương án **ĐẠT** trên mặt Pareto: ưu tiên (1) **ít cọc nhất** → (2) **mục tiêu phụ** (bệ gọn / Pmax nhỏ) → (3) nếu ngang nhau thì **giữ phương án gốc**. Chương trình so sánh **Kiểu A vs Kiểu B**, kiến nghị phương án tối ưu kèm lý do, bảng tọa độ, báo cáo kỹ thuật và biểu đồ tổ hợp bất lợi nhất.

## 6. Ba engine trong code (dùng tùy mục đích)

| Engine | Thuật toán | Đánh giá nội lực | Vai trò |
|---|---|---|---|
| `nsga2_optimizer.py` | **NSGA-II (di truyền, đa mục tiêu)** | **MCOC exact** (hoặc mock) | **Chính** — nút "Chạy tối ưu hóa" |
| `refine_optimizer.py` | Pareto tất định (dự báo→kiểm chứng→hiệu chỉnh) | MCOC exact + dự báo bệ cứng | Tinh chỉnh từ phương án gốc, ít lần gọi MCOC |
| `optimizer.py` | Grid Search (quét lưới) | Bệ cứng (xấp xỉ) | **Chỉ demo** (`run_demo.py`) — không dùng quyết định |

> Chạy thử: `python run_nsga2_demo.py` (NSGA-II mock), `python run_demo.py` (bệ cứng).
> Chi tiết đầy đủ: `methodology.md`; báo cáo thuật toán theo "VI. YÊU CẦU": `docs/BAO_CAO_THUAT_TOAN.md`.
