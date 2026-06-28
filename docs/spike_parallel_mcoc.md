# Spike 007 — Song song hóa lời gọi MCOC (findings + thiết kế + Go/No-Go)

Tài liệu này là kết quả của một **spike thiết kế** (không phải kế hoạch build toàn
bộ). Mục tiêu: quyết định **CÓ NÊN** song song hóa việc chấm MCOC, **LÀM THẾ NÀO**,
và **CẦN SỬA GÌ TRƯỚC**. Có một **prototype dùng-một-lần** đã commit trong worktree
này để chứng minh khái niệm — **prototype KHÔNG được merge** từ kế hoạch này.

Liên kết bối cảnh:
- Backlog: `docs/vault/4-Vấn đề & Cải tiến/Vấn đề & Cải tiến.md` — mục
  "Song song hóa lời gọi MCOC" (medium): *"MCOCRunner đang tuần tự → song song
  nhiều lõi (mỗi tiến trình out-dir riêng). Tăng tốc ≈ số lõi, giữ chính xác.
  Càng cần khi quét nhiều đường kính."*
- ADR-001 (`docs/vault/3-Quyết định (ADR)/ADR-001 MCOC là oracle duy nhất.md`):
  *"tốc độ đến từ giảm số lần gọi + **song song**, không từ xấp xỉ."*

## TL;DR — Khuyến nghị: **GO**
- Prototype đạt **speedup ≈ 6.0x** trên máy 16 lõi với độ trễ giả lập 0.1 s/lời
  gọi, **CÙNG seed cho ra CÙNG phương án kiến nghị** và **cùng số lần gọi MCOC**
  (79 = 79). Không phát hiện non-determinism trong kết quả quyết định.
- Có **một điều kiện tiên quyết bắt buộc** đã được vá trong prototype: **cô lập
  kết quả** giữa các lời gọi đồng thời (tránh lời gọi A nhặt nhầm file kết quả
  của lời gọi B). Phải làm việc này TRƯỚC khi bật song song.
- Mức công sức cho bản chính thức (mergeable): **nhỏ–trung bình** (xem cuối).

---

## 1. Hiện trạng (đo được)
- **Hoàn toàn tuần tự hôm nay.** `grep -rn "ThreadPoolExecutor|multiprocessing|
  concurrent.futures|Pool(" core io_handlers ui` → **không khớp** (exit 1).
- Điểm song song hóa: `_eval_pop` trong `core/nsga2_optimizer.py` (vòng `for`
  tuần tự, mỗi cá thể 1 lời gọi `evaluate()` → 1 lần gọi MCOC).
- `os.cpu_count()` trên máy chạy spike = **16**.
- Mỗi cá thể NSGA-II và mỗi đường kính trong luồng mở rộng = 1 lời gọi subprocess
  MCOC; đây là phần thống trị thời gian treo (wall-clock).

### Hiểm họa đồng thời đã xác định
`MCOCBlackbox.make_real_evaluator` (`core/blackbox.py`) + `MCOCRunner.run`
(`core/mcoc_runner.py`):
1. `counter[0] += 1` **không nguyên tử** → hai luồng có thể chọn trùng chỉ số/file.
2. Tất cả lời gọi dùng **chung một workdir** `_opt_runs`. `MCOCRunner.run()` suy ra
   `<base>_result.txt`; trên **đường fallback** nó quét cả thư mục tìm
   `*_result.txt` mới nhất theo mtime → dưới đồng thời, lời gọi A có thể nhặt
   nhầm kết quả của lời gọi B. **Đây là điều kiện tiên quyết phải sửa.**

---

## 2. Baseline vs Prototype (số đo)
Harness: `tests/_spike007/bench.py` dựng input giống `tests/test_nsga2_mcoc.py`
(bệ 7.2×13.2, 8 cọc D1.2, 2 tổ hợp tải, Po=500T) rồi chạy `run_nsga2` với evaluator
MCOC thực (stub). Stub chậm là **bản sao** `tests/_spike007/mcoc_stub_slow.py`
(thêm `time.sleep(CALL_DELAY)`), **không sửa** `tests/mcoc_stub.py` đã commit.

Tham số: `pop_size=20, n_gen=10, max_evals=140, seed=1`, **độ trễ giả lập = 0.1 s
mỗi lời gọi MCOC**. Máy: `os.cpu_count() = 16`.

