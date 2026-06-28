# OptApp — Giải thích chi tiết kỹ thuật toàn bộ chương trình

Tài liệu này giải thích chiều sâu của TỪNG thuật toán/công thức trong OptApp theo cấu trúc:
**(a) làm gì — (b) công thức/cơ chế — (c) vì sao làm vậy**.

---

## A. ĐỘNG CƠ TỐI ƯU NSGA-II (`core/nsga2_optimizer.py`)

### A1. Mã hóa phương án (genome) và giải mã có sửa chữa
**Làm gì:** Mỗi phương án bố trí cọc được mã hóa thành 5 gene: `type ∈ {A, B}`, `nx`, `ny`, `sx`, `sy`.

**Cơ chế (`decode`, `_grid_bounds`):**
- Số cọc tối đa mỗi phương: `nmax = 1 + floor(2·maxx / (3d))` — suy từ điều kiện bước lưới ≥ 3d và cọc nằm trong mép bệ (`maxx = L_X/2 − SAFE_D`).
- `nx, ny` làm tròn rồi **kẹp** về `[1, nmax]`; kiểu B ép tối thiểu 2×2.
- `sx, sy` kẹp về `[ε, bước_mép]` với `sx_edge = min(6d, 2·maxx/(nx−1))`.

**Vì sao:** Toán tử di truyền sinh số thực bất kỳ → phải **"sửa chữa" (repair)** về miền hợp lệ trước khi đánh giá. Đây là kỹ thuật chuẩn để GA làm việc với biến rời rạc + ràng buộc biên, tránh sinh phương án vô nghĩa.

### A2. Constrained-domination (Deb) — trái tim xử lý ràng buộc
**Làm gì:** Định nghĩa "phương án A tốt hơn B" khi có ràng buộc.

**Cơ chế (`_constrained_dominates`):**
1. Khả thi luôn thắng bất khả thi.
2. Hai bất khả thi → ai có **mức vi phạm CV nhỏ hơn** thì thắng.
3. Hai khả thi → so Pareto trên (số cọc, mục tiêu phụ).

**Vì sao:** Đây là cách của Deb (2002) để GA tự "bò" từ vùng vi phạm về vùng khả thi mà không cần hàm phạt thủ công. Rất ít người tự cài đúng phần này — nó là dấu hiệu hiểu sâu lý thuyết tối ưu.

### A3. Mức vi phạm ràng buộc CV — chuẩn hóa (`evaluate`)
**Làm gì:** Gộp mọi vi phạm R3–R8 thành 1 số `cv ≥ 0` (cv≈0 = khả thi).

**Cơ chế:** Mỗi ràng buộc được **chuẩn hóa không thứ nguyên** rồi cộng dồn:
```
cv += max(0, pmax − Po)/Po          # R5 nén
cv += max(0, −Ct − pmin)/Ct         # R5b nhổ
cv += max(0, s_min − s)/s_min       # R3 dưới (kể cả đường chéo kiểu B)
cv += max(0, mx+SAFE_D − L_X/2)/(L_X/2)  # R4 mép bệ
cv += max(0, mxmax − [M])/[M]       # R6 uốn
cv += max(0, hmax − [H])/[H]        # R7 ngang
cv += max(0, pmax/Po + M/[M] − 1)   # R8 tương tác P–M
```

**Vì sao chuẩn hóa:** Nếu cộng thô, vi phạm lực (hàng trăm Tấn) sẽ "nuốt" vi phạm hình học (vài cm) → GA bỏ qua ràng buộc nhỏ. Chia cho giá trị giới hạn đưa mọi thành phần về cùng thang ~O(1) để **cân bằng tầm quan trọng**. Đây là kỹ thuật penalty normalization chuẩn mực.

### A4. Fast non-dominated sorting
**Làm gì:** Xếp cả quần thể thành các "tầng" Pareto (front 0 = tốt nhất).

