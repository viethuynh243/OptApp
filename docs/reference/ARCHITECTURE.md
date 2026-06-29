# Kiến trúc & phương pháp — OptApp

> **Mã:** OA-DOC-01 · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved
> **Căn cứ:** `core/`, `core/ext/`, `io_handlers/`, `ui/`, `core/version.py` (v1.10.0).
> Tổng hợp & thay thế vault Obsidian cũ. Mô tả **trạng thái thực tế của code** (cơ sở
> TCVN 10304:2014). Định hướng chuyển sang TCVN 11823:2017: xem [ADR-008](adr/ADR-008-co-so-thiet-ke-tcvn-11823.md).

OptApp tìm **bố trí cọc tối ưu** (số cọc ít / vật liệu rẻ) trên bệ chữ nhật, thỏa
mọi ràng buộc kỹ thuật, với nội lực **chấm bắt buộc bằng MCOC (chính xác)** và tối
ưu bằng **NSGA-II**. Bản mở rộng còn bật R7/R8, đổi đường kính cọc và thu bệ vừa khít.

---

## Bài toán & mô hình

**Mục tiêu:** tìm bố trí cọc tối ưu cùng vị trí từng cọc, thỏa mọi [ràng buộc
R1–R8](#ràng-buộc-r1r8), trên bệ `Lx × Ly`.

**Biến quyết định (genome)** `(type, nx, ny, sx, sy)`:
- `type ∈ {A trực giao, B hoa mai/so le}` — rời rạc.
- `nx, ny` — số cột/hàng, rời rạc.
- `sx, sy ∈ [3d, 6d]` — bước lưới, liên tục.
- Tọa độ luôn **đối xứng quanh tâm bệ** (`cx = cy = 0`).
- Bản mở rộng thêm **đường kính `d`** thành biến (quét theo bảng) — xem
  [ADR-006](adr/ADR-006-duong-kinh-coc-bien-toi-uu.md).

**Hai mục tiêu (đều cực tiểu) → mặt Pareto:**
- `f1` = số cọc (tiết kiệm vật liệu/thi công).
- `f2` = bệ gọn (footprint, mặc định) **hoặc** Pmax (an toàn) — chọn qua `secondary`.

Lời giải là **mặt Pareto** (tập không bị trội), không phải một điểm.

**Đánh giá nội lực — bắt buộc MCOC.** Mỗi phương án chấm bằng `MCOC_Batch.exe`
(oracle duy nhất, [ADR-001](adr/ADR-001-mcoc-oracle-duy-nhat.md)). Mô hình **bệ
cứng** ([`core/rigid_cap.py`](../../core/rigid_cap.py)) chỉ dẫn hướng nội bộ +
heatmap, không phải kết quả giao nộp:

```
P_i = N/n + (Mx − N·cy)(y_i − cy)/Ix + (My − N·cx)(x_i − cx)/Iy
```

(dời mômen về trọng tâm — đúng cả khi tâm lệch, ví dụ Kiểu B `ny` chẵn).

---

## Thuật toán NSGA-II

Engine chính ([`core/nsga2_optimizer.py`](../../core/nsga2_optimizer.py)) — di truyền
đa mục tiêu (Deb et al. 2002), xem [ADR-002](adr/ADR-002-chon-nsga2.md).

**4 thành phần cốt lõi:**
1. Fast non-dominated sorting → xếp hạng Pareto (rank).
2. Crowding distance → giữ đa dạng trên mặt Pareto.
3. Crowded-comparison tournament → chọn lọc.
4. SBX crossover + polynomial mutation + elitism (μ+λ).

**Xử lý ràng buộc — constrained-domination:** khả thi **>** bất khả thi; 2 bất khả
thi → `cv` (Constraint Violation) nhỏ hơn trội hơn; 2 khả thi → so Pareto trên mục tiêu.

**Chính xác bắt buộc nhưng vẫn nhanh.** Tốc độ KHÔNG từ xấp xỉ mà từ **giảm số lần
gọi MCOC** + **song song**: (1) cache theo lưới (không gọi trùng); (2) trần
`max_evals` (≈50); (3) predictor bệ cứng xếp thứ tự gửi MCOC; (4) song song hóa
*(backlog [O1](../project/BACKLOG.md))*; (5) cache bền *(backlog)*. Một lần gọi
≈ 0,1–1 s; mặc định ≤50 lần ≈ 50 s (song song 8 lõi ≈ 7 s).

**Số neo kiểm thử (oracle hồi quy):**
- `tests/test_nsga2.py` → Kiểu A 2×3, 6 cọc, **Pmax = 486,91 T**.
- `tests/test_refine.py` → 8 cọc, **Pmax = 408,34 T**.
- `tests/test_nsga2_mcoc.py` → 8 cọc, **Pmax = 398,80 T**, **25 lần gọi MCOC**.

---

## Ràng buộc R1–R8

Kiểm trong [`core/mechanics.py`](../../core/mechanics.py)`::check_layout` (gom lỗi,
không dừng ở lỗi đầu) và `core/nsga2_optimizer.py::evaluate` (chuẩn hóa thành CV).
`d` = đường kính cọc; `SAFE_D` = khoảng cách an toàn tới mép (mặc định = d).

| Mã | Ràng buộc | Ghi chú |
|---|---|---|
| **R1** | có ≥ 1 cọc | tiền đề |
| **R2** | có ≥ 1 tổ hợp tải | tiền đề |
| **R3** | `s_min ≤ s ≤ 6d`, `s_min = max(3d, d + thông thủy)` | Kiểu B xét **đường chéo** `√((sx/2)² + sy²)` |
| **R4** | cọc trong bệ: `max\|x\| + SAFE_D ≤ Lx/2` (và theo Y) | TCVN cấu tạo (Điều 8) |
| **R5** | `Pmax ≤ [Po]` | nén |
| **R5b** | `Pmin ≥ −[Ct]` (khi `[Ct] > 0`) | nhổ |
| **R6** | `Mx, My ≤ [M]` (khi `[M] > 0`) | uốn; mock heuristic kém tin cậy |
| **R7** | `Hmax ≤ [H]` (khi `[H] > 0`) | lực ngang — **mặc định TẮT ở lõi** |
| **R8** | `Pmax/[Po] + max(Mx,My)/[M] ≤ 1` | tương tác P–M — **mặc định TẮT ở lõi** |

**R7 / R8 — trạng thái:**
- **Lõi:** `ENABLE_LATERAL_CHECK=False`, `ENABLE_PM_INTERACTION=False`
  ([`core/constants.py`](../../core/constants.py)). Lý do: [ADR-003](adr/ADR-003-tat-r7-r8-o-loi.md).
- **Bản mở rộng:** **BẬT** cả R7 và R8 qua context manager, không sửa lõi —
  [ADR-005](adr/ADR-005-bat-r7-r8-trong-ext.md).

> **Cơ chế CV:** mỗi vi phạm cộng vào `cv` đã chuẩn hóa (ví dụ
> `max(0, Pmax − [Po]) / [Po]`); `ok = (cv ≈ 0)`.

---

## Luồng MCOC (đánh giá chính xác)

Tab 1 (Tương tác) và Tab 2 (Hàng loạt) dùng **cùng** luồng:

```
file input MCOC + tham số UI
   → nsga2_optimizer.run_nsga2()
   → evaluator = MCOCBlackbox.make_real_evaluator()
   → mcoc_writer (sinh input) → MCOC_Batch.exe → *_result.txt   [EXACT]
   → recommended + pareto_front
```

**Định dạng file input MCOC.** Mỗi *khối cọc* nhúng đặc trưng tiết diện: đường
kính `Bpx/Bpy` (= d), `Fo = π·d²/4` (diện tích), `Jo = π·d⁴/64` (mômen quán tính),
`Po` (sức chịu nén cho phép), tọa độ `X, Y`. Nhờ đó **đổi đường kính** = patch các
trường này (dò bằng **khớp giá trị gốc**, không hardcode offset).

**Gọi tiến trình (chạy ngầm).** [`core/mcoc_runner.py`](../../core/mcoc_runner.py)
gọi `MCOC_Batch.exe` (`.exe/.bat/.py/.lnk`) bằng subprocess, **không bật cửa sổ
cmd** (`CREATE_NO_WINDOW` + `STARTUPINFO`/SW_HIDE).

---

## Bản đồ module

### Engine
| Engine | File | Vai trò |
|---|---|---|
| **NSGA-II** | `core/nsga2_optimizer.py` | **Chính** — di truyền đa mục tiêu + MCOC exact |
| Refine | `core/refine_optimizer.py` | Tinh chỉnh Pareto *dự báo → kiểm chứng MCOC → hiệu chỉnh*; rất ít lần gọi MCOC |
| Quét lưới | `core/optimizer.py` | Bệ cứng (xấp xỉ) — **chỉ cho `run_demo.py`** ([ADR-004](adr/ADR-004-batch-theo-mcoc.md)) |

### Module lõi
| Module | Vai trò |
|---|---|
| `core/rigid_cap.py` | **Nguồn duy nhất** công thức bệ cứng (lực dọc dời tâm, `min_spacing`, K) |
| `core/blackbox.py` | Cầu nối: MCOC thực (`make_real_evaluator`) hoặc mock |
| `core/mcoc_runner.py` | Gọi `MCOC_Batch.exe` (subprocess), parse `*_result.txt`; hỗ trợ `.lnk`; chạy ngầm |
| `io_handlers/mcoc_writer.py` | Sinh file input MCOC từ template (ghi đè tải từ UI) |
| `io_handlers/report_writer.py` | Báo cáo kỹ thuật `.md`/`.pdf` (R1–R8, lún Đ.7.4.4, ngang Phụ lục A Mục 6c) |
| `core/tcvn.py` | TCVN 10304:2014: Rc,d (Đ.7.1.11), móng khối quy ước + lún (Đ.7.4.4 — Se + Boussinesq) |
| `core/lrfd.py` | **TCVN 11823:2017 (LRFD)** — nguồn duy nhất γ/φ, `φ·Rn`, tải có hệ số, `apply_design_basis`. Chọn qua cờ `DESIGN_BASIS` (mặc định 11823). Xem [ADR-008](adr/ADR-008-co-so-thiet-ke-tcvn-11823.md), [kế hoạch migration](../project/MIGRATION_TCVN11823.md) |
| `core/cap_design.py` | Thiết kế đài TCVN 5574:2018 (uốn, chọc thủng, cắt 1 phương Qb đầy đủ, STM) |
| `core/ssi_engine.py` | Tương tác đất–cọc thuần NumPy (dọc trục + ngang Winkler "m" + lún + nhóm) |
| `core/version.py` | Nguồn version duy nhất (**v1.10.0**) |

### Giao diện (GUI) — composition (Plan 023)
`ui/main_window.py` từ **3247 dòng (1 class)** → còn **~512 dòng**: VỎ điều phối giữ
state chia sẻ + dựng khung 2 tab/menu + tạo & nối component; giữ **delegator mỏng**
cho API ngoài. Logic tách thành (component nhận tham chiếu `app`):

| Nhóm | File | Vai trò |
|---|---|---|
| controllers | `ui/controllers/{params,loads,file_ops,results,simulation,optimization}.py` | tham số+TCVN, CRUD tải, nạp/xuất file, render kết quả+KPI, vẽ mô phỏng+audit, chạy tối ưu (thread) |
| tabs | `ui/tabs/{interactive_tab,batch_tab}.py` | dựng giao diện Tab 1 / Tab 2 (hàng loạt) |
| widgets | `ui/widgets/{tooltip,widget_utils}.py`, `ui/constants.py`, `ui/strings.py` | tiện ích GUI + hằng số + nhãn dùng chung |

### Gói mở rộng (ext)
`core/ext/` + `io_handlers/mcoc_writer_ext.py` — **tách biệt, không sửa lõi**. Ba
tính năng: bật R7/R8, đổi đường kính cọc, thu bệ vừa khít. Chi tiết:
[EXT_TOIUU_MO_RONG.md](EXT_TOIUU_MO_RONG.md).

---

## Cạm bẫy / lưu ý
- `rigid_cap` phải giữ số hạng dời tâm `N·cy` / `N·cx` (Kiểu B `ny` chẵn).
- Mock cho mômen là heuristic → R6 ở mock kém tin cậy (có cảnh báo trong báo cáo).
- Mọi mô tả tiêu chuẩn ở đây phản ánh **TCVN 10304:2014** (code hiện tại). Định
  hướng bắt buộc chuyển sang **TCVN 11823:2017**: [ADR-008](adr/ADR-008-co-so-thiet-ke-tcvn-11823.md),
  [Backlog M1](../project/BACKLOG.md).

Liên quan: [Báo cáo thuật toán & kiểm chứng](BAO_CAO_THUAT_TOAN.md) · [Phương pháp](METHODOLOGY.md) · [ADR](adr/README.md) · [Thuật ngữ](../guides/GLOSSARY.md)
