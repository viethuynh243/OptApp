# BÁO CÁO GIẢI THÍCH THUẬT TOÁN — OptApp (Tối ưu bố trí cọc móng cầu)

> Tài liệu này trả lời mục **B. Báo cáo giải thích** trong "VI. YÊU CẦU":
>
> 1) Mô hình hóa bài toán · 2) Thuật toán (chọn gì, tại sao, ưu/nhược) ·
> 3) Kết quả (so sánh 2 kiểu bố trí + kiến nghị) · 4) Độ phức tạp & khả năng mở rộng khi K hoặc n tăng.
>
> Ngôn ngữ: **Python 3** (Tkinter cho GUI). Mã nguồn rõ ràng, có comment từng bước,
> chạy được với dữ liệu mẫu (`mcoc_input_sample/`, `run_demo.py`) và dữ liệu nhập tùy ý (qua GUI / file input MCOC).
> Cập nhật: 2026-06-15.

---

## 0. Tóm tắt một trang

- **Bài toán:** tìm cách bố trí cọc sao cho **số cọc ít nhất** mà vẫn thỏa mọi ràng buộc kỹ thuật (sức chịu nén/nhổ, khoảng cách tim cọc, nằm trong bệ, momen…).
- **Đánh giá nội lực — bắt buộc chính xác:** mỗi phương án quyết định được chấm trực tiếp bằng **MCOC** (chương trình tính móng cọc) — gọi như một *hộp đen* (oracle duy nhất). Bên thi công **không chấp nhận kết quả xấp xỉ**.
- **Thuật toán tối ưu chính:** **NSGA-II** (giải thuật di truyền đa mục tiêu) + MCOC exact — file [`core/nsga2_optimizer.py`](../core/nsga2_optimizer.py).
- **Hai mục tiêu:** (f1) số cọc; (f2) mục tiêu phụ — "bệ gọn" (footprint nhỏ, mặc định) hoặc "an toàn" (Pmax nhỏ).
- **Hai kiểu bố trí so sánh:** **Kiểu A** (lưới trực giao) và **Kiểu B** (hoa mai / so le).
- **Chính xác nhưng vẫn nhanh (§2.6):** tốc độ đến từ *giảm số lần gọi MCOC* (cache + ngân sách + dẫn hướng) và *chạy song song*, **không** từ mô hình xấp xỉ. Mô hình bệ cứng ([`rigid_cap.py`](../core/rigid_cap.py)) chỉ là **dẫn hướng nội bộ + heatmap**, không bao giờ là kết quả giao nộp.

---

## 1. MÔ HÌNH HÓA BÀI TOÁN

### 1.1. Phát biểu bài toán (lời)

Kỹ sư cho trước: kích thước bệ `Lx × Ly`, đường kính cọc `d`, sức chịu tải đầu cọc `[Po]` (nén), `[Ct]` (nhổ), `[M]` (uốn, tùy chọn), và **các tổ hợp tải trọng** tác dụng lên đáy bệ (`N, Mx, My`, kèm `Hx, Hy, Mz` nếu xét lực ngang). Cần tìm **số cọc và vị trí từng cọc** để công trình an toàn với **chi phí thấp nhất** (ít cọc nhất, bệ gọn nhất).

### 1.2. Biến quyết định (decision variables)

Thay vì tối ưu trực tiếp tọa độ `(x_i, y_i)` của từng cọc (không gian liên tục 2n chiều, dễ sinh bố trí lệch/phi đối xứng, **không thi công được**), ta tham số hóa bố trí bằng một **lưới đối xứng** qua tâm bệ. Một phương án = một "genome" 5 thành phần ([`nsga2_optimizer.py:24`](../core/nsga2_optimizer.py)):

| Gene     | Ý nghĩa            | Miền giá trị                     |
| -------- | -------------------- | ----------------------------------- |
| `type` | kiểu bố trí       | {A = trực giao, B = hoa mai/so le} |
| `nx`   | số cột             | `1 .. nmax_x` (rời rạc)         |
| `ny`   | số hàng            | `1 .. nmax_y` (rời rạc)         |
| `sx`   | bước lưới theo X | `[3d, 6d]` (liên tục, m)        |
| `sy`   | bước lưới theo Y | `[3d, 6d]` (liên tục, m)        |