**Cơ chế:** Với mỗi cá thể p, đếm `nd[p]` = số cá thể trội hơn p, và lưu `S[p]` = tập p trội. Front 0 = các p có `nd=0`. Bóc dần từng tầng. Độ phức tạp O(M·N²).

**Vì sao:** Bài toán đa mục tiêu không có "1 nghiệm tốt nhất" — chỉ có mặt đánh đổi (Pareto). Sorting này là cách phân hạng toàn quần thể theo độ trội.

### A5. Crowding distance — giữ đa dạng
**Làm gì:** Trong cùng một front, ưu tiên giữ cá thể "thưa hàng xóm" để mặt Pareto trải đều.

**Cơ chế:** Với mỗi mục tiêu m, sắp xếp front theo m, cộng cho mỗi cá thể khoảng cách chuẩn hóa tới 2 hàng xóm: `(f[k+1] − f[k−1])/(fmax − fmin)`. Hai đầu mút = ∞ (luôn giữ).

**Vì sao:** Không có cơ chế này, GA hội tụ về một cụm → mất đa dạng, người dùng không có nhiều phương án để chọn. Khoảng cách chen chúc là cách của NSGA-II thay cho fitness sharing (rẻ hơn, không cần tham số).

### A6. SBX crossover (lai ghép nhị phân mô phỏng)
**Làm gì:** Lai 2 giá trị thực cha-mẹ thành 2 con.

**Cơ chế (`_sbx`):** Sinh `u ~ U(0,1)`, tính hệ số phân bố `β_q`:
```
nếu u ≤ 1/α:  β_q = (u·α)^(1/(η+1))
ngược lại:     β_q = (1/(2−u·α))^(1/(η+1))
con = 0.5·[(x1+x2) ∓ β_q·(x2−x1)]
```
với η=15. Có xử lý biên (lo, hi) riêng cho từng con.

**Vì sao:** SBX mô phỏng hành vi của lai ghép nhị phân cổ điển nhưng trên **biến thực**: con có xu hướng gần cha mẹ (khai thác cục bộ), thỉnh thoảng nhảy xa (khám phá). η điều khiển độ "bám" cha mẹ. Đây là toán **biến đổi nghịch đảo CDF** (inverse-transform sampling) của một phân phối xác suất thiết kế riêng.

### A7. Polynomial mutation (đột biến đa thức)
**Làm gì:** Nhiễu loạn 1 gene thực để tạo biến dị.

**Cơ chế (`_poly_mutate`):**
```
nếu u < 0.5:  δ = (2u)^(1/(η+1)) − 1
ngược lại:    δ = 1 − (2(1−u))^(1/(η+1))
x_mới = x + δ·(hi − lo)
```
với η=20.

**Vì sao:** Đột biến tạo "lối thoát" khỏi cực trị cục bộ. Phân phối đa thức cho bước nhỏ thường xuyên + bước lớn hiếm — cân bằng khai thác/khám phá. Cũng là inverse-transform của một phân phối đối xứng quanh 0.

### A8. Tournament + Environmental selection (μ+λ elitism)
**Làm gì:** Chọn cha mẹ và chọn người sống sót sang thế hệ sau.

**Cơ chế:**
- `_tournament`: bốc 2 cá thể, giữ cá thể "crowded-better" (rank thấp hơn, hoặc cùng rank thì crowd lớn hơn).
- `_environmental_selection`: gộp cha + con (μ+λ), lấy lần lượt từng front đầy dần `pop_size`; front bị cắt thì ưu tiên crowd lớn.

**Vì sao:** Elitism (μ+λ) đảm bảo nghiệm tốt **không bao giờ mất đi** qua các thế hệ — tính chất hội tụ then chốt của NSGA-II.

### A9. Chiến lược gieo hạt tất định (`_build_seed_genomes`) — insight domain mạnh nhất
**Làm gì:** Tiêm sẵn một số phương án "chắc chắn nên thử" vào quần thể khởi tạo, thay vì để toàn ngẫu nhiên.

