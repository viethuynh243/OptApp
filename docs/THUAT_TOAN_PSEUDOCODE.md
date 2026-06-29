# Thuật toán giải bài toán tối ưu bố trí cọc (pseudocode)

Dựa trên mô hình trong `docs/MO_HINH_TOI_UU.tex`. Ký hiệu giữ nhất quán:
Ω miền khả thi · Θ vi phạm cứng · Π phạt mềm · ≺ trội có ràng buộc ·
G toán tử sinh lưới · Ψ oracle MCOC · F_aug = (f1, f2·(1+Π)).

```
═══════════════════════════════════════════════════════════════════════
 NSGA-II + MCOC
═══════════════════════════════════════════════════════════════════════

INPUT : D, Lx, Ly, c, [Po],[Ct],[M],[H], tải {ℓk};  μ, T, ηc=15, ηm=20, max_evals
OUTPUT: tập Pareto P các phương án x = (t, nx, ny, sx, sy)

─── HÀM PHỤ ───────────────────────────────────────────────────────────

DECODE(x):                          # giải mã + SỬA CHỮA về miền hợp lệ
    nx ← clamp(round(nx), 1, nx_max);  ny ← clamp(round(ny), 1, ny_max)
    nếu t = B: nx,ny ← max(·,2)
    sx,sy ← clamp vào [3D, bước_mép]
    return spec(t, nx, ny, sx, sy)

EVALUATE(x):                        # → (F_aug, Θ)   có CACHE
    spec ← DECODE(x);  key ← (t,nx,ny,sx,sy)
    nếu key ∈ cache: return cache[key]
    C ← G(spec);  n ← |C|
    {Pi^k} ← Ψ(C, {ℓk});  evals++   # GỌI MCOC (chính xác)
    rút Pmax, Pmin, Mx_max, My_max; Hmax ← từ mô hình bệ cứng

    Θ ← [3D − s★]+/3D                            # H2 khoảng cách min
      + [max|x|+c − Lx/2]+/(Lx/2) + (theo y)      # H3,H4 mép bệ
      + [Pmax − Po]+/Po                           # H5 nén
      + [−Ct − Pmin]+/Ct      (nếu Ct>0)          # H6 nhổ
      + [max(Mx,My) − M]+/M   (nếu M>0)           # H7 uốn
      + [Hmax − H]+/H         (nếu bật)           # H8 ngang
      + [Pmax/Po + max(Mx,My)/M − 1]+ (nếu bật)   # H9 tương tác P–M

    Π ← Σ wq · [s† − 6D]+/(6D)   (chỉ khi ENFORCE_SPACING_MAX)  # S1 mềm

    f1 ← n;   f2 ← footprint(C) hoặc Pmax        # chế độ Gọn / An toàn
    F_aug ← ( f1 , f2·(1+Π) );  ok ← (Θ = 0)
    cache[key] ← (F_aug, Θ, ok);  return cache[key]

DOMINATES(a, b):                    # a ≺ b ?
    nếu Θa=0 và Θb>0:  return true
    nếu Θa>0 và Θb>0:  return Θa < Θb
    return ParetoLE(Fa,Fb) và ParetoLT(Fa,Fb)

─── CHƯƠNG TRÌNH CHÍNH ────────────────────────────────────────────────

SOLVE():
    # 1) KHỞI TẠO có GIEO HẠT TẤT ĐỊNH
    seeds ← {phương án gốc} ∪ {mọi lưới (t,nx,ny) ở 2 bước 3D,6D, sắp n tăng dần}
    Pop ← seeds ∪ {ngẫu nhiên};  cắt còn μ
    for x in Pop: EVALUATE(x)

    # 2) TIẾN HÓA
    for gen = 1 … T:
        if evals ≥ max_evals: break
        Offspring ← ∅
        repeat μ/2 lần:
            p1 ← TOURNAMENT(Pop);  p2 ← TOURNAMENT(Pop)   # theo (rank, crowd)
            c1,c2 ← SBX(p1,p2,ηc);  c1,c2 ← POLY_MUTATE(c1,c2,ηm)
            EVALUATE(c1); EVALUATE(c2);  Offspring ∪= {c1,c2}
        R ← Pop ∪ Offspring
        fronts ← FAST_NON_DOMINATED_SORT(R)        # dùng DOMINATES()
        Pop ← ∅
        for F in fronts:
            CROWDING_DISTANCE(F)
            nếu |Pop|+|F| ≤ μ:  Pop ∪= F
            else: Pop ∪= (μ−|Pop| cá thể của F có crowd lớn nhất); break

    # 3) KẾT QUẢ
    P ← { x ∈ Pop : Θx = 0 và front 0 }
    recommended ← argmin_{x∈P} (n, f2)
    return P, recommended

═══════════════════════════════════════════════════════════════════════
 MÔ HÌNH MỞ RỘNG (đường kính + thu bệ)
═══════════════════════════════════════════════════════════════════════

SOLVE_EXTENDED(bảng đường kính 𝒟):
    for d in 𝒟:
        patch tiết diện d vào template MCOC; cập nhật [Po],[Ct],[M],[H]
        Pd ← SOLVE()  với H8,H9 BẬT
        best[d] ← argmin_{x∈Pd} n;  cost[d] ← n(best[d])·(π d²/4)
    d* ← argmin_d ( cost[d], n[d] )
    x* ← best[d*];  (Lx,Ly) ← RESIZE_CAP(x*)
    return x*, d*, (Lx,Ly)
```

## Mạch logic tóm tắt

1. **Gieo hạt** để phủ vùng khả thi rất hẹp → tránh báo "vô nghiệm" oan.
2. **EVALUATE**: sinh tọa độ → MCOC chấm → đo vi phạm cứng Θ + phạt mềm Π → mục tiêu (n, f2).
3. **DOMINATES**: khả thi thắng bất khả thi → ít vi phạm thắng → Pareto.
4. **Tiến hóa**: chọn → lai ghép → đột biến → giữ μ cá thể tốt nhất (elitism + crowding).
5. **Cache + trần ngân sách** giảm số lần gọi MCOC.
6. **Mở rộng**: lặp cho từng đường kính → chọn rẻ nhất → thu bệ.