→ Đây là **bài toán hỗn hợp rời rạc–liên tục** (mixed-integer). Tọa độ cọc được *sinh ra* từ genome bằng [`generator.generate_coords`](../core/generator.py) / [`refine_optimizer.grid_coords`](../core/refine_optimizer.py), luôn đối xứng quanh tâm bệ (tâm nhóm cọc ≈ tâm bệ → phân bố lực đều nhất).

- **Kiểu A:** lưới chữ nhật `nx × ny` → `n = nx·ny` cọc.
- **Kiểu B:** hàng chẵn `nx` cọc, hàng lẻ `nx−1` cọc (tự lệch nửa bước → hoa mai) → `n = nx·⌈ny/2⌉ + (nx−1)·⌊ny/2⌋`.

### 1.3. Hàm mục tiêu (cả hai đều **cực tiểu hóa**)

```
f1 = số cọc n                         (tiết kiệm vật liệu & thi công)
f2 = mục tiêu phụ:
       'compact' (mặc định) = footprint = (bề rộng + bề cao cụm cọc)  → bệ nhỏ, tiết kiệm bê tông
       'pmax'               = Pmax (T)                                 → dự trữ an toàn lớn hơn
```

Đây là **đa mục tiêu** vì hai tiêu chí **mâu thuẫn**: trải cọc rộng ra mép bệ làm giảm Pmax (an toàn hơn) nhưng tốn bê tông bệ; cụm cọc sát nhau thì bệ gọn nhưng Pmax tăng. Lời giải không phải một điểm mà là một **mặt Pareto** các phương án đánh đổi.

### 1.4. Ràng buộc kỹ thuật

Mỗi phương án phải thỏa (cài đặt trong [`mechanics.check_layout`](../core/mechanics.py) và hàm phạt trong [`nsga2_optimizer.evaluate`](../core/nsga2_optimizer.py:99)):

| Mã   | Ràng buộc             | Diễn giải                                                                                       |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------- |
| R1/R2 | tiền đề              | lưới đối xứng, không bỏ cọc đơn lẻ                                                     |
| R3    | `3d ≤ s ≤ 6d`       | khoảng cách tim–tim nhỏ nhất; có thể siết theo "thông thủy":`s ≥ max(3d, d + clear)` |
| R4    | cọc nằm trong bệ     | `max(\|x\|) + SAFE_D ≤ Lx/2`, tương tự Y |
| R5    | `Pmax ≤ [Po]`        | lực nén đầu cọc lớn nhất                                                                   |
| R5b   | `Pmin ≥ −[Ct]`      | lực nhổ (kéo)                                                                                  |
| R6    | `Mx, My ≤ [M]`       | momen đầu cọc (nếu khai báo)                                                                 |
| R7*   | `Hmax ≤ [H]`         | lực ngang —**đang TẮT** (`ENABLE_LATERAL_CHECK=False`)                                |
| R8*   | `P/[Po] + M/[M] ≤ 1` | tương tác P–M —**đang TẮT** (`ENABLE_PM_INTERACTION=False`)                        |

\* R7/R8 nằm ngoài đề bài (R1–R6) nên tắt theo yêu cầu; khi chấm bằng MCOC thì MCOC đã tính 3D đầy đủ (gồm Hx/Hy/Mz) nên không mất an toàn. Bật lại trong [`core/constants.py`](../core/constants.py:15).

### 1.5. Mô hình tính nội lực — "hộp đen" hai tầng

Cốt lõi của tối ưu là hàm `evaluator(coords) → {Pmax, Pmin, Mxmax, Mymax}`. Có hai cài đặt cắm lẫn nhau ([`blackbox.py`](../core/blackbox.py)):

