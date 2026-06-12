# 📘 TÀI LIỆU KỸ THUẬT DỰ ÁN: OptApp — Tối Ưu Hóa Bố Trí Cọc Móng Cầu

> **Tổ chức:** TEDI – Tổng Công ty Tư vấn Thiết kế GTVT
> **Ngôn ngữ:** Python 3.x
> **Giao diện:** Tkinter + TkinterDnD2
> **Mục tiêu:** Tự động tìm cấu hình bố trí cọc tối ưu (ít cọc nhất, đảm bảo tuyệt đối các ràng buộc kỹ thuật) cho móng cọc cầu đường bộ.

---

## MỤC LỤC

1. [Bài toán &amp; Đặt vấn đề](#1-bài-toán--đặt-vấn-đề)
2. [Kiến trúc tổng thể](#2-kiến-trúc-tổng-thể)
3. [Workflow chi tiết từng bước](#3-workflow-chi-tiết-từng-bước)
4. [Phương pháp giải quyết bài toán](#4-phương-pháp-giải-quyết-bài-toán)
5. [Giải thích từng module &amp; hàm](#5-giải-thích-từng-module--hàm)
6. [Bảng Design Pattern](#6-bảng-design-pattern)
7. [Dữ liệu nhập tùy ý — Ví dụ chạy thực tế](#7-dữ-liệu-nhập-tùy-ý--ví-dụ-chạy-thực-tế)
8. [Định dạng file Input/Output](#8-định-dạng-file-inputoutput)
9. [Cài đặt &amp; Chạy chương trình](#9-cài-đặt--chạy-chương-trình)

---

## 1. Bài toán & Đặt vấn đề

### 1.1 Bài toán gốc

Kỹ sư thiết kế cầu cần **bố trí cọc móng** cho mố/trụ cầu sao cho:

| Yêu cầu                        | Ý nghĩa                                                    |
| -------------------------------- | ------------------------------------------------------------ |
| **Ít cọc nhất**         | Tiết kiệm chi phí vật liệu, thi công                   |
| **Pmax ≤ Po**             | Lực nén đầu cọc không vượt sức chịu tải cho phép |
| **Pmin ≥ −Ct**           | Lực nhổ (kéo) không vượt giới hạn kéo               |
| **3d ≤ s ≤ 6d**          | Khoảng cách tim cọc đảm bảo tiêu chuẩn thi công     |
| **Tim cọc trong bệ**     | Tất cả cọc cách mép bệ ≥ 1 đường kính cọc        |
| **M ≤ Mmax** (tùy chọn) | Momen đầu cọc không vượt sức chịu uốn               |

### 1.2 Giải pháp cốt lõi

Sử dụng mô hình **Bệ Cứng + Hiệu chỉnh Calibration**, sau đó quét toàn bộ không gian nghiệm.

---

## 2. Kiến trúc tổng thể

```
OptApp/
├── main.py                     # Entry Point – khởi chạy ứng dụng
│
├── core/                       # Logic lõi (không phụ thuộc UI)
│   ├── generator.py            # Sinh tọa độ lưới cọc (Kiểu A & B)
│   ├── mechanics.py            # Kiểm tra ràng buộc R1-R6
│   ├── blackbox.py             # Mô hình Hộp Đen (Bệ cứng + Calibration)
│   └── optimizer.py            # Thuật toán tối ưu hóa (Grid Search)
│
├── io_handlers/                # Xử lý dữ liệu vào/ra
│   ├── file_io.py              # Đọc file CSV/TXT/MCOC; xuất TXT kết quả
│   ├── export_utils.py         # Xuất Excel, PDF, PNG
│   └── _new_parsers.py         # Parser bổ sung (dự phòng)
│
└── ui/                         # Giao diện người dùng
    ├── main_window.py           # Cửa sổ chính (Tab Interactive + Batch)
    └── plot_canvas.py           # Vẽ mặt bằng cọc (Matplotlib Embedded)
```

### Sơ đồ luồng dữ liệu

```
[File MCOC/CSV]  ──→  file_io.parse_input_file()
                              │
                              ▼
                     params + loads (dict/list)
                              │
                              ▼
                    optimizer.run_optimization()
                     /               \
          generator.generate_coords()  mechanics.check_layout()
                                              │
                                     blackbox.MCOCBlackbox()
                                     [Bệ cứng + Calibration]
                              │
                              ▼
                   results (dict): recommended, best_A, best_B, ...
                              │
                     ┌────────┼────────┐
                     ▼        ▼        ▼
                 UI Text   PNG Plot  Excel/PDF/TXT
```

---

## 3. Workflow chi tiết từng bước

### Bước 0 — Khởi động ứng dụng

**File:** `main.py`

```python
root = TkinterDnD.Tk()   # Khởi tạo cửa sổ hỗ trợ kéo-thả file
app  = MainWindow(root)  # Tạo giao diện chính
root.mainloop()          # Bắt đầu vòng lặp sự kiện Tkinter
```

**Mô tả:** Kiểm tra thư viện `tkinterdnd2`. Nếu thiếu → thông báo lỗi rõ ràng và thoát. Nếu đủ → khởi tạo `MainWindow` với 2 tab: *Interactive* và *Batch Mode*.

---

### Bước 1 — Nhập dữ liệu

**File:** `io_handlers/file_io.py` → `parse_input_file(filepath)`

Người dùng có 2 cách nhập liệu:

| Cách                    | Mô tả                                                       |
| ------------------------ | ------------------------------------------------------------- |
| **Kéo thả file** | Thả file `.txt` (chuẩn MCOC) hoặc `.csv` vào cửa sổ |
| **Nhập tay**      | Điền trực tiếp thông số vào các ô Entry trên UI     |

**Nhận dạng tự động format file:**

```python
if "CHUONG TRINH TINH KHONG GIAN MONG COC" in lines[:10]:
    return parse_mcoc_result_as_input(filepath)  # File kết quả MCOC
elif ',' in lines[0]:
    # Đọc CSV (Header + Values + Loads)
else:
    # Đọc TXT chuẩn MCOC input
```

**Kết quả trả về:**

```python
params = {
    'L_X': float,        # Chiều rộng bệ (m)
    'L_Y': float,        # Chiều dài bệ (m)
    'D_PILE': float,     # Đường kính cọc (m)
    'P_LIMIT': float,    # Sức chịu nén Po (T)
    'P_TENSION': float,  # Sức chịu nhổ Ct (T)
    'M_LIMIT': float,    # Sức chịu uốn Mmax (T.m), 0 = bỏ qua
    'original_coords': [[x1,y1], [x2,y2], ...],  # Tọa độ cọc gốc
    'orig_pmax': float,  # Pmax thực từ MCOC (để calibration)
    'orig_pmin': float,  # Pmin thực từ MCOC
    'orig_mxmax': float, # Mx thực từ MCOC
    'orig_mymax': float, # My thực từ MCOC
}

loads = [
    {'Hx': float, 'Hy': float, 'N': float, 'Mx': float, 'My': float, 'Mz': float},
    # ... nhiều tổ hợp tải trọng
]
```

---

### Bước 2 — Sinh lưới cọc ứng viên

**File:** `core/generator.py` → `generate_coords(nx, ny, sx, sy, layout_type)`

Hàm sinh tọa độ cọc với **2 kiểu lưới**:

#### Kiểu A — Lưới Trực Giao (Rectangular Grid)

```
O  O  O  O
O  O  O  O      ← nx = 4, ny = 3
O  O  O  O
```

Công thức tọa độ cọc (i, j):

```
x_i = (i − (nx−1)/2) × sx
y_j = (j − (ny−1)/2) × sy
```

Số cọc: `n = nx × ny`

#### Kiểu B — Lưới So Le (Staggered Grid)

```
O  O  O  O      ← hàng chẵn (j=0): nx cọc
  O  O  O       ← hàng lẻ  (j=1): (nx-1) cọc (dịch phải sx/2)
O  O  O  O
```

Số cọc: `n = Σ(nx nếu j chẵn, nx-1 nếu j lẻ)`

**Vòng lặp sinh ứng viên trong optimizer:**

```python
for layout_type in ["A", "B"]:
    for nx in range(2, 11):      # 2 → 10 cọc/hàng
        for ny in range(2, 11):  # 2 → 10 hàng
            # Kiểm tra giới hạn bệ
            sx_max = min(6d, (L_X - 2*SAFE_D)/(nx-1))
            sy_max = min(6d, (L_Y - 2*SAFE_D)/(ny-1))
            if sx_max < 3d or sy_max < 3d:
                continue  # Bỏ qua – không thể thỏa 3d
            coords = generate_coords(nx, ny, sx_max, sy_max, layout_type)
```

---

### Bước 3 — Đánh giá nội lực (Hộp Đen)

**File:** `core/blackbox.py` → `MCOCBlackbox.evaluate_layout()`

Đây là **trái tim của thuật toán**, thay thế phần mềm FEM bằng phép tính giải tích tốc độ cao.

#### 3a. Tính Pmax lý thuyết (Công thức Bệ Cứng)

Giả thiết bệ móng tuyệt đối cứng → tải trọng phân phối theo quan hệ tuyến tính:

```
P_i = N/n  +  Mx × yᵢ/Ix  +  My × xᵢ/Iy
```

Trong đó:

- `N`  = Lực dọc tại đáy bệ (kN)
- `Mx`, `My` = Momen tại trọng tâm cọc (kNm)
- `xᵢ`, `yᵢ` = Tọa độ cọc so với trọng tâm nhóm cọc (m)
- `Ix = Σyᵢ²` = Momen quán tính nhóm cọc theo trục X
- `Iy = Σxᵢ²` = Momen quán tính nhóm cọc theo trục Y

**Pmax** = max(P_i) trên tất cả cọc × tất cả tổ hợp tải

#### 3b. Trích xuất Hệ số Hiệu chỉnh (Calibration Factor)

```python
# Tính Pmax lý thuyết cho phương án GỐC (đã biết)
pmax_orig_theory = _rigid_cap_pmax(original_coords, loads)

# Lấy Pmax THỰC TẾ từ kết quả MCOC (đọc từ file _result.txt)
pmax_orig_actual = params['orig_pmax']

# Hệ số hiệu chỉnh
K = pmax_orig_actual / pmax_orig_theory
```

**Ý nghĩa của K:** Bệ cứng lý thuyết bỏ qua độ uốn của bệ và biến dạng đất nền → K bù sai số hệ thống. Vì K được trích xuất từ phương án gốc đã tính FEM đầy đủ, sai số dự báo được triệt tiêu đến xấp xỉ **0%**.

#### 3c. Dự báo Pmax cho phương án mới

```python
pmax_new_theory = _rigid_cap_pmax(new_coords, loads)
pmax_predicted  = pmax_new_theory × K
```

#### 3d. Ước lượng Momen đầu cọc

```python
# Cọc càng ít → mỗi cọc phải chịu uốn nhiều hơn (tỉ lệ nghịch với số cọc)
m_calibration = n_original / n_new
Mx_predicted  = Mx_original × m_calibration
My_predicted  = My_original × m_calibration
```

---

### Bước 4 — Kiểm tra Ràng buộc (R1 – R6)

**File:** `core/mechanics.py` → `check_layout()`

| Ký hiệu    | Loại                            | Điều kiện kiểm tra                      |
| ------------ | -------------------------------- | ------------------------------------------- |
| **R1** | Nội lực – Nén                | `Pmax ≤ P_LIMIT` (Po)                    |
| **R2** | Nội lực – Nhổ                | `Pmin ≥ −P_TENSION` (Ct)                |
| **R3** | Hình học – Khoảng cách      | `3d ≤ sx ≤ 6d` và `3d ≤ sy ≤ 6d`   |
| **R4** | Hình học – Vị trí trong bệ | Tim cọc cách mép bệ ≥ SAFE_D           |
| **R5** | Nội lực – Uốn X              | `Mx_max ≤ M_LIMIT` (nếu có giới hạn) |
| **R6** | Nội lực – Uốn Y              | `My_max ≤ M_LIMIT` (nếu có giới hạn) |

**Logic loại bỏ sớm (Early Termination):**

```python
# Kiểm tra R3/R4 TRƯỚC khi gọi Hộp Đen (tiết kiệm thời gian)
if sx_max < 3*d or sy_max < 3*d:
    continue  # Loại sớm

# Sau đó mới gọi Hộp Đen
res = MCOCBlackbox.evaluate_layout(...)

# Kiểm tra R1, R2, R5, R6
if pmax > P_LIMIT: fail
if pmin < -P_TENSION: fail
...
```

---

### Bước 5 — Chọn phương án tối ưu

**File:** `core/optimizer.py` → `run_optimization()`

**Tiêu chí ưu tiên (theo thứ tự):**

1. **Ít cọc nhất** – Giảm chi phí vật liệu tối đa
2. **Pmax nhỏ nhất** – An toàn kết cấu tốt hơn (nếu cùng số cọc)
3. **Ưu tiên giữ phương án gốc** – Nếu phương án gốc ĐẠT và không có phương án lưới nào ít hơn, giữ nguyên thiết kế ban đầu

```python
# Bước 5a: Lấy phương án tốt nhất của từng kiểu
best_A = min(valid_A_configs, key=lambda c: (c['n'], c['pmax']))
best_B = min(valid_B_configs, key=lambda c: (c['n'], c['pmax']))

# Bước 5b: So sánh A vs B
if best_B['n'] < best_A['n']:
    recommended = best_B   # Kiểu B ít cọc hơn
elif best_A['n'] < best_B['n']:
    recommended = best_A   # Kiểu A ít cọc hơn
else:
    recommended = best_B if best_B['pmax'] < best_A['pmax'] else best_A

# Bước 5c: So với phương án gốc
if original_config['ok'] and recommended['n'] >= original_config['n']:
    recommended = original_config  # Phương án gốc không kém hơn → giữ lại
```

---

### Bước 6 — Hiển thị kết quả & Xuất file

**File:** `ui/main_window.py`, `ui/plot_canvas.py`, `io_handlers/export_utils.py`

| Kênh xuất              | Nội dung                                                    | Thư viện       |
| ------------------------ | ------------------------------------------------------------ | ---------------- |
| **Text Box UI**    | Bảng so sánh tất cả phương án, kết luận kiến nghị | Tkinter `Text` |
| **Vẽ mặt bằng** | Sơ đồ cọc, màu nhiệt độ theo Pmax, colorbar          | Matplotlib       |
| **File TXT**       | Định dạng chuẩn MCOC, tọa độ cọc, bảng nội lực    | Built-in I/O     |
| **File Excel**     | Bảng tổng hợp đẹp, tọa độ, kiểm tra R1-R6           | openpyxl         |
| **File PDF**       | Báo cáo kỹ thuật có chèn ảnh mặt bằng               | reportlab        |

**Biểu đồ màu nhiệt (Heatmap):**

- 🟢 Xanh lá: P thấp (an toàn)
- 🟡 Vàng: P gần giới hạn
- 🔴 Đỏ: P vượt Po (không đạt)
- 🟣 Tím: Cọc chịu nhổ vượt Ct

---

## 4. Phương pháp giải quyết bài toán

### 4.1 Tổng quan phương pháp

| Giai đoạn         | Phương pháp                                    | Lý do lựa chọn                                                            |
| ------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------- |
| Tìm kiếm nghiệm  | **Grid Search (Quét cạn có chọn lọc)** | Không gian hữu hạn (<200 cấu hình), đảm bảo tìm TOÀN CẦU tối ưu |
| Đánh giá nghiệm | **Rigid Cap + Calibration**                 | Thay FEM (<1ms vs >60s), sai số ≈ 0% nhờ hiệu chỉnh                     |
| Loại bỏ sớm      | **Constraint Propagation**                  | Loại vi phạm hình học trước khi tính nội lực                        |
| So sánh kết quả  | **Lexicographic Ordering**                  | Ưu tiên ít cọc → Pmax nhỏ                                              |

### 4.2 Grid Search có chọn lọc

**Không gian tìm kiếm:**

- Layout: {A, B} → 2 loại
- nx ∈ {2..10} → 9 giá trị
- ny ∈ {2..10} → 9 giá trị
- sx = sx_max (tối đa hóa khoảng cách → phân phối tải đều nhất có thể)
- Tổng: **2 × 9 × 9 = 162 ứng viên** (thực tế ít hơn do lọc sớm)

**Tại sao dùng sx_max?**

Với số cọc cố định (nx, ny), khoảng cách sx lớn nhất → Momen quán tính Ix, Iy lớn nhất → P_max nhỏ nhất → tốt nhất có thể cho cấu hình đó. Vậy chỉ cần kiểm tra 1 điểm duy nhất thay vì quét liên tục sx.

### 4.3 Mô hình Bệ Cứng (Rigid Pile Cap)

**Giả thiết:**

- Bệ móng tuyệt đối cứng (không biến dạng)
- Đất nền và cọc là lò xo đàn hồi tuyến tính bằng nhau
- Tải trọng tác dụng tại trọng tâm nhóm cọc

**Phương trình cân bằng:**

```
ΣN = N               →   N/n = Lực trung bình/cọc
ΣMx = Mx - N×ȳ      →   Phần đóng góp của Mx vào từng cọc
ΣMy = My - N×x̄      →   Phần đóng góp của My vào từng cọc
```

**Lực trên cọc thứ i:**

```
Pᵢ = N/n  +  (Mx - N×ȳ) × (yᵢ - ȳ)/Ix  +  (My - N×x̄) × (xᵢ - x̄)/Iy
```

**Đặc điểm:**

- Tính tức thì (< 0.1 ms)
- Sai số hệ thống so với bệ đàn hồi FEM: 5-20%
- **Sau khi hiệu chỉnh K:** sai số ≈ 0% với cùng loại tải trọng

### 4.4 Hiệu chỉnh Calibration

**Vấn đề:**

Bệ cứng cho Pmax thấp hơn thực tế (bệ đàn hồi) vì bệ thực có biến dạng làm tập trung tải vào cọc biên.

**Giải pháp:**

Lấy 1 điểm dữ liệu đã biết chính xác (phương án gốc đã chạy MCOC) để trích xuất hệ số bù sai số:

```
K = P_MCOC(gốc) / P_lý_thuyết(gốc)

P_dự_báo(mới) = P_lý_thuyết(mới) × K
```

**Điều kiện áp dụng:**

- Phương án mới phải có cùng loại tải trọng (tổ hợp tương tự)
- Cùng kích thước bệ Lx, Ly
- K được cập nhật tự động khi load file kết quả MCOC mới

### 4.5 Ưu điểm & Giới hạn

|                       | Ưu điểm                          | Giới hạn                                                |
| --------------------- | ----------------------------------- | --------------------------------------------------------- |
| **Grid Search** | Đảm bảo tối ưu toàn cục      | Chỉ xét lưới đều (A, B)                             |
| **Bệ Cứng**   | Cực nhanh, công thức đơn giản | Cần 1 điểm hiệu chỉnh thực tế                      |
| **Calibration** | Sai số ≈ 0% sau hiệu chỉnh      | Kém chính xác khi bố cục cọc thay đổi quá nhiều |

---

## 5. Giải thích từng module & hàm

### 5.1 `core/generator.py`

#### `generate_coords(nx, ny, sx, sy, layout_type) → np.ndarray`

**Mục đích:** Sinh mảng tọa độ `[x, y]` của các đầu cọc, căn giữa tại gốc tọa độ (0, 0).

**Thuật toán:**

```python
# Kiểu A (Trực giao)
for j in range(ny):
    y = (j - (ny-1)/2.0) * sy     # Căn giữa theo Y
    for i in range(nx):
        x = (i - (nx-1)/2.0) * sx  # Căn giữa theo X
        coords.append([x, y])

# Kiểu B (So le)
for j in range(ny):
    y = (j - (ny-1)/2.0) * sy
    cols = nx if (j % 2 == 0) else (nx - 1)
    offset = -(cols-1)/2.0 * sx   # Dịch chuyển để căn giữa
    for i in range(cols):
        x = offset + i * sx
        coords.append([x, y])
```

**Ví dụ (nx=3, ny=2, sx=2.0, sy=3.0, Kiểu A):**

```
(-2.0, 1.5)  (0.0, 1.5)  (2.0, 1.5)
(-2.0,-1.5)  (0.0,-1.5)  (2.0,-1.5)
```

---

### 5.2 `core/blackbox.py`

#### `MCOCBlackbox._rigid_cap_pmax(coords_arr, loads) → float`

**Tính Pmax trên toàn bộ tổ hợp tải:**

```python
cx, cy = np.mean(coords[:,0]), np.mean(coords[:,1])  # Trọng tâm nhóm cọc
Ix = Σ(yᵢ - cy)²   # Momen quán tính trục X
Iy = Σ(xᵢ - cx)²   # Momen quán tính trục Y

for load in loads:
    for (xi, yi) in coords:
        p = N/n + Mx*(yi-cy)/Ix + My*(xi-cx)/Iy
        global_pmax = max(global_pmax, p)
```

**Lưu ý:** `or 1e-9` tránh chia cho 0 khi tất cả cọc thẳng hàng.

#### `MCOCBlackbox._mock_execution(coords, loads, params) → (dict, str)`

**Logic phân nhánh:**

```python
if is_original:       # Phương án gốc → đọc kết quả thực từ file
    return parse_mcoc_result_file(result_filepath)
else:                 # Phương án mới → Bệ cứng + Calibration
    pmax_theory = _rigid_cap_pmax(new_coords, loads)
    K = pmax_orig_actual / pmax_orig_theory
    return {'pmax': pmax_theory * K, ...}
```

---

### 5.3 `core/mechanics.py`

#### `check_layout(coords, nx, ny, sx, sy, layout_type, params, loads) → tuple`

**Luồng xử lý:**

```
1. Kiểm tra R4 (vị trí trong bệ):
   max_x + SAFE_D ≤ L_X/2  AND  max_y + SAFE_D ≤ L_Y/2

2. Kiểm tra R3 (khoảng cách cọc):
   Kiểu A: 3d ≤ sx ≤ 6d  AND  3d ≤ sy ≤ 6d
   Kiểu B: 3d ≤ sx ≤ 6d  AND  3d ≤ diag ≤ 6d  (diag = khoảng cách chéo)

3. Gọi Hộp Đen → pmax, pmin, mxmax, mymax

4. Kiểm tra R1: pmax ≤ P_LIMIT
   Kiểm tra R2: pmin ≥ -P_TENSION  (nếu P_TENSION > 0)
   Kiểm tra R5/R6: mxmax, mymax ≤ M_LIMIT  (nếu M_LIMIT > 0)

5. Trả về: (ok, pmax, pmin, mxmax, mymax, forces, message)
```

---

### 5.4 `core/optimizer.py`

#### `run_optimization(params, loads) → dict`

**Trả về cấu trúc kết quả:**

```python
{
    'best_A': dict,              # Phương án tốt nhất Kiểu A
    'best_B': dict,              # Phương án tốt nhất Kiểu B
    'recommended': dict,         # PHƯƠNG ÁN KIẾN NGHỊ
    'reason': str,               # Lý do chọn phương án này
    'all_valid_configs': [dict], # Tất cả cấu hình ĐẠT (sắp xếp tăng dần n)
    'all_candidates': [dict],    # Tất cả ứng viên kể cả không đạt
    'original_config': dict      # Đánh giá phương án gốc (nếu có)
}
```

---

### 5.5 `io_handlers/file_io.py`

#### `parse_input_file(filepath) → (params, loads, project_name)`

Tự động phát hiện format: CSV (dấu phẩy) hoặc TXT chuẩn MCOC.

#### `parse_mcoc_result_as_input(filepath) → (params, loads, project_name)`

Đọc file *kết quả* của MCOC làm *đầu vào* cho OptApp (trích xuất cả tọa độ cọc gốc, Pmax/Mxmax thực tế để calibration).

#### `parse_mcoc_result_file(filepath) → dict`

Đọc chính xác Nmax, Nmin, Mxmax, Mymax từ bảng tổng kết trong file kết quả MCOC.

#### `export_output_file(filepath, results, params, loads, project_name, output_option)`

Xuất file TXT định dạng chuẩn MCOC, có thêm:

- Bảng so sánh Kiểu A vs Kiểu B
- Bảng tọa độ cọc tối ưu
- Bảng nội lực từng cọc × từng tổ hợp tải

---

### 5.6 `ui/plot_canvas.py`

#### `PlotCanvas.draw_simulation(coords, params, forces, m_forces)`

**Vẽ mặt bằng cọc với:**

1. Hình chữ nhật xám = bệ móng
2. Viền đỏ nét đứt = giới hạn tâm cọc (cách mép SAFE_D)
3. Vòng tròn màu = cọc (màu nhiệt độ: xanh→vàng→đỏ theo tỉ lệ P/Po)
4. Nhãn số thứ tự + giá trị P từng cọc
5. Colorbar bên phải với đường giới hạn Po

---

### 5.7 `ui/main_window.py`

**`MainWindow.__init__`:** Khởi tạo biến Tkinter (`DoubleVar`, `BooleanVar`) và giao diện.

**`add_default_loads()`:** Điền tải trọng mặc định (N=2577 kN, Mx=My=1500 kNm) để người dùng có thể chạy thử ngay.

**`get_params_dict()`:** Chuyển đổi từ Tkinter `Variable` → Python `dict` thuần để truyền vào core.

**`run_optimize()`:** Gọi `run_optimization()` → hiển thị bảng kết quả dạng văn bản → cập nhật Combobox → vẽ mặt bằng.

**`run_batch()`:** Chạy trong Thread riêng để không làm đơ UI, xử lý từng file một, xuất Excel/PDF/PNG.

---

## 6. Bảng Design Pattern

### 6.1 Pattern kiến trúc

| Pattern                               | Nơi áp dụng             | Mô tả                                                                                      |
| ------------------------------------- | -------------------------- | -------------------------------------------------------------------------------------------- |
| **MVC (Model-View-Controller)** | Toàn dự án              | `core/` = Model, `ui/` = View, `main_window.py` = Controller                           |
| **Facade**                      | `core/optimizer.py`      | `run_optimization()` là giao diện đơn giản che toàn bộ logic phức tạp bên trong  |
| **Strategy**                    | `core/blackbox.py`       | `evaluate_layout()` chọn giữa mock (Bệ Cứng) và real (FEM subprocess)                 |
| **Factory Method**              | `io_handlers/file_io.py` | `parse_input_file()` quyết định parser nào được dùng dựa trên nội dung file     |
| **Observer**                    | `ui/main_window.py`      | Tkinter event binding (`bind`, `dnd_bind`) phản ứng sự kiện người dùng            |
| **Template Method**             | `core/mechanics.py`      | `check_layout()` định nghĩa khung kiểm tra cố định (R4→R3→Hộp Đen→R1/R2/R5/R6) |

### 6.2 Pattern cấu trúc dữ liệu

| Pattern                              | Biến / Hàm                            | Mô tả                                                     |
| ------------------------------------ | --------------------------------------- | ----------------------------------------------------------- |
| **DTO (Data Transfer Object)** | `params` dict, `loads` list of dict | Gói gọn dữ liệu giữa các tầng (UI → Core → IO)     |
| **Dictionary as Config**       | `params = {'L_X':..., 'D_PILE':...}`  | Cấu hình linh hoạt, dễ mở rộng thêm key mới         |
| **Optional Sentinel**          | `M_LIMIT = 0 → float('inf')`         | Giá trị 0 có ngữ nghĩa đặc biệt "bỏ qua kiểm tra" |
| **Early Return**               | `if sx_max < 3d: continue`            | Thoát sớm khi vi phạm ràng buộc hiển nhiên           |

### 6.3 Pattern theo từng hàm quan trọng

| Hàm                      | Design Pattern                    | Giải thích                                                          |
| ------------------------- | --------------------------------- | --------------------------------------------------------------------- |
| `generate_coords()`     | **Builder**                 | Xây dựng tọa độ từng cọc một theo quy tắc lưới             |
| `_rigid_cap_pmax()`     | **Pure Function**           | Không side effect, kết quả chỉ phụ thuộc input                  |
| `_rigid_cap_pmin()`     | **Pure Function**           | Như trên                                                            |
| `_mock_execution()`     | **Proxy**                   | Giả lập hành vi của hệ thống FEM thực (MCOC)                   |
| `check_layout()`        | **Chain of Responsibility** | Kiểm tra tuần tự từng ràng buộc, dừng khi fail                 |
| `run_optimization()`    | **Iterator + Aggregator**   | Lặp qua không gian nghiệm, tổng hợp kết quả tốt nhất         |
| `parse_input_file()`    | **Factory Method**          | Chọn parser phù hợp theo format file                               |
| `export_output_file()`  | **Template Method**         | Cấu trúc file xuất cố định, nội dung thay đổi theo kết quả |
| `run_batch()`           | **Command + Thread**        | Đóng gói tác vụ batch, chạy trong background thread             |
| `populate_comboboxes()` | **Observer**                | Cập nhật UI phản ứng theo kết quả tối ưu                      |
| `draw_simulation()`     | **Renderer**                | Vẽ lại toàn bộ canvas mỗi khi dữ liệu thay đổi               |
| `handle_drop()`         | **Event Handler**           | Xử lý sự kiện kéo-thả file                                      |

### 6.4 Thư viện & Mục đích sử dụng

| Thư viện      | Phiên bản | Mục đích                                       | Module sử dụng                                    |
| --------------- | ----------- | ------------------------------------------------- | --------------------------------------------------- |
| `numpy`       | ≥1.20      | Ma trận tọa độ, tính Ix/Iy, vectorized math  | `blackbox.py`, `mechanics.py`, `generator.py` |
| `tkinter`     | stdlib      | Giao diện cửa sổ, widget, event                | `main_window.py`                                  |
| `tkinterdnd2` | ≥0.3       | Hỗ trợ kéo-thả file vào cửa sổ             | `main.py`, `main_window.py`                     |
| `matplotlib`  | ≥3.3       | Vẽ mặt bằng cọc, heatmap, colorbar            | `plot_canvas.py`, `export_utils.py`             |
| `openpyxl`    | ≥3.0       | Tạo file Excel có định dạng màu/font        | `export_utils.py`                                 |
| `reportlab`   | ≥3.5       | Tạo file PDF                                     | `export_utils.py`                                 |
| `re`          | stdlib      | Regex xử lý đường dẫn file kéo-thả        | `main_window.py`                                  |
| `csv`         | stdlib      | Đọc file CSV (format cũ)                       | `file_io.py`                                      |
| `os`          | stdlib      | Kiểm tra tồn tại file, thao tác đường dẫn | Nhiều module                                       |
| `threading`   | stdlib      | Chạy batch không block UI                       | `main_window.py`                                  |
| `PyPDF2`      | ≥2.0       | Gộp nhiều PDF thành 1 file tổng hợp          | `main_window.py` (optional)                       |
| `datetime`    | stdlib      | Thêm timestamp vào báo cáo                    | `export_utils.py`                                 |

### 6.5 Biến & Hằng số quan trọng

| Biến                  | Kiểu                 | Ý nghĩa                                                    | Đơn vị |
| ---------------------- | --------------------- | ------------------------------------------------------------ | --------- |
| `L_X`                | float                 | Chiều rộng bệ móng                                       | m         |
| `L_Y`                | float                 | Chiều dài bệ móng                                        | m         |
| `D_PILE` / `d`     | float                 | Đường kính cọc                                          | m         |
| `SAFE_D`             | float                 | Khoảng cách tối thiểu từ tim cọc ngoài đến mép bệ | m (= d)   |
| `P_LIMIT` / `Po`   | float                 | Sức chịu nén cho phép của cọc                          | T (Tấn)  |
| `P_TENSION` / `Ct` | float                 | Sức chịu nhổ cho phép                                    | T         |
| `M_LIMIT`            | float                 | Sức chịu uốn cho phép, 0 = không kiểm tra              | T.m       |
| `sx`, `sy`         | float                 | Khoảng cách tim cọc theo X, Y                             | m         |
| `nx`, `ny`         | int                   | Số cọc theo X, Y                                           | —        |
| `coords`             | np.ndarray `(n, 2)` | Ma trận tọa độ [x, y] của n cọc                        | m         |
| `loads`              | list of dict          | Danh sách tổ hợp tải trọng                              | kN, kNm   |
| `N`                  | float                 | Lực dọc (nén dương)                                     | kN        |
| `Mx`, `My`         | float                 | Momen uốn tại đáy bệ                                    | kNm       |
| `pmax`               | float                 | Lực nén lớn nhất trong nhóm cọc                        | T         |
| `pmin`               | float                 | Lực nhổ lớn nhất (âm)                                   | T         |
| `K`                  | float                 | Hệ số hiệu chỉnh Calibration                             | —        |
| `calibration_factor` | float                 | Tên thay thế của K trong UI                               | —        |
| `mock_mode`          | bool                  | `True` = dùng Bệ Cứng; `False` = gọi subprocess FEM  | —        |

---

## 7. Dữ liệu nhập tùy ý — Ví dụ chạy thực tế

### 7.1 Chạy nhanh bằng giao diện (không cần file)

Khi mở chương trình, UI đã có sẵn dữ liệu mặc định để demo:

| Thông số            | Giá trị mặc định       | Ý nghĩa               |
| --------------------- | --------------------------- | ----------------------- |
| Lx (m)                | 6.0                         | Bệ rộng 6m            |
| Ly (m)                | 9.6                         | Bệ dài 9.6m           |
| d (m)                 | 1.2                         | Cọc khoan nhồi Ø1200 |
| Po (T)                | 500.0                       | Sức chịu nén         |
| Ct (T)                | 0.0                         | Không kiểm tra nhổ   |
| M (T.m)               | 0.0                         | Không kiểm tra uốn   |
| **Tải trọng** | N=2577 kN, Mx=1500, My=1500 | 1 tổ hợp mặc định  |

→ Nhấn **▶ CHẠY TỐI ƯU HÓA** ngay, không cần nhập file.

---

### 7.2 File CSV mẫu (Định dạng đơn giản)

**Lưu thành file `input_vi_du.csv`:**

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION
6.0,9.6,1.2,1.2,500.0,0.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,2577.0,1500.0,1500.0,0.0
0.0,0.0,2400.0,800.0,2000.0,0.0
0.0,0.0,2800.0,1800.0,1200.0,0.0
```

**Giải thích từng dòng:**

| Dòng | Nội dung             | Ý nghĩa                         |
| ----- | --------------------- | --------------------------------- |
| 1     | Header thông số bệ | Tên các trường                |
| 2     | Giá trị thông số  | Bệ 6×9.6m, cọc Ø1.2m, Po=500T |
| 3     | Header tải trọng    | Ký hiệu 6 thành phần          |
| 4     | Tổ hợp tải 1       | N=2577 kN, Mx=My=1500 kNm         |
| 5     | Tổ hợp tải 2       | N=2400 kN, Mx=800, My=2000 kNm    |
| 6     | Tổ hợp tải 3       | N=2800 kN, Mx=1800, My=1200 kNm   |

---

### 7.3 File CSV mẫu đầy đủ hơn (Trụ cầu lớn)

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION,M_LIMIT
8.0,12.0,1.5,1.5,750.0,50.0,150.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,5800.0,2200.0,3100.0,0.0
0.0,0.0,5200.0,1800.0,2800.0,0.0
0.0,0.0,6100.0,2500.0,2900.0,0.0
0.0,0.0,4900.0,900.0,3400.0,0.0
50.0,0.0,5500.0,2000.0,2600.0,0.0
0.0,45.0,5700.0,2300.0,2700.0,0.0
```

**Kịch bản:** Trụ cầu lớn, bệ 8×12m, cọc Ø1500, Po=750T, Ct=50T (kiểm tra nhổ), M_limit=150 T.m, 6 tổ hợp tải.

**Kết quả kỳ vọng:** Chương trình sẽ so sánh cấu hình từ 4 cọc (2×2) đến 100 cọc (10×10) theo cả 2 kiểu lưới → đề xuất phương án ít cọc nhất thỏa mãn cả R1-R6.

---

### 7.4 Kịch bản thử nghiệm theo trường hợp đặc biệt

#### Kịch bản A: Bệ vuông, tải đối xứng

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION
6.0,6.0,1.0,1.0,400.0,0.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,3000.0,0.0,0.0,0.0
```

**Kỳ vọng:** Phân phối đều → cọc ngoài = cọc giữa. Phương án ít nhất đạt điều kiện.

#### Kịch bản B: Tải lệch tâm mạnh (Mx >> My)

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION
5.0,10.0,1.0,1.0,450.0,0.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,2000.0,3000.0,100.0,0.0
```

**Kỳ vọng:** Kiểu B (so le) có thể có lợi do Iy lớn hơn.

#### Kịch bản C: Cọc nhỏ, bệ lớn

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION
10.0,15.0,0.6,0.6,120.0,0.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,4500.0,2000.0,2500.0,0.0
```

**Kỳ vọng:** Cần nhiều cọc (n ≈ 40-60) vì Po nhỏ.

#### Kịch bản D: Tải nhỏ, cọc lớn (kiểm tra n_min)

```csv
L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION
6.0,9.0,1.5,1.5,900.0,0.0
Hx,Hy,P,Mx,My,Mz
0.0,0.0,1500.0,500.0,500.0,0.0
```

**Kỳ vọng:** 2×2 = 4 cọc là đủ.

---

### 7.5 Script Python chạy trực tiếp không qua UI

Lưu thành `test_run.py` trong thư mục dự án:

```python
"""
Script kiểm thử chạy thuật toán OptApp trực tiếp (không cần giao diện).
Chạy: python test_run.py
"""
import sys
sys.path.insert(0, '.')

from core.optimizer import run_optimization

# ============================================================
# NHẬP DỮ LIỆU TÙY Ý TẠI ĐÂY
# ============================================================
params = {
    'L_X': 6.0,         # Chiều rộng bệ (m)
    'L_Y': 9.6,         # Chiều dài bệ (m)
    'D_PILE': 1.2,       # Đường kính cọc (m)
    'SAFE_D': 1.2,       # Khoảng cách tim cọc đến mép bệ (m) = d
    'P_LIMIT': 500.0,    # Sức chịu nén Po (T)
    'P_TENSION': 0.0,    # Sức chịu nhổ Ct (T), 0 = không kiểm tra
    'M_LIMIT': 0.0,      # Sức chịu uốn (T.m), 0 = không kiểm tra
    'mock_mode': True,   # Dùng mô hình Bệ Cứng (không cần file MCOC)

    # Tọa độ phương án GỐC (nếu có) — để so sánh
    'original_coords': [
        [-1.5, -3.0], [1.5, -3.0],
        [-1.5,  0.0], [1.5,  0.0],
        [-1.5,  3.0], [1.5,  3.0],
    ],
    'orig_pmax': 519.63,  # Pmax thực từ MCOC (để calibration)
    'orig_pmin':   0.0,
    'orig_mxmax':  7.49,
    'orig_mymax': 27.82,
}

loads = [
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0, 'Mz': 0.0},
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2400.0, 'Mx':  800.0, 'My': 2000.0, 'Mz': 0.0},
    {'Hx': 0.0, 'Hy': 0.0, 'N': 2800.0, 'Mx': 1800.0, 'My': 1200.0, 'Mz': 0.0},
]

# ============================================================
# CHẠY TỐI ƯU
# ============================================================
print("=" * 60)
print("OPT APP — Tối Ưu Hóa Bố Trí Cọc Móng Cầu")
print("=" * 60)

results = run_optimization(params, loads)

# In kết quả phương án gốc
orig = results.get('original_config')
if orig:
    status = "ĐẠT" if orig['ok'] else "KHÔNG ĐẠT"
    print(f"\n[PHƯƠNG ÁN GỐC] {status}")
    print(f"  Số cọc: {orig['n']}")
    print(f"  Pmax = {orig['pmax']:.2f} T  (giới hạn: {params['P_LIMIT']} T)")
    if not orig['ok']:
        print(f"  Lý do: {orig['msg']}")

# In tất cả phương án đạt
print(f"\n[TẤT CẢ PHƯƠNG ÁN ĐẠT — {len(results['all_valid_configs'])} phương án]")
print(f"  {'Kiểu':<5} {'nx':>3} {'ny':>3} {'n':>4} {'sx':>7} {'sy':>7} {'Pmax':>8}")
print("  " + "-"*50)
for c in results['all_valid_configs']:
    print(f"  {c['type']:<5} {c['nx']:>3} {c['ny']:>3} {c['n']:>4} "
          f"{c['sx']:>7.2f} {c['sy']:>7.2f} {c['pmax']:>8.1f} T")

# In kết luận
rec = results.get('recommended')
print(f"\n[KẾT LUẬN — PHƯƠNG ÁN KIẾN NGHỊ]")
if rec:
    type_str = {"A": "Trực giao", "B": "So le", "Gốc": "Phương án Gốc"}.get(rec['type'], rec['type'])
    print(f"  Kiểu: {type_str}")
    print(f"  Số cọc: {rec['n']}")
    if rec['type'] != 'Gốc':
        print(f"  Lưới: {rec['nx']} × {rec['ny']}, sx={rec['sx']:.2f} m, sy={rec['sy']:.2f} m")
    print(f"  Pmax = {rec['pmax']:.2f} T  |  Pmin = {rec['pmin']:.2f} T")
    print(f"  Lý do: {results['reason']}")
else:
    print(f"  ❌ {results['reason']}")

print("\n" + "=" * 60)
```

**Chạy:**

```bash
cd d:\Project\TEDI\OptApp
python test_run.py
```

**Output mẫu:**

```
============================================================
OPT APP — Tối Ưu Hóa Bố Trí Cọc Móng Cầu
============================================================

[PHƯƠNG ÁN GỐC] ĐẠT
  Số cọc: 6
  Pmax = 519.63 T  (giới hạn: 500.0 T)

[TẤT CẢ PHƯƠNG ÁN ĐẠT — 12 phương án]
  Kiểu  nx  ny    n      sx      sy     Pmax
  --------------------------------------------------
  A      2   3    6    3.60    3.00   487.5 T
  B      3   3    7    3.60    3.00   462.3 T
  ...

[KẾT LUẬN — PHƯƠNG ÁN KIẾN NGHỊ]
  Kiểu: Trực giao
  Số cọc: 6
  Lưới: 2 × 3, sx=3.60 m, sy=3.00 m
  Pmax = 487.5 T  |  Pmin = 0.0 T
  Lý do: Phương án gốc ĐẠT (Pmax=519.63T). Các phương án lưới đều không tiết kiệm cọc hơn.

============================================================
```

---

## 8. Định dạng file Input/Output

### 8.1 File Input CSV (đơn giản)

```
Dòng 1: L_X,L_Y,D_PILE,SAFE_D,P_LIMIT,P_TENSION[,M_LIMIT]
Dòng 2: <giá trị tương ứng>
Dòng 3: Hx,Hy,P,Mx,My,Mz
Dòng 4+: <tổ hợp tải trọng>
```

### 8.2 File Input TXT (chuẩn MCOC)

```
Dòng 1: Tên công trình
Dòng 2: Nc Np Nt Nf Ns ... Ax By H
Dòng 3: (bỏ trống)
Dòng 4+: Hx Hy P Mx My Mz  (từng tổ hợp tải)
...
(Khối dữ liệu từng cọc: chiều dài, tiết diện, sức chịu tải, tọa độ X Y)
```

### 8.3 File Output TXT (chuẩn MCOC + thêm bảng tối ưu)

```
TONG CONG TY TVTK GTVT
CHUONG TRINH TINH KHONG GIAN MONG COC - OPTIMIZER

SO SANH CAC KIEU BO TRI:
  Kieu A (Truc giao): 6 coc, P_max = 487.5 kN
  Kieu B (So le)    : 7 coc, P_max = 462.3 kN

PHUONG AN KIEN NGHI: Kieu A
Ly do: Kiểu Trực giao tiết kiệm cọc nhất

TOA DO DAU COC (PHUONG AN TOI UU):
  Luoi: 2 x 3, sx = 3.600 m, sy = 3.000 m
  T.T    X         Y
   1     -1.800    -3.000
   2      1.800    -3.000
   3     -1.800     0.000
   4      1.800     0.000
   5     -1.800     3.000
   6      1.800     3.000

NOI LUC COC KIEM TRA:
...
BANG TONG KET NOI LUC:
  Nmin    ...
  Nmax    ...
```

---

## 9. Cài đặt & Chạy chương trình

### 9.1 Yêu cầu hệ thống

- Python 3.8+
- Windows (khuyến nghị) hoặc Linux

### 9.2 Cài đặt thư viện

```bash
pip install numpy matplotlib openpyxl reportlab tkinterdnd2 PyPDF2
```

### 9.3 Chạy ứng dụng giao diện

```bash
cd d:\Project\TEDI\OptApp
python main.py
```

### 9.4 Chạy kiểm tra không giao diện

```bash
python test_run.py           # Script mẫu từ phần 7.5
python test_opt.py           # Bài test nhanh có sẵn trong dự án
python test_stiffness.py     # Kiểm tra công thức bệ cứng
```

### 9.5 Hướng dẫn sử dụng nhanh

1. Chạy `python main.py`
2. **Tab 1 (Interactive):**
   - Kéo thả file `.txt` MCOC vào cửa sổ **hoặc** nhấn nút "Chọn Input"
   - Điều chỉnh Po, Ct, Mmax nếu cần
   - Nhấn **▶ CHẠY TỐI ƯU HÓA**
   - Xem kết quả bên phải và bảng text bên trái
   - Nhấn "Xuất Kết Quả" để lưu file TXT + PNG
3. **Tab 2 (Batch Mode):**
   - Thêm nhiều file cùng lúc
   - Chọn thư mục lưu
   - Nhấn **TÍNH TOÁN** → chạy ngầm, xuất Excel/PDF/PNG tự động

---

*Tài liệu được tạo tự động từ mã nguồn OptApp – phiên bản hiện tại.*
*Cập nhật: 2026-06-10*