| Chế độ   | Elapsed | n_evals | Phương án kiến nghị            | Pareto |
|----------|---------|---------|--------------------------------|--------|
| serial   | 14.57 s | 79      | A 2×4, sx=sy=3.6, 8 cọc, Pmax=408.34 T | 2 |
| parallel | 2.44 s  | 79      | A 2×4, sx=sy=3.6, 8 cọc, Pmax=408.34 T | 2 |

**Speedup ≈ 6.0x** (lặp lại: 5.96x rồi 6.03x). Lưu ý speedup < 16 vì:
(a) các thế hệ phụ thuộc nhau (rào đồng bộ giữa các thế hệ — chỉ song song trong
một batch); (b) batch đầu (hạt giống) lớn nhưng các batch con bị giới hạn pop_size;
(c) overhead khởi tạo ThreadPool + ghi/đọc file. Với MCOC thực (lời gọi vài giây)
overhead này không đáng kể → speedup thực tế kỳ vọng tiệm cận min(số lõi, kích
thước batch).

### Cách tái lập
```
rm -rf tests/_spike007/_work
python tests/_spike007/bench.py
# Bật/tắt: nsga2_optimizer.PARALLEL_EVAL = True/False (bench tự gạt)
# Tinh chỉnh: SPIKE_MCOC_DELAY=0.2 SPIKE_POP=20 SPIKE_GEN=10 SPIKE_EVALS=140
```

---

## 3. Bằng chứng tính đúng đắn (cùng seed: serial ≡ parallel)
- **Phương án kiến nghị giống hệt**: `('A', 2, 4, 3.6, 3.6, 8, 408.34)` cho cả hai,
  qua 2 lần chạy độc lập. `Phuong an kien nghi GIONG nhau? True`.
- **Số lần gọi MCOC giống hệt**: serial=79, parallel=79 → ngân sách `max_evals`
  được bảo toàn chính xác, không lãng phí cũng không thiếu lời gọi.
- **Vì sao xác định được (deterministic)?** Quyết định NSGA-II chỉ phụ thuộc
  *tập* (spec → kết quả) đã chấm, không phụ thuộc *thứ tự hoàn thành* của các lời
  gọi MCOC trong một batch:
  - Khử trùng spec trong batch trước khi submit ⇒ mỗi spec chấm đúng 1 lần
    (kết quả MCOC ổn định theo input).
  - CV (vi phạm ràng buộc) và việc ghi cache làm **tuần tự sau khi** thu kết quả,
    nên không có cập nhật cache tranh chấp.
  - Sắp xếp non-dominated/crowding dùng giá trị mục tiêu (n, footprint/pmax) — bất
    biến với thứ tự đánh giá.
- **Giới hạn còn lại của non-determinism**: nếu MCOC thực cho kết quả phụ thuộc
  số học dấu phẩy động không ổn định, hai lần chấm CÙNG input có thể lệch nhỏ.
  Điều này có sẵn ở bản tuần tự (không do song song) và được chặn bởi cache (1
  spec chấm 1 lần). Nếu cần "bound" chặt: làm tròn kết quả MCOC theo độ chính xác
  báo cáo trước khi so sánh (đã có round trong `_spec_key`/CV).

---

## 4. Thiết kế cô lập kết quả (ĐIỀU KIỆN TIÊN QUYẾT — bắt buộc)
Xét hai phương án trong plan:
- **Option A — mỗi lời gọi một thư mục con** `_opt_runs/run_<uuid>/`, runner chỉ
  nhìn thư mục đó.
- **Option B — tên file duy nhất** mỗi lời gọi trong workdir chung + khóa kết quả
  strictly theo basename input (không quét cả thư mục theo mtime).

**Chọn Option B.** Lý do:
1. **Tương thích ngược.** Test `tests/test_nsga2_mcoc.py` (và các công cụ/UI) liệt
   kê `*_result.txt` ngay trong `evaluator.workdir` (`_opt_runs`). Option A đẩy
   file kết quả xuống thư mục con ⇒ `os.listdir(workdir)` không thấy ⇒ **test fail
   trên thư mục sạch** (đã quan sát: `AssertionError: MCOC stub khong sinh file
   ket qua`). Option B giữ file ở đúng cấp ⇒ test vẫn pass.