1. **MCOC exact (mặc định khi chạy thật):** ghi phương án thành file input MCOC ([`mcoc_writer.py`](../io_handlers/mcoc_writer.py)), gọi `MCOC_Batch.exe` ([`mcoc_runner.py`](../core/mcoc_runner.py)), đọc lại nội lực. Đây là lời giải **chính xác** (kể cả nền đàn hồi, cọc xiên, lực ngang).
2. **Bệ cứng + hiệu chỉnh K (mock, để ước lượng nhanh):** công thức nén lệch tâm cổ điển trong [`rigid_cap.py`](../core/rigid_cap.py):

```
P_i = N/n + (Mx − N·cy)·(y_i − cy)/Ix + (My − N·cx)·(x_i − cx)/Iy
```

   với `Ix = Σ(y_i−cy)²`, `Iy = Σ(x_i−cx)²`. Sai số mô hình bệ cứng so với MCOC được bù bằng **hệ số hiệu chỉnh** `K = Pmax_MCOC / Pmax_bệ_cứng`, cập nhật lại sau mỗi lần gọi MCOC ([`rigid_cap.calibration_factor`](../core/rigid_cap.py:108)).

> **Tải trọng từ UI là nguồn duy nhất:** khi chạy MCOC thật, khối tổ hợp tải trong file gốc bị **ghi đè** bằng tải nhập trên giao diện ([`mcoc_writer.render`](../io_handlers/mcoc_writer.py:162)) — đã kiểm chứng trên exe thật: nhân đôi N → Nmax đổi (2065.78 → 3464.73 T).

---

## 2. THUẬT TOÁN: CHỌN GÌ, TẠI SAO, ƯU/NHƯỢC

### 2.1. Vì sao bài toán "khó"

- **Hộp đen, không có đạo hàm:** Pmax là kết quả của MCOC (FEM móng cọc) — không có công thức giải tích khả vi theo `(nx, ny, sx, sy)` ⇒ loại các phương pháp cần gradient (gradient descent, SQP…).
- **Hỗn hợp rời rạc–liên tục:** `type, nx, ny` rời rạc; `sx, sy` liên tục ⇒ không phải LP/QP thuần.
- **Đa mục tiêu mâu thuẫn:** cần cả một **mặt Pareto**, không phải một điểm.
- **Hàm mục tiêu đắt:** mỗi lần gọi MCOC tốn ~0.1–1 s ⇒ phải **hạn chế số lần đánh giá**.
- **Không lồi, nhiều cực trị địa phương:** đổi `type` A↔B hay thêm/bớt một hàng làm số cọc nhảy bậc.

### 2.2. Phương pháp đã chọn: **NSGA-II** (Deb et al., 2002)

NSGA-II = *Non-dominated Sorting Genetic Algorithm II* — giải thuật di truyền đa mục tiêu. Cài đặt đầy đủ 4 thành phần trong [`core/nsga2_optimizer.py`](../core/nsga2_optimizer.py):

1. **Fast non-dominated sorting** — xếp hạng quần thể thành các "front" Pareto ([`fast_non_dominated_sort`](../core/nsga2_optimizer.py:191)).
2. **Crowding distance** — khoảng cách chen chúc, giữ đa dạng dọc mặt Pareto ([`crowding_distance`](../core/nsga2_optimizer.py:222)).
3. **Crowded tournament selection** — chọn lọc theo (rank thấp hơn ↔ thưa hơn) ([`_tournament`](../core/nsga2_optimizer.py:253)).
4. **SBX crossover + polynomial mutation + elitism (μ+λ)** — lai ghép/đột biến rồi gộp cha+con, giữ lại tốt nhất ([`_crossover`](../core/nsga2_optimizer.py:292), [`_mutate`](../core/nsga2_optimizer.py:310), vòng lặp [`run_nsga2`](../core/nsga2_optimizer.py:343)).

