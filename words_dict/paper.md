**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

## **THIẾT KẾ TỐI ƯU ĐA MỤC TIÊU CHO KẾT CẤU MÓNG CỌC** 

## ThS. **LÊ QUANG HÒA** 

## Trường Cao đẳng Kỹ nghệ II ThS. NCS. **VÕ DUY TRUNG** , GS. TS. **NGUYỄN THỜI TRUNG** Viện Khoa học Tính toán, Trường Đại học Tôn Đức Thắng 

Tóm tắt: _Nghiên cứu được thực hiện nhằm thiết kế tối ưu đa mục tiêu cho kết cấu móng cọc. Bài toán tối ưu đa mục tiêu được thành lập với hai hàm mục tiêu là thể tích và độ lún của móng cọc. Biến thiết kế là chiều dài cọc và đường kính cọc. Hàm ràng buộc là các ràng buộc về ứng xử kết cấu gồm khả năng chịu tải, độ lún của móng cọc và giới hạn của biến thiết kế. Để giải bài toán thiết kế tối ưu đa mục tiêu cho kết cấu móng cọc, phương pháp được sử dụng trong bài báo là giải thuật NSGA-II (Nondominated Sorting Genetic Algorithm-II)._ 

Từ khóa: _Móng cọc, NSGA - II (Non-dominated Sorting Genetic Algorithm - II), tối ưu hóa đa mục tiêu, tối ưu hóa nền móng._ 

Chỉ số phân loại: _2.1_ 

Abstract: _The paper aims to design multiobjective optimization problems for the pile foundation. The multi-objective optimization problems are established with two objective functions: volume and settlement of the pile foundation. The design variables are pile length and pile diameter. The constraint functions are the behavior constraints of structures including the loadbearing capacity, settlement of pile foundation and the limits of the design variables. To solve multiobjective design optimization problems for the pile foundation, the method used in the paper is NSGA-II (Non-dominated Sorting Genetic Algorithm-II)._ 

Keywords: _Foundation Optimization, multiobjective optimization, NSGA-II (Non-dominated Sorting Genetic Algorithm-II), pile foundation._ 

## Classification number: _2.1_ 

## **1. Giới thiệu** 

Do có những đặc điểm vượt trội, móng cọc đã được sử dụng rộng rãi trong ngành Xây dựng dân dụng và công nghiệp như căn hộ cao cấp, cao ốc văn phòng, chung cư,... Một trong những ưu điểm chính của kết cấu móng cọc là khả năng chịu tải lớn, so với các loại móng khác như móng nông. Ngoài ra, độ ổn định khi sử dụng móng cọc cũng tốt hơn so với móng nông. Tuy nhiên, nhược điểm của 

kết cấu móng cọc là có giá thành xây dựng khá cao, và chiếm một tỷ trọng lớn trong tổng giá thành công trình. Vì vậy trong thực tế, để việc thiết kế và thi công móng cọc vừa đảm bảo độ bền, độ ổn định, cũng như đảm bảo giá thành cạnh tranh, thì việc thiết lập và giải các bài toán tối ưu thiết kế cho kết cấu móng cọc là một vấn đề quan trọng và nhận được sự quan tâm của các nhà nghiên cứu trên thế giới. 

Tổng quát, một bài toán tối ưu có thể có một hay nhiều hàm mục tiêu. Tuy nhiên trong thực tế, hầu hết các trường hợp ra quyết định luôn xem xét sự hòa hợp giữa hai hay nhiều mục tiêu cùng lúc. Do đó, việc áp dụng tối ưu hóa đa mục tiêu để tính toán cho kết cấu là thiết thực và mang lại nhiều lợi ích. Lời giải của bài toán tối ưu hóa đa mục tiêu này sẽ là một tập hợp nghiệm tối ưu, thỏa mãn các mục tiêu đặt ra theo các tỉ lệ ưu tiên hỗn hợp từ 0 đến 1 và tập hợp nghiệm này được gọi là tập nghiệm Pareto [1]. Dạng bài toán tối ưu đa mục tiêu này ta có thể tìm thấy trong một số nghiên cứu điển hình cho các dạng kết cấu, lĩnh vực khác [2] - [5]. 

Riêng với kết cấu móng cọc, cho đến nay phần lớn các công bố nghiên cứu liên quan đến tính toán tối ưu hóa chỉ giải quyết cho bài toán tối ưu đơn mục tiêu, ví dụ các nghiên cứu [6]–[8], nhằm chọn phương án thiết kế móng cọc có hàm mục tiêu thể tích nhỏ nhất hoặc có độ lún thấp nhất; hoặc có một số nghiên cứu về bài toán tối ưu hóa đa mục tiêu, ví dụ như thiết kế tối ưu mô hình làm việc giữa cọc cũ và cọc mới [2], sử dụng giải thuật tiến hóa khác biệt DE hay thiết kế tối ưu đa mục tiêu cho kết cấu cột đá trên nền đất yếu [4]. Điều này cho thấy, việc thiết kế tối ưu hóa đa mục tiêu cho kết cấu móng cọc vẫn chưa được quan tâm đúng mức. Vì vậy, nghiên cứu hiện tại sẽ tập trung vào khe hẹp nghiên cứu này nhằm thành lập và giải bài toán thiết kế tối ưu đa mục tiêu cho kết cấu móng cọc, trong đó hàm mục tiêu bao gồm cực tiểu thể tích móng cọc (gồm: cọc và đài cọc) và độ lún của móng cọc. Biến thiết kế bao gồm chiều dài cọc _Lc_ và đường kính cọc _Dc_ . Ràng buộc về giới hạn khả năng chịu tải _Pmax_ và ràng buộc về giới hạn độ lún _Smax_ . Giải thuật di truyền sắp xếp không trội (Non-dominated Sorting 

50 _Tạp chí KHCN Xây dựng - số 3/2018_ 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

Genetic Algorithm-II, NSGA-II) được trình bày bởi Kalyanmoy Deb vào năm 2002 [9], sẽ được sử dụng trong bài báo để giải bài toán tối ưu đa mục tiêu được thành lập. Đây là một phương pháp có thời gian tính toán khá nhanh và không có nhiều tham số điều khiển. 