2. **Đường nhanh vốn đã an toàn.** Runner suy ra `result_path = <base>_result.txt`
   từ basename input. Khi tên input đã duy nhất (idx + uuid8) thì `result_path`
   cũng duy nhất ⇒ hai lời gọi không bao giờ đụng nhau ở đường nhanh.
3. **Vá đúng chỗ rủi ro.** Hiểm họa duy nhất còn lại là **đường fallback** quét cả
   thư mục theo mtime. Prototype vá: fallback **chỉ nhận file mang đúng tiền tố
   base** của input hiện tại. Khi base duy nhất, ràng buộc tiền tố loại bỏ nguy cơ
   nhặt nhầm; khi base không duy nhất (gọi tuần tự kiểu cũ) hành vi giữ nguyên.

**`counter` nguyên tử**: bọc `counter[0] += 1` trong `threading.Lock()`. Dù đã có
uuid khử va chạm tên, khóa giữ chỉ số tăng đơn điệu (log/đối soát dễ đọc).

Thay đổi prototype (đã commit, KHÔNG merge):
- `core/blackbox.py` — `make_real_evaluator`: khóa quanh counter; tên input duy
  nhất `"%s_opt%03d_%s" % (base, idx, uuid8)`.
- `core/mcoc_runner.py` — `run()`: fallback mtime-scan chỉ nhận `fn` bắt đầu bằng
  `base.lower() + "_"`.

> Lưu ý vận hành: workdir tích nhiều file `*_opt*_*.txt` + `_result.txt`. Bản chính
> thức nên thêm dọn rác (giữ N gần nhất, hoặc xóa input sau khi đọc kết quả).

---

## 5. Chính sách ngân sách & cache dưới đồng thời
Trong `_eval_pop_parallel` (`core/nsga2_optimizer.py`, prototype):
1. **Giải mã trước** toàn batch → (ind, spec, key, coords).
2. **Khử trùng + lọc cache**: mỗi spec mới (chưa có trong cache, chưa trong batch)
   mới được xét submit ⇒ **mỗi spec chấm MCOC đúng 1 lần**.
3. **Ngân sách `max_evals`**: chỉ submit số spec mới ≤ `max_evals − n_evals` còn
   lại; phần dôi ra chỉ lấy từ cache (giống hệt nhánh "hết ngân sách → dùng cache"
   của bản tuần tự). Vì hạt giống được `_eval_pop` gọi **trước** quần thể ngẫu
   nhiên, chính sách "seeds giành ngân sách trước" được giữ nguyên.
4. **Chấm MCOC song song** chỉ cho các spec mới (phần chậm duy nhất), bằng
   `ThreadPoolExecutor(max_workers = min(os.cpu_count(), số_spec_mới))`.
5. **Tính CV + ghi cache tuần tự** sau khi thu kết quả ⇒ không tranh chấp cache;
   `counters['n_evals'] += len(spec_mới)` cộng một lần ở caller.

**Vì sao Thread, không phải Process?** Việc nặng là **tiến trình con MCOC** (chạy
`subprocess.run`, giải phóng GIL khi chờ I/O/đợi tiến trình con). Dữ liệu (cache,
counters, params) **chia sẻ trong bộ nhớ** — dùng thread tránh chi phí pickling /
IPC của multiprocessing và tránh phải tuần tự hóa params/loads/closure. Tiến trình
con đã là đơn vị song song thực sự ở mức HĐH.

---

## 6. Tương tác với luồng nền UI và luồng mở rộng (quét đường kính)
- **UI** (`ui/main_window.py`): mỗi tác vụ tối ưu chạy trong **một**
  `threading.Thread(daemon=True)` (4 chỗ: dòng 957, 1341, 1505, 2364) để không
  treo GUI. Song song hóa nằm **bên trong** lời gọi `run_nsga2` (mức batch), nên
  **không đổi mô hình luồng UI** — đúng phạm vi plan (out of scope: UI threading).
  Lưu ý: ThreadPool tạo trong worker thread là hợp lệ; chỉ cần đảm bảo callback
  cập nhật GUI vẫn marshal về main thread như hiện tại.