**Xử lý ràng buộc — "constrained-domination" (Deb)** ([`_constrained_dominates`](../core/nsga2_optimizer.py:176)): khả thi luôn thắng bất khả thi; hai bất khả thi thì cái vi phạm ít hơn (CV nhỏ hơn) thắng; hai khả thi thì so Pareto. Mức vi phạm `CV` được **chuẩn hóa** từng ràng buộc (chia cho [Po], 3d, Lx/2…) để các thành phần tương đương nhau ([`evaluate`](../core/nsga2_optimizer.py:139)).

**Hai kỹ thuật quan trọng để tiết kiệm MCOC:**

- **Cache theo `spec_key`** ([`nsga2_optimizer.py:108`](../core/nsga2_optimizer.py)): hai genome giải mã ra cùng lưới ⇒ chỉ gọi MCOC một lần.
- **Trần ngân sách `max_evals`** ([`nsga2_optimizer.py:384`](../core/nsga2_optimizer.py)): khi đạt số lần gọi tối đa, chỉ dùng kết quả đã cache (GUI đặt `pop_size=16, n_gen=10, max_evals=50`).

### 2.3. Tại sao NSGA-II phù hợp

- Không cần đạo hàm — chỉ cần giá trị mục tiêu ⇒ hợp với hộp đen MCOC.
- Xử lý tự nhiên biến **hỗn hợp** (rời rạc + liên tục) qua toán tử lai/đột biến riêng cho từng gene.
- Trả về **cả mặt Pareto** trong một lần chạy ⇒ kỹ sư chọn theo bối cảnh (tiết kiệm vs an toàn).
- Cơ chế ràng buộc của Deb không cần hàm phạt thủ công tinh chỉnh trọng số.

### 2.4. So sánh với các phương án khác (ưu/nhược)

| Phương pháp                                                                               | Ưu điểm                                                                                                                                                                       | Nhược điểm                                                                                                                                   | Vai trò trong dự án                                                               |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **Quét lưới (Grid Search)** [`optimizer.py`](../core/optimizer.py)                   | Đơn giản,**vét cạn** không gian rời rạc `(type, nx, ny)`; tất định                                                                                            | `sx, sy` phải cố định (lấy max); **dùng mock bệ cứng ⇒ kết quả xấp xỉ, KHÔNG nghiệm thu được**                                                 | **Chỉ còn dùng cho demo** (`run_demo.py`); UI (Tab 1 & Tab 2) không dùng |
| **Tinh chỉnh Pareto tất định** [`refine_optimizer.py`](../core/refine_optimizer.py) | **Dự báo–kiểm chứng–hiệu chỉnh:** dự báo bằng bệ cứng×K rồi chỉ gọi MCOC cho ứng viên hứa hẹn ⇒ **rất ít lần gọi MCOC**; lặp lại được | Đi theo bước cục bộ (co bước, bỏ hàng/cột, A→B) nên thiên về**lân cận** phương án gốc                                  | Chế độ "Refine" — tinh chỉnh một bố trí có sẵn                             |
| **NSGA-II** [`nsga2_optimizer.py`](../core/nsga2_optimizer.py)                          | Đa mục tiêu, hỗn hợp biến, không gradient, cho cả mặt Pareto; thám hiểm toàn cục tốt                                                                               | **Ngẫu nhiên** (cần seed để tái lập); không đảm bảo tối ưu tuyệt đối; tốn nhiều lần đánh giá nếu không khống chế | **Thuật toán chính** của nút "Chạy tối ưu hóa" (NSGA-II + MCOC exact) |
| Quy hoạch lồi / gradient                                                                   | Hội tụ nhanh nếu áp dụng được                                                                                                                                            | Cần khả vi & lồi —**không** thỏa ở đây                                                                                            | Không dùng                                                                         |
| Vét cạn toàn bộ (lưới + MCOC)                                                          | Tối ưu **tuyệt đối**                                                                                                                                                 | Chi phí MCOC khổng lồ khi n, K lớn                                                                                                           | Đề xuất tùy chọn tương lai                                                    |

> **Kết luận lựa chọn:** **NSGA-II + MCOC exact** là **đường quyết định duy nhất**. Quét lưới (mock bệ cứng) **không** dùng để quyết định — chỉ dùng làm dẫn hướng nội bộ và tô heatmap. Engine tinh chỉnh Pareto tất định cũng chấm bằng MCOC (bệ cứng chỉ là dự báo để chọn ứng viên).

