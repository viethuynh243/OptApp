# Thuật toán giải bài toán tối ưu bố trí cọc (pseudocode)

Giải **mô hình rút gọn** (Phần III trong `docs/MO_HINH_TOI_UU.tex`) — tức bài toán
tổng quát đã thu giảm về họ lưới đối xứng. Ký hiệu nhất quán:

- Ω miền khả thi · Θ vi phạm cứng (chuẩn hóa) · ≺ trội có ràng buộc
- G toán tử sinh lưới · Ψ oracle MCOC (hiện thực số của toán tử phân tích 𝒜)
- Mục tiêu **thuần** F = (f1, f2) — KHÔNG có số hạng phạt.
- Vòng lõi: **Lx, Ly, d CỐ ĐỊNH**. Đường kính & kích thước bệ là 2 tầng NGOÀI.

```
═══════════════════════════════════════════════════════════════════════
 NSGA-II + MCOC  —  giải mô hình rút gọn (R1–R6)
═══════════════════════════════════════════════════════════════════════

INPUT : D, Lx, Ly, c, [Po],[Ct],[M];  μ, T, ηc=15, ηm=20, max_evals
        (tùy chọn: [H], cờ R7/R8, cờ ENFORCE_SPACING_MAX — mặc định TẮT)
OUTPUT: tập Pareto P các phương án x = (t, nx, ny, sx, sy)

─── HÀM PHỤ ───────────────────────────────────────────────────────────

DECODE(x):                          # giải mã + SỬA CHỮA về miền hợp lệ
    nx ← clamp(round(nx), 1, nx_max);  ny ← clamp(round(ny), 1, ny_max)
    nếu t = B: nx,ny ← max(·,2)
    sx,sy ← clamp vào [s_min, min(6d, bước_mép)]   # 6d là CHẶN BIẾN
    return spec(t, nx, ny, sx, sy)
    # s_min = max(3d, d + thông_thủy)

EVALUATE(x):                        # → (F, Θ)   có CACHE
    spec ← DECODE(x);  key ← (t,nx,ny,sx,sy)
    nếu key ∈ cache: return cache[key]
    C ← G(spec);  n ← |C|                          # |C|: kiểu B đã trừ cọc so le
    {Pi^k} ← Ψ(C, {ℓk});  evals++                  # GỌI MCOC (chính xác)
    rút Pmax, Pmin, Mx_max, My_max

    # --- vi phạm CỨNG (lõi R1–R6), chuẩn hóa, [a]+ = max(0,a) -------
    Θ ← [s_min − s★]+/s_min                         # H2 khoảng cách min
      + [max|x|+c − Lx/2]+/(Lx/2) + (theo y)        # H3,H4 mép bệ
      + [Pmax − Po]+/Po                             # H5 nén
      + [−Ct − Pmin]+/Ct      (nếu Ct>0)            # H6 nhổ
      + [max(Mx,My) − M]+/M   (nếu M>0)             # H7 uốn
      # --- ràng buộc TÙY CHỌN: chỉ cộng khi cờ bật ---
      + [s† − 6d]+/(6d)               (nếu ENFORCE_SPACING_MAX)  # C1
      + [Hmax − H]+/H                 (nếu R7 bật)               # C2
      + [Pmax/Po + max(Mx,My)/M − 1]+ (nếu R8 bật)              # C3

    # --- MỤC TIÊU thuần (không phạt) -------------------------------
    f1 ← n
    f2 ← footprint(C)   hoặc   Pmax       # chế độ "bệ gọn" / "an toàn"
    F ← (f1, f2);   ok ← (Θ = 0)
    cache[key] ← (F, Θ, ok);  return cache[key]

DOMINATES(a, b):                    # a ≺ b ?  (constrained-domination)
    nếu Θa=0 và Θb>0:  return true            # khả thi thắng bất khả thi
    nếu Θa>0 và Θb>0:  return Θa < Θb         # ít vi phạm hơn thắng
    return ParetoLE(Fa,Fb) và ParetoLT(Fa,Fb) # cả hai khả thi → Pareto

─── CHƯƠNG TRÌNH CHÍNH ────────────────────────────────────────────────

SOLVE():                            # Lx, Ly, d CỐ ĐỊNH
    # 1) KHỞI TẠO có GIEO HẠT TẤT ĐỊNH (phủ vùng khả thi rất hẹp)
    seeds ← {phương án gốc} ∪ {mọi lưới (t,nx,ny) ở 2 bước 3d,6d, sắp n tăng dần}
    Pop ← env_select(EVAL_ALL(seeds) + EVAL_ALL(ngẫu_nhiên(μ)), μ)

    # 2) TIẾN HÓA
    for gen = 1 … T:
        if evals ≥ max_evals: break
        Off ← ∅
        repeat μ/2 lần:
            p1 ← TOURNAMENT(Pop);  p2 ← TOURNAMENT(Pop)     # theo (rank, crowd)
            c1,c2 ← SBX(p1,p2,ηc);  c1,c2 ← POLY_MUTATE(c1,c2,ηm)
            EVALUATE(c1); EVALUATE(c2);  Off ∪= {c1,c2}
        Pop ← env_select(Pop ∪ Off, μ)                      # μ+λ elitism

    # 3) KẾT QUẢ — tổng hợp trên TOÀN BỘ cache (không chỉ Pop cuối)
    valid ← { r ∈ cache : Θr = 0 }
    P ← các r ∈ valid không bị (n, f2) nào trội         # mặt Pareto khả thi
    recommended ← argmin_{r∈valid} (n, f2)              # ít cọc nhất → mục tiêu phụ
    return P, recommended

env_select(R, μ):                   # chọn lọc môi trường NSGA-II
    fronts ← FAST_NON_DOMINATED_SORT(R)   # dùng DOMINATES()
    Pop ← ∅
    for F in fronts:
        CROWDING_DISTANCE(F)
        nếu |Pop|+|F| ≤ μ:  Pop ∪= F
        else: Pop ∪= (μ−|Pop| cá thể của F có crowd lớn nhất); break
    return Pop

═══════════════════════════════════════════════════════════════════════
 HAI TẦNG NGOÀI (mở rộng — KHÔNG thuộc vòng lõi)
═══════════════════════════════════════════════════════════════════════

SOLVE_EXTENDED(bảng đường kính 𝒟):
    for d in 𝒟:                                  # quét đường kính
        patch tiết diện d vào template MCOC; cập nhật [Po],[Ct],[M],[H]
        Pd ← SOLVE()  với R7 (C2), R8 (C3) BẬT
        best[d] ← argmin_{x∈Pd} n;  cost[d] ← n(best[d])·(π d²/4)   # chi phí vật liệu
    d* ← argmin_d ( cost[d], n[d] )
    x* ← best[d*]
    (Lx,Ly) ← RESIZE_CAP(x*)                     # thu bệ — HẬU XỬ LÝ, không phải biến lõi
    return x*, d*, (Lx,Ly)
```

## Mạch logic tóm tắt

1. **Gieo hạt tất định** để phủ vùng khả thi hẹp → tránh báo "vô nghiệm" oan.
2. **EVALUATE**: sinh tọa độ (G) → MCOC chấm (Ψ) → vi phạm cứng Θ (R1–R6; R7/R8 và 6d chỉ khi bật) → mục tiêu **thuần** (n, f2).
3. **DOMINATES**: khả thi thắng bất khả thi → ít vi phạm thắng → Pareto.
4. **Tiến hóa**: chọn → lai (SBX) → đột biến → giữ μ tốt nhất (elitism + crowding).
5. **Cache + trần ngân sách** giảm số lần gọi MCOC.
6. **Hai tầng ngoài**: quét đường kính theo chi phí vật liệu → thu bệ hậu xử lý.

> Ghi chú trung thực: pseudocode này là **lời giải của mô hình rút gọn**. Bài toán
> tổng quát (chi phí tổng; vị trí cọc tự do; lún/nền khối/thiết kế đài là ràng buộc)
> nằm ở Phần I của `MO_HINH_TOI_UU.tex`; lún & thiết kế đài được kiểm bằng module riêng.