- **Luồng mở rộng** (`core/ext/orchestrator.py::run_extended_optimization`): vòng
  `for dia in table` gọi NSGA-II **tuần tự cho từng đường kính**. Có **hai mức**
  song song:
  - **Mức trong (batch của một đường kính)** — *khuyến nghị làm trước*: tái dùng
    đúng `_eval_pop_parallel`, ít rủi ro, đã chứng minh đúng/nhanh ở spike này.
  - **Mức ngoài (song song nhiều đường kính cùng lúc)** — speedup bổ sung khi
    bảng đường kính dài, nhưng nhân chồng số tiến trình MCOC ⇒ phải **giới hạn
    tổng số worker** (1 pool dùng chung, hoặc semaphore toàn cục) để không quá tải
    CPU/đĩa. Mỗi đường kính đã có input/patch tiết diện riêng nên cô lập file vẫn
    do Option B lo. *Đề xuất*: chỉ làm mức ngoài sau khi mức trong ổn định, và đặt
    trần `max_workers` toàn cục theo `os.cpu_count()`.

---

## 7. Go/No-Go + ước lượng công sức bản chính thức (mergeable)
**Khuyến nghị: GO**, làm theo thứ tự:

1. **(Bắt buộc, tiên quyết) Cô lập kết quả — Option B.** Đưa thay đổi
   `core/blackbox.py` + `core/mcoc_runner.py` của prototype thành bản chính thức,
   thêm dọn rác workdir. *Công sức: ~0.5 ngày.* (Có thể merge độc lập, hữu ích cả
   khi chưa bật song song.)
2. **Song song mức batch** trong `core/nsga2_optimizer.py`: cổng bằng tham số
   (vd `n_jobs`/`parallel`) thay vì biến module toàn cục; mặc định bật khi
   `os.cpu_count() > 1` và đang dùng evaluator MCOC thực (mock nhanh thì không
   cần). Giữ nguyên thuật toán, ngân sách, cache như prototype. *Công sức: ~1
   ngày gồm test.*
3. **Test đồng thời chuyên dụng**: bổ sung test khẳng định serial ≡ parallel cùng
   seed (như bench) + test cô lập (hai lời gọi đồng thời không nhặt nhầm kết quả).
   *Công sức: ~0.5 ngày.*
4. **(Tùy chọn, sau) Song song mức đường kính** trong `core/ext/orchestrator.py`
   với trần worker toàn cục. *Công sức: ~1 ngày.*

**Tổng (mục 1–3, đủ để hưởng phần lớn lợi ích): ~2 ngày.**

**Các file bản chính thức sẽ chạm:**
- `core/blackbox.py` (cô lập tên file + khóa counter)
- `core/mcoc_runner.py` (fallback theo tiền tố + dọn rác)
- `core/nsga2_optimizer.py` (`_eval_pop` song song có cổng tham số)
- `core/ext/orchestrator.py` (tùy chọn, mức đường kính)
- `tests/` (test đồng thời + test cô lập)
- (cân nhắc) truyền `n_jobs` qua `ui/main_window.py` nếu muốn người dùng chỉnh —
  nhưng **không đổi mô hình luồng UI**.

**Rủi ro / lưu ý:**
- MCOC thực có thể tốn RAM/đĩa khi chạy nhiều bản đồng thời → đặt trần worker hợp
  lý (mặc định `min(cpu_count, batch)`), cho phép cấu hình.
- Phải dọn workdir để không phình đĩa (mỗi eval một input + result).
- Nếu MCOC dùng tài nguyên độc quyền (license đơn, file tạm cố định tên) thì giới
  hạn song song hoặc giữ tuần tự — cần xác nhận với MCOC thực (spike này dùng stub).

---

## 8. Trạng thái prototype (KHÔNG MERGE)
Prototype được commit trong worktree này **chỉ để chứng minh khái niệm** và
**KHÔNG được merge** từ plan 007:
- `tests/_spike007/mcoc_stub_slow.py` — bản sao stub + sleep giả lập độ trễ.
- `tests/_spike007/bench.py` — harness đo serial vs parallel + kiểm tra đồng nhất.
- Sửa thử trong `core/blackbox.py`, `core/mcoc_runner.py`, `core/nsga2_optimizer.py`
  (cổng bằng `nsga2_optimizer.PARALLEL_EVAL`, mặc định `False` ⇒ hành vi tuần tự
  giữ nguyên; toàn bộ test hiện có vẫn 22 passed / 2 failed-by-design).

Các sửa core ở trên là **minh họa thiết kế**, không phải bản hoàn thiện; bản chính
thức cần làm theo mục 7 (cổng tham số thay vì biến toàn cục, dọn rác, test riêng).