> **⚠️ Ràng buộc nghiệm thu:** bên thi công **không chấp nhận kết quả xấp xỉ** — mọi số liệu giao nộp (Pmax, Pmin, M, kết luận ĐẠT/KHÔNG) phải do **MCOC** tính. Cách dung hòa "chính xác bắt buộc" với "tốc độ tốt" trình bày ở §2.6.

### 2.6. NGUYÊN TẮC CHÍNH XÁC BẮT BUỘC & CHIẾN LƯỢC TỐC ĐỘ

**Nguyên tắc bất biến:** MCOC là **oracle duy nhất**. Tính hợp lệ (R3–R6) và mọi nội lực báo cáo đều là số MCOC. Tốc độ **không** đến từ việc thay MCOC bằng mô hình xấp xỉ, mà từ hai hướng: **(I) giảm số lần gọi MCOC** và **(II) chạy song song** các lần gọi còn lại. Bệ cứng chỉ là *heuristic dẫn hướng*, ảnh hưởng **thứ tự** duyệt chứ không ảnh hưởng kết quả ⇒ có thể tắt mà không đổi tính đúng đắn.

**Chi phí thực đo:** một lần gọi MCOC ≈ **0.1–1 s** (đo trên máy thật: bài T14 — 22 cọc, 12 tổ hợp — ≈ 0.8–1.0 s/lần). Đây là chi phí *thống trị*; mọi thứ khác (công thức bệ cứng, sắp xếp Pareto) ở mức mili-giây.

**Năm đòn bẩy tốc độ (đều giữ nguyên tính chính xác):**

| # | Đòn bẩy | Cơ chế | Đã có trong code? |
|---|---|---|---|
| 1 | **Cache theo lưới (memoize)** | Không gọi MCOC hai lần cho cùng một bố trí (`spec_key`). GA hay xét lại cấu hình → tiết kiệm lớn | ✅ `nsga2_optimizer.py:108` |
| 2 | **Trần ngân sách + dừng sớm** | `max_evals` chặn số lần gọi MCOC; dừng khi mặt Pareto không cải thiện | ✅ `max_evals` (GUI=50) |
| 3 | **Dẫn hướng bằng predictor rẻ** | Bệ cứng (<1 ms) **xếp hạng** ứng viên & giải nhị phân bước cọc → gửi MCOC ứng viên hứa hẹn nhất trước. Predictor **không** vào kết quả; phương án ĐẠT đều đã qua MCOC | ✅ `refine_optimizer.solve_min_scale` |
| 4 | **Song song hóa lời gọi MCOC** | `MCOC_Batch.exe` nhận **nhiều** file; chạy song song trên nhiều lõi CPU → tăng tốc ≈ số lõi | ⏳ *khuyến nghị nâng cấp* (hiện chạy tuần tự) |
| 5 | **Cache bền (đĩa)** | Hash bố trí → kết quả MCOC lưu ra đĩa; lần chạy sau dùng lại tức thì | ⏳ *khuyến nghị* |

**Ước lượng thời gian (n,K vừa phải, ~1 s/lần gọi):**

| Cách làm | Số lần gọi MCOC | Thời gian tuần tự | Song song 8 lõi |
|---|---|---|---|
| Vét cạn lưới + MCOC | ~162 | ~162 s | ~20 s |
| **NSGA-II + cache + budget** (mặc định) | **≤ 50** | **~50 s** | **~7 s** |
| Tinh chỉnh predict-verify | ~10–25 | ~10–25 s | ~2–4 s |

**Vì sao vẫn "chính xác":** predictor chỉ quyết định *gọi MCOC theo thứ tự nào*; mọi phương án được **chấp nhận/kiến nghị** đều có số liệu MCOC trực tiếp. Nếu muốn tuyệt đối không dùng bất kỳ mô hình nào, tắt đòn bẩy #3 và chạy **MCOC thuần + song song (#4)** — chậm hơn nhưng vẫn trong vài chục giây nhờ #1, #2, #4.