## **2. Tính toán khả năng chịu tải của móng cọc** _**2.1 Khả năng chịu tải của cọc theo cường độ vật liệu**_ 

Sức chịu tải của cọc theo vật liệu được tính theo công thức [10]: 

**==> picture [168 x 11] intentionally omitted <==**

## _**2.2 Khả năng chịu tải của cọc theo chỉ tiêu cường độ đất nền**_ 

Sức chịu tải của cọc gồm hai thành phần: ma sát bên (hay sức kháng hông) và sức chống dưới mũi cọc (hay sức chịu mũi). Ước lượng sức chịu tải _Qu_ của cọc được tính bởi phương trình [11]: 

**==> picture [123 x 12] intentionally omitted <==**

trong đó: _Qu_ kN - khả năng chịu tải cực hạn của cọc, _Qs_ kN - khả năng ma sát bên, _Qp_ kN - khả năng chịu mũi của cọc và được lấy theo công thức: _Qp_  _Ap_ ( _cNc_  _q N ' q_  _DbN_ ) (3) trong đó: _Nc_ , _Nq_ , _N_ - các hệ số sức chịu tải, lấy theo Vesic (1973) [11]. 

Khả năng ma sát bên _Qs_ kN được tính tương tự như cọc đóng, cọc ép theo công thức: 

**==> picture [155 x 15] intentionally omitted <==**

> Lực ma sát đơn vị _[f] s_[ được tính dựa trên ] nguyên lý sức chống cắt của đất, sức kháng hông đơn vị có thể xác định bởi: 

**==> picture [195 x 11] intentionally omitted <==**

> trong đó: _ca_ là lực dính giữa đất và cọc; đối với cọc 

> đóng bê tông cốt thép _ca_  _c_ ; đối với cọc thép _ca_  0,7 _c_ , với _c_ là lực dính của đất; __ là góc ma sát giữa đất và cọc; đối với cọc đóng bê tông hạ bằng phương pháp đóng __  __ ; đối với cọc ma sát __  0,7 __ , với __ là góc ma sát của đất; _K_ là hệ số áp lực ngang của đất, _K_  _K_ 0  1 sin __ ; _ ' v_ là 

ứng suất có hiệu theo phương thẳng đứng ở độ sâu _z_ . 

_Chọn hệ số an toàn và tính sức chịu tải cho phép:_ Hệ số an toàn đối với sức chịu ma sát bên chọn _FSs_  1,5  2,0 ; hệ số an toàn đối với sức chịu mũi chọn _FSp_  2,0  3,0 . Hệ số an toàn 

> chung: _FS_ . 

**==> picture [222 x 92] intentionally omitted <==**

_Xác định sơ bộ kích thước đài cọc:_ 

**==> picture [221 x 114] intentionally omitted <==**

_Xác định số lượng cọc sơ bộ trong đài cọc:_ Tổng lực dọc tính toán sơ bộ ở đáy đài: _N t1_  _N tt_  _W sb_ . Số lượng cọc chọn sơ bộ [10]: _N t1 n_  _ Pctk_ , trong đó __ là hệ số xét đến ảnh hưởng 

> của mô-men tác động lên móng cọc, __  1,0  1,5 . _Cấu tạo và tính toán đài cọc:_ Khoảng cách giữa các 

> tim cọc: _C_  3 _Dc_ . Khoảng cách giữa mép cọc và 

> đài: _C'_  0,3 _Dc_ và _C'_  0,15 m . Chiều dài đài cọc: _Adai_   _n_ 1  1 _C_  _Dc_  2 _C '_ . Chiều rộng đài cọc: _Bdai_   _n_ 2  1 _C_  _Dc_  2 _C '_ . Diện tích đáy đài thực tế: _Fdc_  _Adai Bdai_ . Chiều cao làm việc của đài: _H 0 d_  _Hdc_  _abv_ . _Kiểm tra lực tác dụng lên đầu cọc:_ Trọng lượng 

> đài và đất phủ lên đài: _Wdc_  1,1 _FdctbHdc_ . Tổng lực _t2 tt_ dọc tính toán đáy đài: _N_  _N_  _Wdc_ . Mô-men:  _Mdx dy_ ,  _Mx_ , _y_  _Qy_ , _xHdc_ . Xác định lực tác dụng lên đầu cọc lớn nhất _p_ max và lực tác dụng lên đầu cọc nhỏ nhất _p_ min . Các giá trị _p_ max và _p_ min phải thỏa mãn điều kiện (12). 

Tải trọng tác dụng lên đầu cọc: 

**==> picture [406 x 29] intentionally omitted <==**

_Tạp chí KHCN Xây dựng - số 3/2018_ 51 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

Lực tác dụng vào đầu cọc phải thỏa:[]  _P_ max  _Pctk_ (12)  _P_ min  0 

_Kiểm tra điều kiện ổn định:_ Theo nghiên cứu [10], sức chịu tải tính toán theo trạng thái giới hạn thứ _RII_ của đất nền, được tính bởi công thức: 

**==> picture [385 x 29] intentionally omitted <==**

trong đó _m_ 1, _m_ 2 lần lượt là hệ số điều kiện làm việc của đất nền và nhà hoặc công trình có tác dụng qua lại với nền [12], hoặc được tính theo công thức sau [10]: 

**==> picture [421 x 95] intentionally omitted <==**

Vậy điều kiện đất nền được thỏa mãn khi: 

nền có mô-đun biến dạng _E_  5 MPa . Để bài toán tính lún đạt độ chính xác cao, vùng nén lún được chia thành nhiều lớp nhỏ, mỗi lớp phân tố có bề dày nhỏ hơn 0,4  bề rộng móng. Xác định ứng suất gây lún do trọng lượng bản thân tại đáy móng khối quy ước _pbt_  _Df ' II_ .  Ứng suất gây lún do tải trọng tại đáy móng quy ước _ptt_  _k_ 0 _pgl_ , với _pgl_  _ ' gl_ và hệ số _k_ 0 [12] được tính theo công thức sau: 

## **3. Tính toán độ lún của móng cọc** 

**==> picture [200 x 12] intentionally omitted <==**

Tính áp lực gây lún chính: 

_ ' gl_  _ ' tb_  _Df ' II_ (17) Chiều dày vùng nén lún được xác định một cách quy ước, kể từ đáy móng quy ước dưới móng cọc đến chiều sâu _z_ , thỏa điều kiện: _ ' gl_ ( _z_ )  0,2 _ ' bt_ ( _z_ )[, đối với đất nền có mô-đun biến ] dạng _E_  5 MPa ; _ ' gl_ ( _z_ )  0,1 _ ' bt_ ( _z_ )[, đối với đất ] 

**==> picture [434 x 70] intentionally omitted <==**

> trong đó: _Smax_ là độ lún lớn nhất của đất nền dưới đáy móng khối quy ước;  _S gh_ là độ lún giới hạn của nền 

> móng công trình [12],  _S gh_  8 cm . 

> Vậy độ lún của móng cọc phải thỏa điều kiện: _S max_[]  _S gh_ (20) 

**4. Giải thuật tối ưu hóa đa mục tiêu NSGA – II** [9] 

## _**4.1 Khái niệm đường Pareto**_ 

Bài toán tối ưu đa mục tiêu có nghiệm là một chuỗi nghiệm và tập hợp nghiệm này gọi là nghiệm Pareto [13]. Minh họa đường Pareto được thể hiện như hình 1. 

52 _Tạp chí KHCN Xây dựng - số 3/2018_ 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

**Hình 1.** _Mô tả tập hợ_ _**p** nghiệm Par_ _**e** to_ 

## _**4.2 Khái niệm về sự trội (Domination)**_ 

Hầ **u** hết các th **u** ật toán tối **ư** u đa mục **t** iêu đều sử dụn **g** khái niệm **v** ề sự trội. **T** rong các g **i** ải thuật này, hai cá thể (ng **h** iệm) được lấy để so sánh với nhau. 

**** 1 _Địn_ _**h** nghĩa_ : M **ộ** t nghiệm _x_ được xe **m** là trội 2 so với **n** ghiệm _x_ **,** nếu cả hai điều kiện _**a**_ và _b_ sau đều thỏa: 1  **2**  _a._ Nghi **ệ** m _x_ kh **ô** ng xấu hơn nghiệm _x_ trong tất cả các giá t **r** ị của hà **m** mục tiê **u** , hoặc _[f] j_  _x_ 1  **[]** _[f] j_  _x_ 12  v **ớ** i _j_  1,2,..., _M_ . 2 _b._ Nghi **ệ** m _x_ ph **ả** i tốt hơn n **g** hiệm _x_ trong ít nhất m **ộ** t mục tiêu, hoặc _x_ **** 1  _x_ 2 với ít _[f] j_   _[f] j_  **** nhất mộ **t** _j_ 1,2,..., _M_  . 

Nếu bất kì các đi **ề** u kiện ở trên bị vi ph **ạ** m, 1 2 **n** ghiệm _x_ không trội s **o** với nghiệ **m** _x_ . 

## _**4.3 Giải thuật NSGA – II [9]**_ 

Giải thuật NSGA – II được hìn **h** thành và **p** hát **t** riển dựa trê **n** phương p **h** áp NSGA (Non-Domin **a** ted **S** orting Genetic Algo **r** ithm) và GA (Genetic **A** lgorithm). **D** o vậy giải t **h** uật này kh **ô** ng những k **h** ắc **p** hục được **n** hững hạn **c** hế của NS **G** A mà còn **đ** ảm **b** ảo sự đa dạng và duy trì được cá **c** cá thể tốt **q** ua **c** ác thế hệ. **Q** uá trình lự **a** chọn số lượng cá thể **m** ới **c** ủa giải thu **ậ** t NSGA – I **I** được thực hiện theo t **r** ình **t** ự như sơ đ **ồ** giải thuật t **r** ong hình 2. 

**Hình 2** . _**S** ơ đồ giải th_ _**u** ật NSGA - II_ _**[** 14]_ 

_Tạp chí KHCN Xây dựng - s_ _**ố** 3/2018_ 

53 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

Trong giải thuật NSG **A** -II, để tạo **q** uần thể b **a** n đầu, trước tiê **n** quần thể **c** on _Qt_ sẽ đ **ư** ợc tạo bằ **n** g cá **c** h kết hợp **q** uần thể bố **m** ẹ _[P] t_[. Tuy ] nhiên, thay **v** ì ch **ỉ** tìm các cá **t** hể không bị trội của qu **ầ** n thể con _**Q** t_ thì hai quần thể _[P] t_[ và ] _**[Q]** t_[ sẽ được ] kết hợp v **ớ** i nhau, để tạo r **a** quần thể _**R** t_[ có kích th] **[ư]** ớc 2 _N_ . S **a** u đó, sử dụng p **h** ương phá **p** sắp xếp cá thể không **b** ị tr **ộ** i để phân l **o** ại toàn bộ **d** ân số của quần thể _R_ _**t**_ . K **h** i thực hiện phân loại **c** ác cá thể trên _Qt_ , gi **ả** i th **u** ật NSGA-II cho phép ki **ể** m tra cá th **ể** không bị tr **ộ** i tr **o** ng toàn bộ cá thể bao gồm tập h **ợ** p các cá t **h** ể 

con v **à** cha mẹ. **S** au khi ph **â** n loại được cá thể không bị trội tốt nh **ấ** t ta thu đư **ợ** c lớp 1. Tiếp tục sắp xếp kh **ô** ng bị trội v **à** phân loại **c** ác cá thể c **ò** n lại của _Rt_ ta **t** hu được lớ **p** 2 và cứ th **ế** tiếp tục ta thu được lớp 3.. **.** Nhưng vì kích thước d **â** n số của _**R** t_[ là ][2] _[N]_[ , ] nên không phải tất cả các lớp sẽ nằm tro **n** g dân số mới c **ó** kích thướ **c** là _N_ . D **o** đó, nhữn **g** lớp mà không nằm trong **d** ân số mới **t** hì sẽ bị loại bỏ. Quá trình p **h** ân loại cá **t** hể để tạo r **a** bộ dân số mới của giải th **u** ật NSGA-II được thực **h** iện theo trì **n** h tự như hình 3. 

**Hình 3.** _Sơ đồ phân loại_ _**c** á thể của gi_ _**ả** i thuật NSGA-II [9]_ 

Vì vậy đi **ể** m quan trọ **n** g trong giải thuật là n **ế** u số lượng cá t **h** ể trong _[F]_ 1 **[l]** à _N_ cá thể, thì quần t **h** ể _[P] t_ **** 1[ sẽ bao g] **[ồ]** m tất cả cá **c** cá thể của _[F]_ 1[, không ] **[b]** ổ sung thêm cá thể từ lớp _**F**_ 2, _F_ 3,... nữ **a** . Như vậy **s** ố lầ **n** tính toán c **ủ** a giải thuật sẽ giảm đi **đ** áng kể. Sau khi c **ó** được quầ **n** thể dân số ban đầu, vi **ệ** c đánh giá hàm **m** ục tiêu và **x** ếp hạng cá **c** cá thể tro **n** g quần thể sẽ **đ** ược thực **h** iện, thông qua việc l **ự** a ch **ọ** n, lai tạo v **à** đột biến t **r** ong quần t **h** ể con. Từ **đ** ó tì **m** được nhữ **n** g cá thể ư **u** việt nhất. Để minh h **ọ** a cụ thể cho gi **ả** i thuật NS **G** A – II, cá **c** ví dụ số **s** ẽ đ **ư** ợc trình bà **y** ở phần kế **t** iếp. **5. Ví dụ số** 

Phần này trình bày k **ế** t quả tính t **o** án số cho **b** a bài toán, trong đó bài toán 1 nhằm kiể **m** chứng co **d** e lậ **p** trình Mala **b** cho giải t **h** uật NSGA-II; bài toán 2 

nhằm **t** ính toán kh **ả** năng chịu **t** ải của món **g** cọc; bài toán 3 nhằm thiết kế tối ưu **đ** a mục tiê **u** kết cấu móng **c** ọc sử dụng giải thuật N **S** GA-II. 

## _Bài to_ _**á** n 1: Kiểm tr_ _**a** code lập t_ _**rì** nh matlab:_ 

Đ **ể** chứng mi **n** h sự đúng **đ** ắn của co **d** e Matlab cho p **h** ương phá **p** NSGA-II **v** à minh họ **a** cụ thể đường nghiệm Pareto ở mục 4.1. Phần này trình bày m **ộ** t ví dụ điển hình cho k **ế** t cấu dầm [13] được thể hiện như hình **4** . Hàm mụ **c** tiêu của bài toán lần lượt là cực tiểu tr **ọ** ng lượng **v** à cực tiểu **c** huyển vị cho kết cấu dầm; **h** àm ràng b **u** ộc yêu cầu ứng suất lớn n **h** ất phải nh **ỏ** hơn ứng suất cho phép và chuyể **n** vị lớn nh **ấ** t phải nhỏ hơn chuy **ể** n vị cho phép; **b** iến thiết kế là đường kí **n** h _d_ và chiều dài _l_ . Thông số chi tiết **c** ủa bài toá **n** được trình bày như bảng 1. 

**Hình 4.** _Sơ đ_ _**ồ** chịu lực kết_ _**c** ấu dầm_ 

_Tạp chí KHCN Xâ_ _**y** dựng - s_ _**ố** 3/2018_ 

5 **4** 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

||**Bảng 1.**|**Bảng 1.**_Thông số đầu vào của bài toán_|**Bảng 1.**_Thông số đầu vào của bài toán_|**Bảng 1.**_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|_Thông số đầu vào của bài toán_|||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Hàm mục tiêu|Min <br>1<br>_f _||<br><br>,<br> _d l_|__<br>4<br>_d_|2||_l_ ;|Min|<br>2<br>_f_|,<br>_d l_||__<br><br>3<br>4<br>64<br>3<br>_Pl_<br>_E d_|||||.|
|Hàm ràng buộc|_max_<br>__||__<br>3<br>32<br>_Pl_<br>_d_|<br>__<br>||;|__<br>;|__<br><br>3<br>4<br>64<br>3<br>_Pl_<br>_E d_|||||<br>__|||||
||<br>10|_d_|<br>50 mm; 200|50 mm; 200|50 mm; 200|<br>50 mm; 200<br>_l_|||<br>1000 mm||||1000 mm|||||
|Biến thiết kế|<br><br>**x**|<br>,<br>_d l_||||||||||||||||
|Số lượng cá thể|100|||||||||||||||||
|Số lượngthế hệ|100|||||||||||||||||



> Các thông số vật liệu bài toán được lấy như sau: __  7800 kG/m3 ; _P_  1 kN ; _E_  207 GPa ; 

-  __  300 MPa ;  __  5 mm . 

Kết quả giải bài toán tối ưu được thể hiện như hình 5. Kết quả này cho thấy nghiệm pareto tối ưu trong ví dụ tương đồng với kết quả tham khảo của Kalyanmoy Deb [20]. Điều này cho thấy code matlab của giải thuật NSGA-II được sử dụng trong bài báo là đáng tin cậy. 

**==> picture [274 x 235] intentionally omitted <==**

**----- Start of picture text -----**<br>
2,5<br>A(0,44; 2,03)<br>2<br>1,5 B(0,58; 1,17) E(2,02; 1,21)<br>Y  ¢ |<br>1<br>0,5 C(1,43; 0,19)<br>D(3,06; 0,04)<br>0<br>0 0,5 1 1,5 2 2,5 3 3,5<br>Trọng lượng W (kG)<br>Hình 5.  Kết quảnghiệm Pareto tối ưu<br>**----- End of picture text -----**<br>


Mặt khác để làm rõ hơn về khái niệm trội trong giải thuật NSGA – II ở mục 1.1, bài báo sẽ sử dụng 5 nghiệm nằm trên đường Pareto được thể hiện ở hình 5 để so sánh. Kết quả cho thấy nghiệm A có trọng lượng _Wmin_ kG và chuyển vị  _max_ mm , nghiệm D có trọng lượng _Wmax_ kG và chuyển vị  _min_ mm . Điều này có nghĩa không có nghiệm nào vượt trội hoặc tốt hơn giữa hai nghiệm này. Khi xảy ra điều này, hai nghiệm A và D gọi là nghiệm không bị trội. Tương tự xét cho hai nghiệm kế tiếp là B – D và C – D. Như vậy cả 4 nghiệm A, B, C, D đều có thể so sánh trong cả 2 mục tiêu. Ngoài ra, khi so sánh nghiệm E với C, ta thấy rằng nghiệm C tốt hơn cả hai mục tiêu so với 

nghiệm E, nên ta nói nghiệm C trội hơn nghiệm E hoặc nghiệm E bị trội bởi nghiệm C. Tiếp tục so sánh nghiệm D với E, ta thấy mục tiêu thứ hai của nghiệm D tốt hơn nghiệm E, nhưng ngược lại mục tiêu thứ nhất của nghiệm E lại tốt hơn nghiệm D. Như vậy trong trường hợp nếu không có các nghiệm A, B, C và bất kỳ nghiệm không bị trội nào khác, thì nghiệm E sẽ thuộc cùng nhóm với nghiệm D. Nhưng thực tế cho thấy nghiệm C và D là không bị trội với nhau, mà nghiệm E là một nghiệm bị trội bởi C. Vì vậy nghiệm E chưa tối ưu và là một nghiệm bị trội. Điều này đúng với khái niệm của nghiệm tối ưu đa mục tiêu như đã trình bày. 

_Tạp chí KHCN Xây dựng - số 3/2018_ 55 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

**Bảng 2.** _So sánh kết quả nghiệm tối ưu của bài toán_ 

|Nghiệm|Đường kính|Đường kính<br><br>mm<br>_d_||Chiều dài<br><br><br>mm<br>_l_|Chiều dài<br><br><br>mm<br>_l_|Chiều dài<br><br><br>mm<br>_l_|Khối lượng<br><br>kG|Khối lượng<br><br>kG|Chuyển vị|Chuyển vị|<br>mm|
|---|---|---|---|---|---|---|---|---|---|---|---|
||_Tham_<br>_khảo [20]_|_Bài_<br>_báo_||_Tham_<br>_khảo [20]_|_khảo [20]_|_Bài_<br>_báo_|_Tham_<br>_khảo [20]_|_khảo [20]_<br>_Bài báo_|_Bài báo_<br>_Tham_<br>_khảo [20]_|_khảo [20]_<br>_Bài báo_||
|A|18,94|**18,95**||200||**200**|0,44|**0,44**|2,04||**2,03**|
|B|21,24|**21,84**||200||**200**|0,58|**0,58**|1,18||**1,15**|
|C|34,19|**34,14**||200||**200**|1,43|**1,43**|0,19||**0,19**|
|D|50,00|**50,00**||200||**200**|3,06|**3,06**|0,04||**0,04**|
|E|33,02|**33,52**||362,49|<br>**302,43**||<br>2,42|**2,02**|1,31||**1,21**|



_Bài toán 2: Thiết kế khả năng chịu tải của móng cọc:_ 

Trong phần này, các thông số đầu vào của bài toán sẽ dựa trên số liệu địa chất thực tế của Dự án Riverside Thủ Đức đã được nghiên cứu trước đó [15]. Móng cọc trong bài báo được tính 

toán dựa trên nền đất của hố khoan 1 (HK1). Mực nước tĩnh đo được tại hố khoan HK1 là 0,4 m . Các thông số về đặc điểm địa chất và đặc trưng cơ lý của các lớp đất được trình bày trong các bảng 3 và bảng 4. 

**Bảng 3.** _Thông số dữ liệu địa chất_ 

||||**Bảng 3.**_Thông số dữ liệu địa chất_|_Thông số dữ liệu địa chất_|_Thông số dữ liệu địa chất_|_Thông số dữ liệu địa chất_|||
|---|---|---|---|---|---|---|---|---|
|**Lớp**|||**Lớp đất**|||**Bề dày lớp**<br><br>m|**Giá trị xuyên tiêu**<br>**chuẩn SPT-N.**||
|Lớp A||Đất san nền, xà bần|Đất san nền, xà bần|||2,2||0|
|Lớp 1||Bùn sét xám xanh đen, trạng thái chảy||||15,6|0÷14||
|Lớp 2||Cát pha, trạng thái dẻo||||13,0|11÷31||
|Lớp 3||Sét pha, trạng thái dẻo mềm||||3,9|13÷29||
|Lớp4||Sét,trạngthái nửa cứng||||>23,7|14÷33||
||||**Bảng 4.**_Đặc trưng cơ lý của các lớp đất_||||||
|||**Chỉ tiêu cơ lý**|**Chỉ tiêu cơ lý**|_Lớp 1_||**Lớp đất**<br>_Lớp 2_<br>_Lớp 3_||_Lớp 4_|
|Dung trọng tự nhiên|Dung trọng tự nhiên<br><br>__<br>3<br>kN/m<br>_unsat_|||14,6||19,5|19,5|19,0|
|Dung trọng đẩy nổi||Dung trọng đẩy nổi<br><br><br>__<br>3<br>' kN/m||4,8||10,1|10,0|9,1|
|Mô-đun đàn hồi||Mô-đun đàn hồi<br><br><br>2<br>kN/m<br>_E_||800||8050|26070|43650|
|Lực dính<br><br>2<br>kN/m<br>_c_||||5,7||9,0|20,0|26,5|
|Góc nội ma sát||Góc nội ma sát<br>__<br>0||3039’||22020’|10047’|12010’|
|Các thông số về tải trọng và vật liệu được thể hiện ở bảng 5 và bảng 6.||||||Các thông số về tải trọng và vật liệu được thể hiện ở bảng 5 và bảng 6.|||



. 

**Bảng 5.** _Thông số tải trọng_ 

|||||||**Bảng 5.**_Thông số tải trọng_|**Bảng 5.**_Thông số tải trọng_|_Thông số tải trọng_|_Thông số tải trọng_|_Thông số tải trọng_|_Thông số tải trọng_|||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|**Lực dọc**|**Lực dọc**|_N_|**Mô-men**||_x_<br>_M_|**Mô-men**||_M_|_y_<br>|**Lực cắt**||**Lực cắt**<br>_x_<br>_Q_||**Lực cắt**||**Lực cắt**<br>_y_<br>_Q_||
||<br>kN|||kNm|<br>||kNm|<br>|||kNm||<br>||kNm||<br>|
|29600||||1500|||390||||150||||90|||



**Bảng 6.** _Thông số vật liệu bê tông - cốt thép của cọc_ 

|||**Bảng 6.**_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_|_Thông số vật liệu bê tông - cốt thép của cọc_||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
||||||**Cường độtính toán**||||**Mô-đun đàn h**|||**Mô-đun đàn hồi**||
|**Đặc tính**|||_R_|_b_|<br><br>MPa|<br>MPa<br>_bt_<br>_R_|||_E_|<br>3<br>x10<br>MPa<br>_b_||||
|Bê tông cọc nhồi B30 (M400)|||||17|1,2|||||32,5|||
||||||Cường độchịu kéo||||Cường độchịu nén||Cường độchịu nén|||
|Cốt thép CIII, AIII<br>10||40|Thép dọc<br><br><br>MPa<br>_s_<br>_R_|||Thép ngang<br><br><br>MPa<br>_sw_<br>_R_||||_sc_<br>_R_|<br>MPa|||
||||||365|290|||||365|||



56 _Tạp chí KHCN Xây dựng - số 3/2018_ 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

Thi **ế** t kế sơ bộ cho móng cọc gồm 6 c **ọ** c, có đườn **g** kính _Dc_  1,0 m và c **á** c thông số **k** ích thước **h** ình học của đài cọc đư **ợ** c minh họa **n** hư hình 6. 

**Hình 6.** _Mặt_ _**b** ằng móng c_ _**ọ** c điển hình (_ _**B** lock C)_ 

Cá **c** thông số của bài toán như chỉ tiê **u** cơ lý và c **ư** ờng độ đất nền , , _c_ ****  hoặc tải trọng tác đ **ộ** ng  _N_ , _M_ , _Q_  được x **e** m là các gi **á** trị tiền địn **h** khi giải bài toán thiết kế. Trong ng **h** iên cứu nà **y** , dựa trên **đ** iều kiện thi **c** ông thực t **ế** , các tác gi **ả** đã chọn h **a** i loại đườn **g** kính 1,0 m và 1,2 m **đ** ể thiết kế ban đầu cho cọc khoan nhồi điển hìn **h** . Tuy nhiê **n** , khi thiết k **ế** tối ưu đa **m** ục tiêu, tá **c** giả sẽ khả **o** sát cho tấ **t** cả các trư **ờ** ng hợp củ **a** đường kín **h** cọc _Dc_  **** 0,6 m  1, 2 m , để g **i** úp cho người thiết kế **c** ó nhiều cơ sở lựa chọ **n** và đánh gi **á** các phươn **g** án thiết kế. Sơ đồ tính toán: 

**Hình 7.** _**S** ơ đồ khối tín_ _**h** toán kết qu_ _**ả** số_ 

**Bảng 7.** _B_ _**ả** ng tổng hợp_ _**k** ết quả sức c_ _**h** ịu tải cọc theo cường độ v_ _**ậ** t liệu_ 

|Đư**ờ**<br>ng kính cọc<br>_c_<br>_D_ <br>m|ng kính cọc<br>**C**<br>ấu tạo cốt th**é**<br>chịu lực<br>p|ng kính cọc<br>**C**<br>ấu tạo cốt th**é**<br>chịu lực<br>p|ng kính cọc<br>**C**<br>ấu tạo cốt th**é**<br>chịu lực<br>p|_T_**_h_**<br>Sức chịu**t**<br>_am khảo [15]_<br>ải|_T_**_h_**<br>Sức chịu**t**<br>_am khảo [15]_<br>ải|_T_**_h_**<br>Sức chịu**t**<br>_am khảo [15]_<br>ải|ải<br>_vl_<br>_Q_ |<br>kN <br>_Bài_**_b_**<br>_áo_|Sự khác biệ**t**<br><br><br>%|
|---|---|---|---|---|---|---|---|---|---|
|1,2||<br>18<br>20|||8030|||802**9**<br>,91|0,001|
|1,0||<br>22 25|||7090|||708**8**<br>,22|0,025|
|0,8||<br>12 22|||4020|||401**9**<br>,48|0,013|
|0,6||<br>10 18|||2260|||225**6**<br>,29|0,164|



_Tạp chí KHCN Xây dựng - s_ _**ố** 3/2018_ 

57 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

**Bảng 8.** _Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_ 

||||**Bảng 8.**_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_|_Bảng tổng hợp kết quả sức chịu tải cọc theo đất nền_||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Chiều dài cọc<br>_c_<br>_L_ <br>m|||Đường kính cọc<br>_c_<br>_D_<br><br>m|_s_<br>_Q_ <br><br>kN|||_p_<br>_Q_ <br><br>kN||_u_<br>_Q_ <br><br>kN||||_a_<br>_Q_ <br><br>kN|
||55||1,2|1,2877<br>_e_||4|1745,78||<br>1,4623<br>4<br>_e_||||**7020,63**|
||||1,0|1,0731<br>_e_||4|1209,88||<br>1,1941<br>4<br>_e_||||5768,88|
||58||1,2|1,4178<br>_e_||4|1792,03||1,5970|<br>4<br>_e_|||7686,24|
||||1,0|1,1815<br>_e_||4|1242,00||1,3057|<br>4<br>_e_|||6321,41|
||63||1,2|1,6461<br>_e_||4|1869,12||1,8330|<br>4<br>_e_|||8853,43|
||||1,0|1,3717<br>_e_||4|1295,54||1,5013|<br>4<br>_e_|||**7290,50**|
||||**Bảng 9.**_Bảng tổng hợp kết quả tính toán kiểm tra đài móng cọc_|_Bảng tổng hợp kết quả tính toán kiểm tra đài móng cọc_|||||_Bảng tổng hợp kết quả tính toán kiểm tra đài móng cọc_|||||
|||_dai_<br>_A_|_dai_<br>_B_<br>_a_<br>_Q_|max<br>_P_||_tc_<br>_R_<br>_tb_||||_max_|||_max_<br>_S_|
|Loại cọc||<br>m|<br>m <br><br><br>kN|<br><br>kN||<br><br>2<br>kN/m<br><br>2<br>kN/m|||<br><br>kN/m||2||<br>m|
|||||Tham khảo||[15]||||||||
|1,2<br>_c_<br>_D_<br>;<br>55 m<br>_cL_||9,4|5,8<br>**7020**|5550||2844,2 <br>696,3||||721,3|||0,0396|
|_D_<br>_cL_|1,0<br>_c_<br>;<br>63 m|8,0|5,0<br>**7290**|5490||3221,7 <br>768,4||||797,1|||0,0397|
|||||Bài báo||||||||||
|1,2<br>_c_<br>_D_<br>;<br>55 m<br>_cL_||9,4|5,8<br>**7020,63**|5559||2844,7 <br>690,5||||714,4|||0,0391|
|1,0<br>_c_<br>_D_<br>;<br>63 m<br>_cL_||8,0|5,0<br>**7290,50**|5471||3221,6 <br>768,2||||796,9|||0,0397|



Kết quả tính toán trong bảng 7, bảng 8 và bảng 9 cho thấy, việc tính toán bài toán thiết kế tiền định trong bài báo hoàn toàn tương đồng với kết quả của nghiên cứu trong tài liệu [15]. Sự sai lệch kết quả là không đáng kể. Cụ thể, sức chịu tải của cọc theo vật liệu có sự khác biệt nhỏ nhất là 0,001%  và lớn nhất 0,164% , còn sức chịu tải theo đất nền có sự khác biệt chưa đến 0,1% . Vì vậy sức chịu tải của cọc được chọn theo thiết kế là _Qa_  7000 kN (kết quả 

này phù hợp với kết quả kiểm tra bằng thử tĩnh tại hiện trường do Công ty Vista - Hà Nội cung cấp). Kết quả này một lần nữa cho thấy phương pháp tính toán thiết kế móng cọc trong bài báo là đáng tin cậy và sẽ được sử dụng để tìm nghiệm tối ưu cho bài toán thiết kế tối ưu đa mục tiêu kết cấu móng cọc. 

_Bài toán 3: Thiết kế tối ưu đa mục tiêu kết cấu móng cọc:_ 

Bài toán thiết kế tối ưu đa mục tiêu cho kết cấu móng cọc được trình bày như sau: 

|**Hàm mục tiêu**|**Hàm mục tiêu**|**Min**|**Min**<br>1(<br>,<br>_c_<br>_c_<br>_f D L_|)|<br>min|<br>min|<br>_V_|<br><br> **X**|;**Min**|;**Min**|**Min**<br>2<br>_f_|**Min**<br>2<br>_f_|<br>_c_<br>_D _|,<br>_c_<br> _L_||||min|min|min|<br>_S_|<br><br> **X**|<br><br> **X**|<br><br> **X**||||||
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Hàm ràng buộc|Hàm ràng buộc|<br><br>1<br>max<br>,<br>_c_<br>_c_<br>_g_<br>_D L_<br>_P_<br><br><br>0,6 m<br>1,2 m<br>_c_<br>_D_||||<br>_u_<br>_Q_<br>1,2 m<br>;||<br>0<br>;<br>30 m|;<br>_g_<br>|<br>2<br>_c_<br>_D _<br><br>_c_<br>_L_||<br>,<br>_c_<br> _L_<br>100 m||<br>_S_ <br>100 m<br>.||<br> **X**<br>.||||0,08||||0|;<br>min<br>_P_|||0|;|
|Biến thiết kế|Biến thiết kế|<br>**X**|<br><br>,<br>_c_<br>_c_<br>_D L_|||||||||||||||||||||||||||



Trong phần này, các tác giả sẽ giải bài toán tối ưu đa mục tiêu cho móng cọc gồm 6 cọc, với số lượng cá thể/ thế hệ là 100/1000. Hàm mục tiêu là cực tiểu thể tích _V_  **X** và cực tiểu độ lún móng cọc 

> _S_  **X** ; hàm ràng buộc gồm các ràng buộc về khả năng chịu tải, độ lún và giới hạn biến thiết kế. Trong 

> đó biến thiết kế chiều dài  _[L] c_  được khảo sát trong 

> khoảng 30 m; 100 m và đường kính được khảo 

58 _Tạp chí KHCN Xây dựng - số 3/2018_ 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

## sát trong khoảng 0,6 m; 1,2 m . 

Kết quả tính toán trong hình 8 cho thấy, nghiệm bài toán không chỉ là một nghiệm duy nhất như bài toán thiết kế tối ưu đơn mục tiêu, mà sẽ là một tập hợp các điểm thiết kế tối ưu nằm trên đường pareto. Kết quả này vì vậy sẽ giúp cho người thiết kế có thêm nhiều sự lựa chọn trong quá trình tính toán thiết kế. Dựa vào nghiệm tối ưu trên 

đường cong pareto này, người thiết kế có thể chọn các điểm thiết kế thiên về an toàn hoặc thiên về tiết kiệm chi phí. Kết quả chi tiết được thể hiện ở bảng 10. Kết quả cho thấy rằng nếu chọn phương án thiết kế thiên về an toàn thì nên chọn điểm thiết kế I, hoặc phương án thiên về tiết kiệm chi phí thì nên chọn điểm thiết kế G, hoặc phương án cân đối giữa chi phí và an toàn thì nên chọn điểm thiết kế H. 

**==> picture [251 x 210] intentionally omitted <==**

**----- Start of picture text -----**<br>
0,06<br>Dc=0,6(m)-1,2(m)<br>0,055 G(49.12; 0.059)<br>0,05<br>0,045<br>H(62.84; 0.04)<br>0,04<br>I(181.1; 0.035)<br>0,035 Fan iin 0.006000 @o00 G¢5"<br>0,03<br>40 60 80 100 120 140 160 180 200 220 240<br>Trọng lượng thể tích  V (m [3] )<br>**----- End of picture text -----**<br>


**Hình 8.** _Nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc_ 

**Bảng 10.** _Tổng hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc_ 

|**Bảng 10.g 10. 10.**_Tổng hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcg hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcghiệm tối ưu đa mục tiêu cho kết cấu móng cọchiệm tối ưu đa mục tiêu cho kết cấu móng cọc_|_Tổng hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcg hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcghiệm tối ưu đa mục tiêu cho kết cấu móng cọchiệm tối ưu đa mục tiêu cho kết cấu móng cọcệm tối ưu đa mục tiêu cho kết cấu móng cọcm tối ưu đa mục tiêu cho kết cấu móng cọcục tiêu cho kết cấu móng cọcc tiêu cho kết cấu móng cọc_|_Tổng hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcg hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc hợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcợp nghiệm tối ưu đa mục tiêu cho kết cấu móng cọc nghiệm tối ưu đa mục tiêu cho kết cấu móng cọcghiệm tối ưu đa mục tiêu cho kết cấu móng cọchiệm tối ưu đa mục tiêu cho kết cấu móng cọcệm tối ưu đa mục tiêu cho kết cấu móng cọcm tối ưu đa mục tiêu cho kết cấu móng cọcục tiêu cho kết cấu móng cọcc tiêu cho kết cấu móng cọcg cọc cọcọcc _||
|---|---|---|---|
|**Điểm**|**G**|**H**|**I**|
|Đường kính<br><br>m<br>_c_<br>_D_|0,6|0,6|1,1|
|Chiều dài<br><br>m<br>_c_<br>_L_|48,7|97,2|100|
|Thể tích<br><br>3<br>m<br>_V_|49,12|62,84|181,1|
|Độ lún<br><br>m<br>_S_|0,059|0,04|0,035|



## **6. Kết luận** 

Chúng tôi đã tiến hành nghiên cứu, thiết lập và giải bài toán tối ưu hóa đa mục tiêu cho kết cấu móng cọc bằng phương pháp giải thuật di truyền phân loại không trội NSGA-II. Bài toán tối ưu đa mục tiêu được thành lập với hai hàm mục tiêu đối lập nhau là cực tiểu thể tích móng cọc và cực tiểu độ lún. Biến thiết kế là chiều dài cọc _Lc_ và đường kính cọc _Dc_ . Điều kiện ràng buộc bài toán tối ưu gồm có ràng buộc về khả năng chịu tải, ràng buộc về độ lún móng cọc và ràng buộc về độ ổn định của đất nền. Các kết quả đạt được cho thấy lời giải tối ưu đạt được là một tập hợp các nghiệm tối ưu nằm trên đường nghiệm Pareto. Kết quả của nghiên cứu 

là nền tảng quan trọng giúp cho người thiết kế có cái nhìn tổng quan và có nhiều phương án thiết kế tối ưu để chọn lựa, tùy theo yêu cầu của chủ đầu tư. 

Lời cảm ơn: _Nghiên cứu này được tài trợ bởi Quỹ Phát triển khoa học và công nghệ quốc gia (NAFOSTED) trong đề tài mã số 107.02-2017.08. Chúng tôi xin trân trọng cảm ơn._ 

## **TÀI LIỆU THAM KHẢO** 

- [1] P. Ngatchou, A. Zarei, and A. El-Sharkawi (2005), “Pareto Multi Objective Optimization,” _Proc. 13th Int. Conf. on, Intell. Syst. Appl. to Power Syst._ , 6-10 Nov. 2005, pp. 84–91. 

_Tạp chí KHCN Xây dựng - số 3/2018_ 59 

**ĐỊA KỸ THUẬT - TRẮC ĐỊA** 

- [2] K. S. Y. F. Leung and  and A. Klar (2011), “Multiobjective Foundation Optimization and its Application to Pile Reuse,” _Geo-Frontiers 2011 © ASCE 2011_ , 397(9), pp. 75–84. 

- [3] M. F. Ashby, “Multi-objective optimization in material design and selection,” _Acta Mater._ , vol. 48, no. 1, pp. 359–369, 2000. 

- [4] K. Deb and A. Dhar (2011), “Optimum design of stone column-improved soft soil using multiobjective optimization technique,” _Comput. Geotech._ , 38(1), pp. 50–57, 2011. 

- [5] L. Wang, C. H. Juang, S. Atamturktur, W. Gong, S. Khoshnevisan, and H. S. Hsieh (2014), “Optimization of design of supported excavations in multi-layer strata,” _J. Geoengin._ , 9(1), pp. 1–10. 

- [6] X. Liu, G. Cheng, B. Wang, and S. Lin (2012), “Optimum Design of Pile Foundation by Automatic Grouping Genetic Algorithms,” _ISRN Civ. Eng._ , 2012, pp. 1–16. 

- [7] Vũ Anh Tuấn and Nguyễn Quốc Cường (2007), “Thiết kế tối ưu kết cấu thép bằng thuật tiến hóa,” _Tạp chí khoa học và công nghệ_ , 45(4), tr. 111–118. 

- [8] Y. F. Leung, A. Klar, and K. Soga (2010), “Theoretical Study on Pile Length Optimization of Pile Groups and Piled Rafts,” _J. Geotech. Geoenvironmental Eng._ , 

136(2), pp. 319–330. 

- [9] K. Deb, A. Pratap, S. Agarwal, and T. Meyarivan (2002), “A fast and elitist multiobjective genetic algorithm: NSGA-II,” _IEEE Trans. Evol. Comput._ , **6(2)** , pp. 182–197. 

- [10] Châu Ngọc Ẩn (2012), _Nền móng công trình_ , Nhà xuất bản xây dựng Hà Nội. 

- [11] Braja M. Das (2016), _Principles of Foundation Engineering_ , Cengage Learning. 

- [12] TCVN 9362:2012 (2013), _Tiêu chuẩn thiết kế nền nhà và công trình_ , Bộ khoa học và Công nghệ. 

- [13] Kalyanmoy Deb (2001), “Multi Objective Optimization Using Evolutionary Algorithms.” John Wiley & Sons, Ltd. 

- [14] A. Starkey, H. Hagras, S. Shakya, and G. Owusu (2016), “A multi-objective genetic type-2 fuzzy logic based system for mobile field workforce area optimization,” _Inf. Sci. (Ny)._ , 329, pp. 390–411. 

- [15] Nguyễn Minh Thọ (2015), _Tối ưu hóa dựa trên độ tin cậy bài toán thiết kế móng cọc sử dụng vòng lặp kép_ , Luận văn thạc sỹ, Đại học Hutech, Trường Đại học Công nghệ TP. Hồ Chí Minh. 

_**Ngày nhận bài: 27/7/2018.**_ 

_**Ngày nhận bài sửa lần cuối: 26/8/2018.**_ 

60 _Tạp chí KHCN Xây dựng - số 3/2018_ 