**Cơ chế:**
1. Phương án GỐC của kỹ sư (giải mã tọa độ thật thành lưới qua `detect_grid`).
2. Liệt kê mọi lưới `type × nx × ny` ở **đúng 2 bước lưới**: 3d (dày) và 6d (thưa). Sắp xếp **theo số cọc tăng dần**.

**Vì sao (rất quan trọng):** Vùng khả thi của bài toán này là một "lát rất mỏng" — bước cọc bị kẹp gần 3d bởi mép bệ, kiểu B còn bị siết bởi ràng buộc đường chéo. Toán tử **ngẫu nhiên gần như không bao giờ trúng** → GA báo "vô nghiệm" dù nghiệm tồn tại. Sắp xếp theo số cọc tăng dần để khi ngân sách MCOC hẹp vẫn quét đủ phổ. Đây là hiểu biết về **hình học miền nghiệm**, không phải kiến thức GA sách vở.

### A10. Cache + ngân sách (budget)
**Làm gì:** Không gọi MCOC trùng; dừng khi đạt trần `max_evals`.

**Cơ chế:** Khóa cache = `(type, nx, ny, round(sx,3), round(sy,3))`. Khi hết ngân sách, chỉ nhận cá thể đã có trong cache.

**Vì sao:** MCOC chạy chậm (mỗi lần là 1 tiến trình). Nhiều genome khác nhau sau khi "sửa chữa" kẹp về cùng spec → cache loại trùng giúp **số lần gọi MCOC = số spec phân biệt**, tiết kiệm cực lớn.

---

## B. SINH TỌA ĐỘ LƯỚI (`core/generator.py`)

**Làm gì:** Dựng tọa độ cọc đối xứng quanh tâm bệ.

**Cơ chế:**
- Kiểu A: `x_i = (i − (nx−1)/2)·sx` → đối xứng quanh 0.
- Kiểu B (hoa mai): hàng chẵn nx cọc, hàng lẻ nx−1 cọc; mỗi hàng tự đối xứng nên hàng lẻ **tự lệch sx/2** mà không cần cộng offset thủ công.

**Vì sao:** Tâm nhóm cọc trùng tâm bệ → lực phân bố đều nhất (giảm lệch tâm). Mẹo "hàng lẻ ít hơn 1 cọc tự tạo so le" là cách viết gọn và không lỗi.

---

## C. CƠ HỌC BỆ CỨNG (`core/rigid_cap.py`)

### C1. Phân phối lực dọc trục
**Công thức:** `P_i = N/n + Mx_t·dy/Ix + My_t·dx/Iy`, với mômen quy về tâm nhóm `Mx_t = Mx − N·cy`.

**Vì sao quy về tâm:** Khử lệch tâm khi hợp lực N đặt tại gốc tọa độ chứ không tại tâm nhóm cọc — nếu không trừ `N·cy`, kết quả sai khi nhóm cọc lệch tâm.

### C2. Mômen quán tính & lực ngang/xoắn
- `Ix = Σ(y−cy)²`, `Iy = Σ(x−cx)²`, mômen cực `Ip = Ix+Iy`.
- Lực ngang: `Hxi = Hx/n − Mz·dy/Ip` (chia đều lực cắt + phân phối xoắn theo bán kính cực).
- Chống chia 0: `Ix or EPS` khi cọc thẳng hàng.

### C3. Khoảng cách & đường chéo hoa mai
`spacing_values` là **nguồn duy nhất** quy tắc R3. Kiểu B trả khoảng cách đường chéo `√((sx/2)² + sy²)` — vì cặp cọc gần nhất ở hàng so le là đường chéo, không phải sx hay sy. (Lỗi cũ bỏ sót đường chéo đã được sửa.)