### 2.5. Các bước xử lý (pipeline đầu–cuối)

```
(1) Nhập:  Lx, Ly, d, [Po], [Ct], [M] + các tổ hợp tải (N, Mx, My, …)   [GUI / file MCOC]
(2) Kiểm tra đầu vào: phải có ≥1 tổ hợp tải; nếu chạy MCOC phải có MCOC_Batch + file input gốc
(3) Khởi tạo quần thể genome ngẫu nhiên (sửa chữa nx,ny hợp lệ; kẹp sx,sy vào [3d,6d])
(4) Đánh giá mỗi cá thể:
        decode genome → tọa độ cọc  →  evaluator(coords) = MCOC exact (oracle duy nhất)
        → Pmax,Pmin,Mxmax,Mymax → tính CV (vi phạm ràng buộc) + mục tiêu (n, f2)
        (cache theo lưới để không gọi MCOC trùng; predictor bệ cứng chỉ để xếp thứ tự)
(5) Lặp tiến hóa G thế hệ:
        tournament chọn cha → SBX lai ghép → đột biến đa thức
        → gộp cha+con → non-dominated sort + crowding → giữ lại pop_size tốt nhất (elitism)
        (dừng sớm nếu chạm trần max_evals)
(6) Tổng hợp: lọc mặt Pareto khả thi (số cọc, mục tiêu phụ) từ TẤT CẢ cá thể đã đánh giá
(7) Kiến nghị phương án ít cọc nhất → gọn/an toàn nhất; xuất bảng tọa độ + báo cáo kỹ thuật + biểu đồ
```

---

## 3. KẾT QUẢ: SO SÁNH 2 KIỂU BỐ TRÍ & KIẾN NGHỊ

### 3.1. Bảng so sánh Kiểu A vs Kiểu B

Ví dụ minh họa **đánh đổi hình học A↔B** (bệ `Lx=12.0, Ly=15.0 m`, `d=1.0 m`, `[Po]=400 T`, một tổ hợp `N=4000 T, Mx=1200, My=800 T·m`). *Lưu ý:* các số `Pmax` dưới đây lấy từ bộ dẫn hướng để minh họa quan hệ A/B; **trong vận hành thực, `Pmax` quyết định lấy từ MCOC**:

| Tiêu chí                         | **Kiểu A (trực giao)** | **Kiểu B (hoa mai/so le)** |
| ---------------------------------- | ------------------------------ | --------------------------------- |
| Lưới                             | 3 × 4                         | 3 × 5                            |
| **Số cọc**                 | **12**                   | 13                                |
| Bước cọc `sx, sy` (m)         | 5.00 / 4.33                    | 5.00 / 3.25                       |
| `Pmax` (T)                       | 381.0                          | 356.9                             |
| Thỏa `Pmax ≤ [Po]=400`         | ✅                             | ✅                                |
| Dự trữ an toàn (`[Po]−Pmax`) | 19.0 T                         | **43.1 T**                  |

**Nhận xét:** Kiểu B trải cọc so le nên `Pmax` thấp hơn (an toàn hơn ~6%), nhưng để thỏa khoảng cách 3d–6d nó cần **thêm 1 cọc**. Khi tiêu chí hàng đầu là **ít cọc nhất**, Kiểu A thắng.

> Trên bệ nhỏ (`6.0×9.6 m, d=1.2`, `Po=500`), Kiểu B (cần `nx≥2, ny≥2` và khoảng cách chéo ≥ 3d) **không có** phương án khả thi, còn Kiểu A đạt **2×3 = 6 cọc, Pmax≈479–487 T** — minh họa rằng trên bệ chật, lưới trực giao linh hoạt hơn.

### 3.2. Phương án kiến nghị & lý do

Quy tắc chọn (phần tổng hợp Pareto của NSGA-II, [`nsga2_optimizer.py:444`](../core/nsga2_optimizer.py)):

