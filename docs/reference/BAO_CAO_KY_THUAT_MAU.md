# BAN TINH KIEM TRA & TOI UU BO TRI MONG COC

> **Mã:** OA-DOC-06b · **Phiên bản:** 1.0 · **Cập nhật:** 2026-06-29 · **Trạng thái:** Approved · **Căn cứ:** io_handlers/report_writer.py

## Cong trinh: Cau Demo - Mo T1

OptApp v1.1.0. Tieu chuan: TCVN 10304:2014 (mong coc); TCVN 11823 (cau, LRFD). Noi luc tinh bang MCOC (chinh xac). Don vi: Tan (T), T.m.

## 1. SO LIEU DAU VAO

| Thong so | Ky hieu | Gia tri | Don vi |
|---|---|---:|---|
| Rong be | Lx | 6.00 | m |
| Dai be | Ly | 9.60 | m |
| Duong kinh coc | d | 1.20 | m |
| Tim coc -> mep be toi thieu | c_min | 1.20 | m |
| Suc chiu nen | [Po] | 500.0 | T |
| Suc chiu nho | [Ct] | 0.0 | T |
| Suc chiu uon | [M] | 0.0 | T.m |

## 2. TO HOP TAI TRONG  (luc T, momen T.m)

| TH | Hx | Hy | N | Mx | My | Mz |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.0 | 0.0 | 2577.0 | 1500.0 | 1500.0 | 0.0 |
| 2 | 0.0 | 0.0 | 2400.0 | 800.0 | 2000.0 | 0.0 |
| 3 | 0.0 | 0.0 | 2800.0 | 1800.0 | 1200.0 | 0.0 |

## 3. PHUONG AN KHUYEN NGHI

- Kieu bo tri: **A - Truc giao**
- So coc: **6** (luoi 2 x 3)
- Buoc coc: sx = 3.60 m; sy = 3.60 m
- Ly do chon: Chi kieu Truc giao thoa man dieu kien.

## 4. KIEM TRA HINH HOC

| Ma | Dieu kien | Gia tri | Gioi han | Ty le | KL |
|---|---|---:|---:|---:|:--:|
| R3a | Khoang cach tim-tim >= 3.60 m | 3.60 | 3.60 | 100.0% | DAT |
| R3b | Khoang cach <= 6d | 3.60 | 7.20 | 50.0% | DAT |
| R4x | max|x| + c_min <= Lx/2 | 3.00 | 3.00 | 100.0% | DAT |
| R4y | max|y| + c_min <= Ly/2 | 4.80 | 4.80 | 100.0% | DAT |

## 5. NOI LUC COC THEO TUNG TO HOP  (quy ve Tan)

| TH | N_max (T) | N_min (T) | N_max/[Po] | KL |
|---|---:|---:|---:|:--:|
| 1 | 466.0 | 129.2 | 93.2% | DAT |
| 2 | 443.9 | 110.3 | 88.8% | DAT |
| 3 | 486.9 | 159.7 | 97.4% | DAT |

**To hop chi phoi: TH3** — N_max = 486.9 T / [Po] = 500.0 T → he so su dung = 0.974.

## 6. BANG TONG HOP RANG BUOC

| Ma | Noi dung | Gia tri | Gioi han | KL |
|---|---|---:|---:|:--:|
| R1 | N_max <= [Po] | 486.9 | 500.0 | DAT |
| R2 | N_min >= -[Ct] | 110.3 | - | - |
| R3 | 3d <= khoang cach <= 6d | 3.60 | [3.60, 7.20] | DAT |
| R4 | Tim coc cach mep >= c_min | OK | - | DAT |
| R5/R6 | Mx, My <= [M] | 27.8 | - | - |

## 7. KET LUAN

Phuong an **6 coc** — trang thai **DAT**, he so su dung lon nhat 0.974. De nghi tham tra lai bang MCOC truoc khi phat hanh.

---

## PHU LUC — PHAM VI & GIOI HAN MO HINH

- Luc doc truc: `P_i = N/n + Mx*(y_i-cy)/Ix + My*(x_i-cx)/Iy` (be cung).
- Chua xet: hieu ung nhom coc, do lun, ket cau be (chong thung/uon).
- Ket qua dung cho bo tri so bo/toi uu; thiet ke chi tiet phai chay MCOC/FEM day du.