### C4. Hệ số hiệu chỉnh mô hình
`K = Pmax_MCOC / Pmax_bệ_cứng` (≈ 0.98). Dùng để hiệu chỉnh dự báo nhanh bệ cứng theo MCOC thực — **sai số mô hình ~2%**, không phải quy đổi đơn vị.

---

## D. ENGINE TƯƠNG TÁC ĐẤT–CỌC SSI (`core/ssi_engine.py`)

### D1. Bài toán dọc trục — hệ 3 bậc tự do
**Làm gì:** Tính lún + xoay bệ khi các cọc có độ cứng khác nhau.

**Cơ chế:** Ẩn `u = (d0, a, b)` = lún tâm + 2 độ dốc xoay. Lập hệ `K·u = f`:
```
| Σk     Σk·dx   Σk·dy  | |d0|   | N    |
| Σk·dx  Σk·dx²  Σk·dxdy| |a | = | My_t |
| Σk·dy  Σk·dxdy Σk·dy² | |b |   | Mx_t |
```
Lún cọc `δ_i = d0 + a·dx + b·dy`, lực `P_i = k_i·δ_i`. Chống suy biến bằng nhiễu Tikhonov nhỏ trên đường chéo.

**Vì sao:** Đây là tổng quát hóa của bệ cứng — khi mọi cọc cùng độ cứng, kết quả **trùng khớp `rigid_cap`** (dùng làm mỏ neo kiểm chứng). Khi cọc khác độ cứng (vd cọc dài/ngắn khác nhau) thì chỉ hệ này tính đúng.

### D2. Cọc chịu ngang — dầm Euler–Bernoulli trên nền Winkler (FEM 1D)
**Làm gì:** Giải chuyển vị và mômen dọc thân cọc khi chịu lực ngang.

**Cơ chế:**
- **Ma trận độ cứng dầm** (Hermite bậc 3): `EI/L³·[[12, 6L, −12, 6L], ...]`.
- **Ma trận nền Winkler nhất quán** (consistent): `k·L/420·[[156, 22L, 54, −13L], ...]`.
- Lắp ghép theo DOF, áp điều kiện biên (ngàm xoay đầu cọc nếu liên kết bệ cứng), giải `K_ff·u = F`.
- Phục hồi mômen từ chuyển vị: `f_e = K_e·u_e`.

**Vì sao consistent matrix:** Ma trận nền "nhất quán" (tích phân hàm dạng × hàm dạng) chính xác hơn ma trận "tập trung" (lumped). Mô hình này là PT vi phân bậc 4 `EI·w'''' + k·w = 0` — nghiệm số được kiểm chứng bằng nghiệm giải tích Hetenyi và tham số đặc trưng `β = (k/4EI)^(1/4)`.

### D3. Hiệu ứng nhóm cọc — p-multiplier AASHTO (đã giải thích chi tiết)
Giảm sức kháng đất của cọc hàng sau do "shadowing". Bảng 3D/5D nội suy tuyến tính theo s/D thực tế. Cọc hàng sau → Pₘ nhỏ → đất yếu hơn → chuyển vị/mômen tăng.

### D4. Tỷ số lún nhóm — power law Poulos
`R_s ≈ n^ω` (ω≈0.5). Lún nhóm cọc > lún cọc đơn do các vùng ứng suất chồng lấn. Hàm mũ là quy luật thực nghiệm Poulos để khuếch đại lún cọc đơn lên lún nhóm — bù cho hạn chế của mô hình lò xo độc lập.

---

## E. TÍNH TOÁN THEO TCVN (`core/tcvn.py`)

### E1. Sức chịu tải thiết kế (Điều 7.1.11)
`Rc,d = (γ0/γn)·(Rc,k/γk)`:
- γ0 = điều kiện làm việc (1.15 móng nhiều cọc).
- γn = tầm quan trọng công trình (cấp I/II/III = 1.2/1.15/1.1).
- γk = tin cậy theo đất, **tra theo số cọc** (1.40–1.75; bảng `GAMMA_K_BY_NPILES`).