1. **Ít cọc nhất** (chi phí thấp nhất) — ưu tiên số 1.
2. Nếu **bằng số cọc** → chọn **mục tiêu phụ**: "bệ gọn" (footprint nhỏ, mặc định) hoặc "an toàn" (`Pmax` nhỏ).
3. Nếu vẫn ngang nhau → **ưu tiên giữ phương án gốc** trong file (giảm xáo trộn thiết kế).

→ Với ví dụ trên: **kiến nghị Kiểu A 3×4 = 12 cọc, Pmax = 381.0 T / [Po] = 400 T** — *"Kiểu trực giao tiết kiệm cọc nhất (chỉ 12 cọc)"*. Nếu kỹ sư ưu tiên dự trữ an toàn hơn tiết kiệm, có thể chọn phương án Kiểu B 13 cọc trên cùng mặt Pareto.

### 3.3. Đầu ra của chương trình

- Bảng **tọa độ từng cọc** + nội lực `P` của tổ hợp **bất lợi nhất**.
- **Mặt Pareto** các phương án không bị thống trị (để kỹ sư cân nhắc đánh đổi).
- **Báo cáo kỹ thuật** Markdown ([`report_writer.py`](../io_handlers/report_writer.py)): số liệu đầu vào, tổ hợp tải, kiểm tra hình học, nội lực + **hệ số sử dụng** + **tổ hợp chi phối**, bảng ràng buộc R1–R8, phụ lục giới hạn mô hình.
- **Biểu đồ** bố trí cọc vẽ tổ hợp bất lợi nhất ([`plot_canvas.py`](../ui/plot_canvas.py)).

---

## 4. ĐỘ PHỨC TẠP TÍNH TOÁN & KHẢ NĂNG MỞ RỘNG

Ký hiệu: `n` = số cọc một phương án; `K` = số tổ hợp tải; `P` = kích thước quần thể (`pop_size`); `G` = số thế hệ (`n_gen`); `M` = số mục tiêu (= 2).

### 4.1. Chi phí một lần đánh giá phương án

| Thao tác                                                                | Độ phức tạp       | Ghi chú                                                          |
| ------------------------------------------------------------------------ | --------------------- | ----------------------------------------------------------------- |
| Công thức bệ cứng 1 tổ hợp[`pile_forces`](../core/rigid_cap.py:21)  | `O(n)`              | vector hóa NumPy                                                 |
| Tất cả tổ hợp[`forces_all_loads`](../core/rigid_cap.py:36)            | **`O(K·n)`** | **tuyến tính theo K**                                     |
| Khoảng cách tim–tim nhỏ nhất[`min_spacing`](../core/rigid_cap.py:97) | **`O(n²)`**  | ma trận khoảng cách cặp đôi —*nút thắt khi n lớn*     |
| Một lần gọi**MCOC**                                             | hộp đen (~0.1–1 s) | chi phối thời gian thực tế; xử lý cả K tổ hợp bên trong |

→ Đánh giá bằng **mock** (bệ cứng): `O(K·n + n²)`. Đánh giá bằng **MCOC**: chi phối bởi thời gian của exe (mỗi lần gọi tính trọn K tổ hợp).

### 4.2. Chi phí thuật toán NSGA-II

- **Sắp xếp không-bị-thống-trị:** `O(M·P²)` mỗi thế hệ → `O(G·M·P²)` toàn cuộc.
- **Số lần đánh giá (gọi evaluator):** tối đa `P + G·P`, nhưng **bị chặn trên bởi `max_evals`** và **giảm mạnh nhờ cache** (nhiều genome trùng lưới). Đây là chi phí *thống trị* khi dùng MCOC.
- Quan trọng: chi phí NSGA-II **không phụ thuộc n** (số cọc) — chỉ phụ thuộc `P, G`. Vì vậy bệ lớn (n lớn) không làm GA chậm thêm; chỉ làm mỗi lần đánh giá (mock `O(n²)` hoặc MCOC) đắt hơn.

