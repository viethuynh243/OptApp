# Thuật toán giải mô hình tối ưu móng cọc trụ cầu (LRFD / TCVN 11823:2017)

Giải mô hình hợp nhất trong `docs/MO_HINH_TOI_UU.tex`. Mọi ràng buộc là một thể hiện
của bất đẳng thức LRFD `Σηγ·Q ≤ φ·R_n` và **luôn áp dụng** (không bật/tắt).

Ký hiệu: Ω miền khả thi · Θ vi phạm (gộp tỉ số LRFD) · ≺ trội có ràng buộc ·
G sinh lưới · 𝒜 phân tích nội lực (MCOC) · 𝒮 phân tích lún · C chi phí.

```
═══════════════════════════════════════════════════════════════════════
 NSGA-II + ORACLE LRFD  (TCVN 11823: phần 3 tải, 5 bê tông, 10 nền móng)
═══════════════════════════════════════════════════════════════════════

INPUT : tải danh định {DC,DW,LL,EQ,...}; địa chất Σ; vật liệu f'c,fy;
        hệ số chuẩn φ (10.5.5.2.3, 5.5.4.2), γ (Bảng 3.4.1-1);
        dung sai S_tol, δ_tol;  μ, T, ηc=15, ηm=20, max_evals
OUTPUT: phương án x = (lưới đối xứng, D, Lc, đài Bx×By×h, As) chi phí nhỏ nhất

─── DỮ LIỆU TẢI: dựng tổ hợp đã nhân hệ số (TCVN 11823-3) ──────────────
BUILD_COMBINATIONS():
    Strength_I  : 1.25·DC + 1.50·DW + 1.75·(LL+IM)         (+ biến thể min 0.90/0.65)
    Service_I   : 1.00·DC + 1.00·DW + 1.00·(LL+IM)
    Extreme_I   : 1.25·DC + 1.50·DW + 0.50·(LL+IM) + 1.00·EQ
    return L = {Strength_I, Service_I, Extreme_I}

─── HÀM PHỤ ───────────────────────────────────────────────────────────
DECODE(x):                          # giải mã + sửa chữa về miền hợp lệ
    nx,ny ← clamp số nguyên;  sx,sy ← clamp [s_min, bước_mép]
    s_min = max(2.5·D, 750mm)        # TCVN 11823-10 (KHÁC 10304: 2.5D, không 3D)
    return spec(t,nx,ny,sx,sy)

EVALUATE(x):                        # → (C, Θ)   có CACHE
    spec ← DECODE(x);  nếu cache có: return
    C_geom ← G(spec);  n ← |C_geom|;  L ← BUILD_COMBINATIONS()
    for ℓ in L:
        {Pi,Hi,Mi}^ℓ ← 𝒜(x, Σ; ℓ)        # MCOC — gồm p-multiplier (10.7.2.4)
        S^ℓ ← 𝒮(x, Σ; ℓ);  δ^ℓ ← p-y      # lún (10.7.2), chuyển vị ngang

    # ── Θ = Σ tỉ số LRFD vượt 1, gộp mọi ràng buộc (vô thứ nguyên) ──
    Θ ← 0
    for ℓ in {Strength_I, Extreme_I}:                         # CƯỜNG ĐỘ + ĐẶC BIỆT
        for i in cọc:
            Θ += [ Pu,i^ℓ /(φc·Rn) − 1 ]+          # C1 nén  (10.5.5.2.3)
            Θ += [ Tu,i^ℓ /(φup·Rn,up) − 1 ]+      # C2 nhổ
            Θ += [ Hu,i^ℓ /(φℓ·Rℓ) − 1 ]+          # C3 ngang
            Θ += [ tỉ số bao P–M tiết diện cọc − 1 ]+   # C4 (11823-5)
        Θ += [ Mu /(φf·Mn) − 1 ]+                   # C5 uốn đài  (5.5.4.2: φf=0.9)
        Θ += [ Vu /(φv·Vn_1way) − 1 ]+             # C6 cắt 1 phương
        Θ += [ Vu /(φv·Vn_2way) − 1 ]+             # C7 chọc thủng
        Θ += [ STM tỉ số /(φstm) − 1 ]+   (đài sâu) # C8 giàn ảo
    for ℓ in {Service_I}:                                     # SỬ DỤNG
        Θ += [ S^ℓ / S_tol − 1 ]+                  # C9 lún   (10.7.2.2)
        Θ += [ δ^ℓ / δ_tol − 1 ]+                  # C10 chuyển vị ngang
    for i≠j:                                                  # CẤU TẠO (10.7.1.2)
        Θ += [ s_min / ‖pi−pj‖ − 1 ]+             # C11 khoảng cách tim
    Θ += [ vi phạm mép đài (≥ D/2+225mm) ]+        # C12,C13

    # ── MỤC TIÊU: chi phí công trình ──
    C ← n·(πD²/4)·Lc·c_bt + n·c_tc + (Bx·By·h)·c_bt + Ws(As)·c_s
    cache[key] ← (C, Θ, ok=(Θ=0));  return

DOMINATES(a,b):                     # a ≺ b ?  (constrained-domination)
    nếu Θa=0 và Θb>0:  return true            # khả thi thắng bất khả thi
    nếu Θa>0 và Θb>0:  return Θa < Θb         # ít vi phạm hơn thắng
    return Ca < Cb                            # cả hai khả thi → chi phí nhỏ hơn

─── CHƯƠNG TRÌNH CHÍNH ────────────────────────────────────────────────
SOLVE():
    # 1) KHỞI TẠO có GIEO HẠT TẤT ĐỊNH (phủ vùng khả thi hẹp)
    seeds ← {phương án gốc} ∪ {lưới (t,nx,ny) ở 2.5D và bước thưa, sắp n tăng dần}
    Pop ← env_select(EVAL_ALL(seeds) ∪ EVAL_ALL(ngẫu_nhiên(μ)), μ)
    # 2) TIẾN HÓA
    for gen = 1..T:
        if evals ≥ max_evals: break
        Off ← ∅
        repeat μ/2:
            p1,p2 ← TOURNAMENT(Pop)×2            # theo (rank, crowd)
            c1,c2 ← SBX(p1,p2,ηc);  MUTATE(ηm);  EVALUATE(c1,c2);  Off ∪= {c1,c2}
        Pop ← env_select(Pop ∪ Off, μ)           # μ+λ elitism
    # 3) KẾT QUẢ
    valid ← {r ∈ cache : Θr=0}
    return argmin_{r∈valid} Cr,  Pareto(chi phí, dự_trữ) [hỗ trợ quyết định]

env_select(R,μ):                    # chọn lọc môi trường NSGA-II
    fronts ← NON_DOMINATED_SORT(R)   # dùng DOMINATES()
    lấy từng front + CROWDING_DISTANCE cho tới đủ μ (front cắt: ưu tiên crowd lớn)
```

## Mạch logic

1. **Dựng tổ hợp tải** Strength I / Service I / Extreme I (hệ số TCVN 11823-3).
2. **EVALUATE**: với mỗi tổ hợp, MCOC chấm nội lực (gồm hiệu ứng nhóm) + tính lún/chuyển vị → gộp **mọi** kiểm toán C1–C13 thành Θ (tỉ số LRFD vượt 1).
3. **Khả thi ⟺ Θ=0**; so sánh bằng trội có ràng buộc → cực tiểu **chi phí C**.
4. Tiến hóa NSGA-II + gieo hạt + cache + trần ngân sách.

> **Một mô hình — một bất đẳng thức LRFD — mọi trạng thái giới hạn luôn kiểm.**
> Trị số φ, γ, s_min theo AASHTO LRFD mà TCVN 11823:2017 áp dụng (đối chiếu bản TCVN khi phát hành hồ sơ).