**Điểm tinh tế — vòng lặp phụ thuộc:** `[Po] = Rc,d` cần γk, mà γk phụ thuộc **số cọc** — chỉ biết SAU khi tối ưu. Giải pháp: dùng mặc định khi chạy, áp γk đúng ở khâu báo cáo khi đã có số cọc; ô nhập tay luôn ưu tiên. Hàm `apply_design_capacities` idempotent (gọi nhiều lần vẫn an toàn), gắn metadata truy vết nguồn.

### E2. Móng khối quy ước (Điều 7.4)
Khối mở rộng từ chu vi nhóm cọc một góc φ_tb/4 trên suốt chiều dài cọc:
`B_qu = span_x + d + 2·Lc·tan(φ_tb/4)`. Có chặn `a ≤ 2d` khi dưới mũi là đất dính yếu (IL>0.6). Thiếu số liệu địa chất → trả `evaluated=False` (báo "chưa kiểm" thay vì âm thầm bỏ qua).

### E3. Lún — nghiệm Boussinesq (Điều 7.4.4 + TCVN 9362)
`S = Se + S_khối`:
- Se = β·N·Lc/(E·A) (biến dạng đàn hồi thân cọc, β=0.5).
- S_khối = Σ β·σ_zi·h_i/E_i (β=0.8), cộng từng lớp.
- σ_zi tính bằng **nghiệm Boussinesq dạng đóng tại tâm móng chữ nhật**:
  `σz/p = 4·I_góc(m,n)`, m=(B/2)/z, n=(L/2)/z — dùng atan2 xử lý dấu.
- Dừng khi `σz ≤ 0.2·σ'vz` (vùng nén lún kết thúc).

**Vì sao Boussinesq thay 2:1:** Xấp xỉ 2:1 (ứng suất lan đều theo góc 2:1) là gần đúng thô; nghiệm Boussinesq là lời giải đàn hồi chính xác — chính là cơ sở của bảng tra TCVN 9362. Dùng công thức đóng = chính xác hơn + không cần bảng tra.

---

## F. THIẾT KẾ KẾT CẤU ĐÀI (`core/cap_design.py`, TCVN 5574:2018)

### F1. Vật liệu & chiều cao vùng nén giới hạn
`ξ_R = 0.8/(1 + (Rs/Es)/εb2)`, εb2=0.0035 — đúng CT(31). Quyết định ranh giới phá hoại dẻo/giòn.

### F2. Cốt thép chịu uốn (Điều 8.1.2)
```
α_m = M/(Rb·b·h0²);  ξ = 1 − √(1−2α_m);  ζ = 0.5(1+√(1−2α_m))
As = M/(Rs·ζ·h0)
```
- Nếu `1−2α_m < 0` → bê tông nén vỡ, báo lỗi "tăng H hoặc cấp BT".
- Kiểm `ξ ≤ ξ_R` (không vượt vùng nén giới hạn), áp As tối thiểu 0.1%.

**Tiết diện nguy hiểm:** tại **mép cột**, lấy mômen của các cọc nằm ngoài mép cột (`flexure_dir`), chọn bên bất lợi hơn.

### F3. Chọc thủng (Điều 8.1.6)
- Quanh cột: chu vi tới hạn tại h0/2: `u_m = 2(bc+hc+2h0)`, `F_ult = Rbt·u_m·h0`. Lực gây chọc = `N_cột − Σ phản lực cọc trong tháp`.
- Quanh cọc: `u_m = π(D+h0)`.

### F4. Cắt một phương (Điều 8.1.3)
`Qb = 1.5·Rbt·b·h0²/C`, kẹp `[0.5; 2.5]·Rbt·b·h0`; giới hạn nén dải `Q ≤ 0.3·Rb·b·h0`. C = hình chiếu tiết diện nghiêng = khoảng cách từ mép cột tới **trọng tâm lực** các cọc ngoài mép (tính theo trung bình có trọng số `Σ(d_i·P_i)/ΣP_i`).