So sánh: **quét lưới** duyệt `2·(NX_MAX−NX_MIN+1)²` cấu hình (mặc định `2·9² = 162`), mỗi cấu hình 1 lần đánh giá ⇒ tất định nhưng số lần đánh giá cố định và không tinh chỉnh được `sx, sy`.

### 4.3. Khi **K tăng lớn** (nhiều tổ hợp tải)

- Mô hình bệ cứng: **tuyến tính `O(K·n)`** — mở rộng tốt.
- MCOC: xử lý mọi tổ hợp trong **một** lần gọi (số lần gọi exe không tăng theo K), nên chi phí tăng *bên trong* MCOC chứ không nhân với số lần tối ưu.
- Tác động lên thuật toán tối ưu: **không đáng kể** — K chỉ làm nặng phép đánh giá, không làm tăng kích thước không gian tìm kiếm.

### 4.4. Khi **n tăng lớn** (bệ nhiều cọc)

- Số lần gọi MCOC **không tăng** theo n (vẫn `≤ max_evals`), nên GA vẫn khả thi.
- Nút thắt là `min_spacing` `O(n²)` trong mock. Khi cần n rất lớn (vài trăm cọc), nên thay bằng **cây k-d / lưới băm không gian** để hạ về `O(n log n)`.
- Không gian tìm kiếm `(type, nx, ny, sx, sy)` lớn lên cùng bệ, nhưng GA điều khiển chi phí qua `P, G` (độc lập với n) ⇒ co giãn tốt hơn quét lưới.

### 4.5. Tóm tắt khả năng mở rộng

| Yếu tố tăng        | Ảnh hưởng                                                                   | Đánh giá                                    |
| --------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------- |
| `K` (tổ hợp tải) | đánh giá `O(K·n)`; MCOC gộp 1 lần gọi                                 | **Tốt** (tuyến tính)                  |
| `n` (số cọc)      | mock `O(n²)` (cải thiện được); MCOC tự lo; số lần gọi không đổi | **Khá** — nút thắt `min_spacing`   |
| `P, G` (GA)         | sắp xếp `O(G·M·P²)`, đánh giá `≤ max_evals` (cache)               | **Điều khiển được** bằng tham số |
| Không gian bố trí  | GA không vét cạn → gần tối ưu                                           | Đổi lấy chi phí MCOC chấp nhận được   |

---

## 5. ĐỐI CHIẾU VỚI YÊU CẦU

| Yêu cầu (VI)                                | Đáp ứng                                                                           |
| --------------------------------------------- | ------------------------------------------------------------------------------------ |
| A. Ngôn ngữ tự chọn                       | Python 3                                                                             |
| A. Code rõ ràng, comment từng bước       | docstring + comment tiếng Việt ở mọi module `core/`, `io_handlers/`, `ui/` |
| A. Chạy với dữ liệu mẫu & nhập tùy ý  | `run_demo.py`, `mcoc_input_sample/`; GUI nhập tay / nạp file MCOC              |
| B1. Mô hình hóa                            | §1 (biến, mục tiêu, ràng buộc, mô hình nội lực)                            |
| B2. Thuật toán + tại sao + ưu/nhược     | §2 (NSGA-II; bảng so sánh các phương pháp)                                    |
| B3. Kết quả: so sánh 2 kiểu + kiến nghị | §3 (bảng A vs B + quy tắc kiến nghị)                                            |
| B4. Độ phức tạp & mở rộng khi K, n lớn | §4                                                                                  |

---

*Tham chiếu mã nguồn:* [`core/nsga2_optimizer.py`](../core/nsga2_optimizer.py) · [`core/optimizer.py`](../core/optimizer.py) · [`core/refine_optimizer.py`](../core/refine_optimizer.py) · [`core/rigid_cap.py`](../core/rigid_cap.py) · [`core/mechanics.py`](../core/mechanics.py) · [`core/blackbox.py`](../core/blackbox.py) · [`core/generator.py`](../core/generator.py) · [`io_handlers/mcoc_writer.py`](../io_handlers/mcoc_writer.py) · [`core/mcoc_runner.py`](../core/mcoc_runner.py).