### F5. Giàn ảo STM (đài sâu)
`z = 0.9·h0; T = P·a/z; As_tie = T/Rs`. Cờ "đài sâu" khi a/h0 < 1.0. **Ghi rõ:** z và ngưỡng a/h0 lấy theo ACI/AASHTO (TCVN không định lượng) — trung thực về nguồn.

---

## G. TỐI ƯU MỞ RỘNG (`core/ext/orchestrator.py`)

### G1. Quét đường kính + chọn toàn cục
Với mỗi đường kính d (mỗi d có [Po]/[Ct]/[M]/[H] riêng), patch tiết diện thật vào file MCOC, chạy NSGA-II (R7+R8 bật). Chọn d thắng theo **hàm chi phí vật liệu**:
```
cost = n_cọc × diện_tích_tiết_diện = n × πd²/4
```
Đồng hạng thì ít cọc hơn.

**Vì sao hàm chi phí này:** Nó xấp xỉ **thể tích bê tông cọc trên 1 m dài** → cân bằng đúng đánh đổi "ít cọc to" vs "nhiều cọc nhỏ". Chỉ đếm số cọc thì sai (cọc to đắt hơn).

### G2. Thu bệ (`cap_resize`)
Sau khi có phương án thắng, co Lx/Ly về vừa khít cọc (mép ≥ d), làm tròn bội số thi công. Mỗi phương án mang **bệ riêng**: phương án gốc vẽ theo bệ gốc, đề xuất theo bệ đã thu — để so sánh "tiến hóa" công bằng. Bệ gốc luôn `max(ô hiện tại, bệ vừa khít)` để cọc gốc không tràn ra ngoài.

---

## H. TÍCH HỢP MCOC (`core/mcoc_runner.py`)

- Hỗ trợ `.exe/.bat/.py/.lnk` (resolve shortcut qua PowerShell trên Windows).
- **Xóa file kết quả cũ trước khi chạy** → phát hiện đúng kết quả mới (chống stale-result).
- Kiểm returncode: MCOC báo lỗi thì **không đọc kết quả** (tránh nhận số rác).
- Timeout chống treo; ẩn cửa sổ console (CREATE_NO_WINDOW) khi đóng gói.

**Vì sao quan trọng:** MCOC là "trọng tài" quyết định kết quả giao nộp. Nếu đọc nhầm kết quả cũ/lỗi, toàn bộ tối ưu sai mà không ai biết. Đây là phần xử lý rủi ro mà chỉ kỹ sư cẩn thận mới lường trước.

---

## TÓM LẠI — bản đồ kiến thức một dòng mỗi phần

| Phần | Kiến thức cốt lõi |
|---|---|
| NSGA-II | Tối ưu đa mục tiêu, Pareto, xác suất (SBX/mutation), xử lý ràng buộc |
| CV normalization | Chuẩn hóa không thứ nguyên, penalty cân bằng |
| Seeding | Hình học miền nghiệm, chiến lược phủ ngân sách |
| rigid_cap | Cơ học kết cấu (nén lệch tâm, xoắn, mômen quán tính) |
| SSI dọc trục | Đại số tuyến tính, hệ 3 ẩn, regularization |
| SSI ngang | FEM dầm, PT vi phân bậc 4, nghiệm Hetenyi |
| p-multiplier | Nội suy tuyến tính, cơ học nhóm cọc |
| Lún nhóm | Power law thực nghiệm |
| TCVN capacity | Hệ số an toàn, vòng lặp phụ thuộc |
| Lún | Nghiệm Boussinesq, tích phân số theo lớp |
| Cap design | Bê tông cốt thép, uốn/chọc thủng/cắt/STM |
| Diameter sweep | Hàm chi phí vật liệu, tối ưu rời rạc |
| MCOC integration | Xử lý subprocess robust, chống stale-result |
