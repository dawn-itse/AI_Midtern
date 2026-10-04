# NỘI DUNG VÀ KỊCH BẢN THUYẾT TRÌNH BÁO CÁO GIỮA KỲ (TASK 2)
## MÔN: NHẬP MÔN TRÍ TUỆ NHÂN TẠO (503043) - ĐẠI HỌC TÔN ĐỨC THẮNG
**Đề tài:** Sokoban Search & Competitive Two-Agent AI  
**Thời lượng thuyết trình tối đa:** 05 phút  
**Quy chuẩn Slide:** Khung hình tỉ lệ **4:3**, Nền sáng (Light/White background), không dùng hình vẽ lòe loẹt, rõ nét khi in trắng đen (Grayscale), **tuyệt đối không dán code thô**.

---

## 📑 BẢNG PHÂN BỔ THỜI GIAN THUYẾT TRÌNH (TỔNG: 4 PHÚT 45 GIÂY)
- **Slide 1 - 2:** Giới thiệu đề tài, danh sách thành viên & phân công (30 giây)
- **Slide 3 - 5:** Mô hình hóa bài toán, thiết kế Heuristic & Chứng minh toán học (1 phút 30 giây)
- **Slide 6 - 7:** Thuật toán UCS vs A*, Thực nghiệm Benchmark & Demo GUI (1 phút 15 giây)
- **Slide 8 - 9:** Bài toán đối kháng 2 Agent, Thuật toán thi đấu thời gian thực (1 phút)
- **Slide 10 - 11:** Đánh giá ưu/nhược điểm, Bảng % hoàn thành & Kết luận (30 giây)

---

## SLIDE 1: TRANG BÌA (TITLE SLIDE)
* **Tiêu đề lớn:** SOKOBAN SEARCH & COMPETITIVE TWO-AGENT AI
* **Tiêu đề phụ:** Báo cáo Giữa kỳ môn Nhập môn Trí tuệ Nhân tạo (Mã môn: 503043)
* **Khoa / Trường:** Khoa Công nghệ Thông tin - Trường Đại học Tôn Đức Thắng (TDTU)
* **Giảng viên hướng dẫn:** ThS. Nguyễn Thành An (nguyenthanhan@tdtu.edu.vn)
* **Mã nhóm dự án:** Group [Điền mã nhóm của bạn]
* **Gợi ý thiết kế:** 
  - Nền trắng tinh tế, logo trường TDTU góc trên.
  - Hình minh họa sơ đồ mê cung Sokoban dạng tối giản (minimalist vector).

---

## SLIDE 2: DANH SÁCH THÀNH VIÊN & PHÂN CÔNG NHIỆM VỤ (STUDENT LIST)
* **Tiêu đề Slide:** THÀNH VIÊN VÀ PHÂN CÔNG NHIỆM VỤ

| STT | Họ và tên | MSSV | Email sinh viên | Nhiệm vụ đảm nhiệm | % Hoàn thành |
| :---: | :--- | :---: | :--- | :--- | :---: |
| 1 | [Họ tên Bạn - Member A] | [MSSV Bạn] | [Email Bạn]@student.tdtu.edu.vn | • Thiết kế hàm Heuristic & Kiểm chứng toán học (Y/c 2, 4)<br>• Cài đặt thuật toán Agent thi đấu đối kháng (Y/c 7)<br>• Phân tích thuật toán & Soạn thảo báo cáo | **100%** |
| 2 | [Họ tên Bạn Thanh - Member B] | 524H0030 | 524H0030@student.tdtu.edu.vn | • Xây dựng môi trường & Giao diện Pygame (Y/c 5, 8)<br>• Thực nghiệm đo lường hiệu năng Benchmark (Y/c 3)<br>• Thiết kế Slide báo cáo & Quay Video Demo | **100%** |

* **Gợi ý trình bày:** Nhấn mạnh sự phối hợp chặt chẽ: Một thành viên phụ trách giải thuật & toán học, một thành viên phụ trách giao diện, thực nghiệm và kiểm thử.

---

## SLIDE 3: MÔ HÌNH HÓA BÀI TOÁN TÌM KIẾM (STATE-SPACE FORMULATION)
* **Tiêu đề Slide:** MÔ HÌNH HÓA BÀI TOÁN KHÔNG GIAN TRẠNG THÁI (YÊU CẦU 1)
* **Nội dung trình bày (5 thành phần chuẩn AI):**
  1. **Không gian Trạng thái ($\mathcal{S}$):**
     $$s = (\text{agent\_pos}, \text{box\_positions})$$
     - `agent_pos`: Tọa độ $(r, c)$ của người chơi.
     - `box_positions`: Tập hợp tọa độ các quả thùng dưới dạng `frozenset`.
  2. **Trạng thái Khởi đầu ($s_0$):** Đọc từ file bản đồ (`.txt`), nạp vị trí khởi đầu của Agent `A`, thùng `B`, và các đích `D` (xử lý thùng trên đích `C`).
  3. **Tập Hành động ($\mathcal{A}$):** $\mathcal{A} = \{\text{North, South, East, West}\}$.
  4. **Mô hình Chuyển trạng thái ($\text{Result}(s, a)$):**
     - Đi bộ: Di chuyển nếu ô tiếp theo không phải tường và không có thùng.
     - Đẩy thùng: Đẩy thùng nếu ô sau lưng thùng là ô trống (không phải tường/thùng khác).
  5. **Kiểm tra Mục tiêu ($\text{GoalTest}(s)$):** $\text{box\_positions} == \text{targets}$ (Tất cả thùng đều nằm trên đích).
  6. **Chi phí Đường đi ($c$):** Chi phí đồng nhất $c(s, a, s') = 1$ cho mỗi bước di chuyển.
* **Hình vẽ minh họa:** Sơ đồ chuyển đổi trạng thái (State Transition Diagram) khi Agent thực hiện 1 bước đẩy thùng.

---

## SLIDE 4: THIẾT KẾ HÀM HEURISTIC ĐẶC TRƯNG (HEURISTIC DESIGN)
* **Tiêu đề Slide:** THIẾT KẾ HÀM HEURISTIC $h(n)$ (YÊU CẦU 2)
* **Cam kết đề bài:** **Tuyệt đối KHÔNG sử dụng khoảng cách Manhattan và Euclidean**.
* **Nguyên lý Heuristic đề xuất:**
  - **BFS né tường đa nguồn (Multi-Source BFS Shortest Path):**
    - Chạy BFS ngược từ tập hợp tất cả các ô đích $D$ qua các ô trống để lập bảng khoảng cách thực tế né vật cản: $\text{dist\_map}[\text{pos}]$.
    - Khắc phục nhược điểm của Manhattan (vốn luôn bỏ qua các bức tường ngăn cách).
  - **Cơ chế Cắt tỉa Góc chết (Deadlock Pruning):**
    - Nhận diện 4 góc chết vuông góc (Corner Deadlock): Thùng bị kẹp giữa 2 bức tường vuông góc mà không phải là ô đích.
    - Khi có bất kỳ thùng nào rơi vào góc chết: Gán ngay $h(n) = \infty$ để loại bỏ hoàn toàn nhánh tìm kiếm cụt.
* **Công thức tổng quát:**
  $$h(s) = \begin{cases} \infty & \text{nếu tồn tại thùng bị Deadlock} \\ \sum_{b \in \text{boxes}} \text{dist\_map}(b) & \text{ngược lại} \end{cases}$$
* **Sơ đồ minh họa:** Hình vẽ minh họa một góc chết 2 bức tường kẹp thùng và luồng sóng BFS né tường tỏa ra từ các ô đích.

---

## SLIDE 5: CHỨNG MINH & THỰC NGHIỆM TÍNH CHẤT HEURISTIC (YÊU CẦU 4)
* **Tiêu đề Slide:** KIỂM CHỨNG TÍNH ADMISSIBLE VÀ CONSISTENT
* **1. Chứng minh Lý thuyết:**
  - **Tính Chấp nhận được (Admissible):** Với mỗi quả thùng, khoảng cách BFS né tường đến đích gần nhất luôn $\le$ chi phí thực tế $h^*(n)$ để đẩy thùng đó (vì bài toán thực tế còn có thể bị cản bởi thùng khác hoặc cần bước đi vòng của Agent). Do đó $h(n) \le h^*(n)$.
  - **Tính Nhất quán (Consistent):** Trong mỗi bước chuyển trạng thái $n \rightarrow n'$, một thùng chỉ có thể dịch chuyển tối đa 1 ô (hoặc đứng yên). Do đó:
    $$h(n) - h(n') \le 1 = c(n, a, n')$$
    Thỏa mãn bất đẳng thức tam giác của Monotone Heuristic.
* **2. Báo cáo Kết quả Thực nghiệm (Trích xuất từ `verify_heuristic.py`):**

| Tính chất kiểm định | Công thức điều kiện | Số mẫu kiểm thử | Kết quả đạt được | Kết luận |
| :--- | :---: | :---: | :---: | :---: |
| **Admissibility** (Không ước lượng lố) | $h(n) \le h^*(n)$ | 50 trạng thái ngẫu nhiên | **100.00%** (50/50 PASS) | Đạt chuẩn tối ưu tuyệt đối |
| **Consistency** (Bất đẳng thức tam giác) | $h(n) - h(n') \le c(n, a, n')$ | 117 bước chuyển ($n \rightarrow n'$) | **100.00%** (117/117 PASS) | Đạt chuẩn không cần Re-open node |

---

## SLIDE 6: THỰC NGHIỆM ĐỐI CHỨNG: UCS VS A* (YÊU CẦU 3)
* **Tiêu đề Slide:** SO SÁNH HIỆU NĂNG THỰC NGHIỆM: UCS VS A*
* **Phương pháp thực nghiệm (Benchmark Methodology):**
  - Thực thi độc lập trên tiến trình riêng bằng `multiprocessing` để đảm bảo đo lường chính xác.
  - Lặp lại 3 lần cho mỗi bản đồ để lấy giá trị trung bình (`REPEATS = 3`).
  - Đo đạc 4 thông số: Thời gian chạy (giây), Số node mở rộng (`Expanded`), Frontier cực đại, Bộ nhớ RAM đỉnh (`tracemalloc`).
* **Bảng Số liệu Thực nghiệm Chính thức (Từ `results/benchmark.csv`):**

| Bản đồ kiểm thử | Thuật toán | Tỉ lệ giải thành công | Chi phí lời giải ($g$) | Số node mở rộng (Expanded) | Thời gian thực thi (s) | Bộ nhớ RAM đỉnh (MiB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`map_single.txt`**<br>(Bản đồ 4 thùng) | **UCS** | 3/3 (100%) | 29 | 30,670 nodes | 0.587 s | 10.52 MiB |
| | **A\*** | 3/3 (100%) | 29 | **7,158 nodes** | **0.341 s** | **2.26 MiB** |
| **`example_map.txt`**<br>(Map đề bài 7 thùng) | **UCS** | 0/3 (0%) | - | > 494,000 nodes | Timeout (> 5.0s) | > 50 MiB |
| | **A\*** | 3/3 (100%) | 34 | **13,490 nodes** | **0.239 s** | **5.35 MiB** |

* **Đánh giá đột phá:** 
  - Trên `map_single.txt`: A* giảm **4.3 lần số node mở rộng** và tiết kiệm **4.6 lần dung lượng RAM** so với UCS.
  - Trên `example_map.txt`: UCS bị cạn kiệt thời gian (Timeout), trong khi A* giải quyết hoàn hảo chỉ trong **0.24 giây**!

---

## SLIDE 7: GIAO DIỆN ĐỒ HỌA PYGAME TƯƠNG TÁC (YÊU CẦU 5)
* **Tiêu đề Slide:** GIAO DIỆN NGƯỜI DÙNG PYGAME (SINGLE-AGENT GUI)
* **Các tính năng nổi bật đáp ứng Yêu cầu 5:**
  1. **Lựa chọn thuật toán trực quan:** Nút bấm chuyên biệt `Solve UCS` và `Solve A*` (Hỗ trợ phím tắt `U` và `A`).
  2. **Điều khiển linh hoạt:** Hỗ trợ phím `Space` (Pause/Run), mũi tên `->` (Step forward), mũi tên `<-` (Step backward), và phím `R` (Reset).
  3. **Hiển thị thông số tìm kiếm thời gian thực:** Panel bên phải thể hiện rõ: Số bước hành động (`Actions`), Trạng thái (`PLAYBACK`), Thời gian giải (`SEARCH TIME`), Số node mở rộng (`EXPANDED NODES`), và `MAX FRONTIER`.
  4. **Cơ chế Auto-Scaling & Auto-Centering:** Tự động co giãn kích cỡ ô (`cell_size`) theo kích thước bản đồ, căn giữa chính xác, loại bỏ hoàn toàn lỗi tràn khung hình.
* **Hình ảnh chèn trên Slide:** Ảnh chụp giao diện `main_gui.py` đang chạy lời giải của A*.

---

## SLIDE 8: BÀI TOÁN ĐỐI KHÁNG VÀ CHIẾN THUẬT AGENT (YÊU CẦU 6 & 7)
* **Tiêu đề Slide:** BÀI TOÁN ĐỐI KHÁNG 2 AGENT & THUẬT TOÁN THI ĐẤU
* **1. Mô hình hóa Bài toán Đối kháng (Yêu cầu 6):**
  - Môi trường đối kháng đồng thời: Hai Agent cùng ra quyết định tại mỗi lượt.
  - Cơ chế va chạm vật lý: Không thể đi xuyên qua nhau; khi cùng lao vào 1 ô, hành động bị hủy bỏ.
  - Cơ chế cướp thùng (Stealing): Cho phép đẩy thùng đối thủ ra khỏi đích để trừ điểm và chiếm lại đích.
* **2. Thuật toán Agent Thi đấu (`agent_team.py` - Yêu cầu 7):**
  - **Kiến trúc kết hợp:** **Multi-Goal Reverse BFS** + **Forward Walk BFS** + **Real-time GBFS**.
  - **4 Chiến thuật Master AI:**
    1. *Ưu tiên sân nhà (Home Yard Priority):* Quét sạch và ăn chắc điểm các thùng sân nhà trước.
    2. *Cam kết mục tiêu (Target Commitment):* Cộng điểm cam kết để tránh hiện tượng dao động đổi mục tiêu liên tục giữa 2 lượt.
    3. *Né đối đầu trực diện (Anti-Standoff):* Tránh đâm đầu vào ô đích đang có đối thủ đứng rình, chuyển sang đẩy tạt cánh (Flank Push).
    4. *Nhường nhịp phá vỡ kẹt cứng (Collision Recovery):* Tự động đứng yên (`Stay`) 1 nhịp nếu va chạm để đối thủ đi qua giải phóng nút thắt.
* **Hiệu năng thời gian:** Thời gian ra quyết định trung bình: **~0.5ms – 0.9ms** (Vượt xa ràng buộc $\le 1000$ms của đề bài).

---

## SLIDE 9: GIAO DIỆN ĐỐI KHÁNG VÀ KẾT QUẢ THI ĐẤU (YÊU CẦU 8)
* **Tiêu đề Slide:** SÀN ĐẤU ĐỐI KHÁNG 2 AGENT (COMPETITIVE ARENA)
* **Đặc điểm giao diện thi đấu (`competitive_gui.py`):**
  - **Bản đồ đại chiến trường (`battle_map.txt`):** Kích thước 25 cột $\times$ 11 hàng, gồm 7 Goal và 8 Thùng.
  - **Mã màu phân biệt rõ ràng:** 
    - Thùng của Agent 1: Màu Xanh dương.
    - Thùng của Agent 2: Màu Đỏ.
    - Thùng trung lập: Màu Nâu.
  - **Bảng điều khiển trận đấu:** Cho phép người dùng nhập trực tiếp giới hạn bước đi $n$ (`Step limit`), xem lượt hiện tại và tỉ số trực tiếp.
* **Kết quả thi đấu thực tế:**
  - Ở mốc 50 bước: Agent 1 ăn trọn 2 thùng sân nhà, chiếm tiếp thùng giữa sân $\rightarrow$ Tỉ số hòa/dẫn chắc chắn.
  - Ở mốc 80 – 100 bước: Agent 1 bứt phá, cướp thùng và thắng áp đảo **Agent 1: 5 | Agent 2: 2**!
* **Hình ảnh chèn trên Slide:** Ảnh chụp giao diện sàn đấu đối kháng `competitive_gui.py`.

---

## SLIDE 10: ĐÁNH GIÁ ƯU ĐIỂM VÀ NHƯỢC ĐIỂM (PROS & CONS)
* **Tiêu đề Slide:** ĐÁNH GIÁ ƯU ĐIỂM VÀ HẠN CHẾ

### 1. Ưu điểm nổi bật (Advantages):
- **Tính tối ưu toán học:** Hàm Heuristic đạt chuẩn 100% Admissible và Consistent, giúp A* tìm ra đường đi ngắn nhất mà không bao giờ bỏ sót.
- **Tốc độ vượt trội:** Cơ chế Deadlock Pruning cắt tỉa nhánh cụt cực mạnh, giải quyết bản đồ 7 thùng phức tạp chỉ trong 0.24 giây.
- **Agent đối kháng thông minh & ổn định:** Không bị hiện tượng rung lắc con lắc, thời gian ra quyết định $< 1$ms, có chiến thuật công - thủ toàn diện.
- **Giao diện hiện đại & tin cậy:** Độc lập với thư viện ngoài, vẽ bằng vector primitives, tự co giãn mượt mà trên cả macOS và Windows.

### 2. Hạn chế & Hướng phát triển (Disadvantages & Future Work):
- **Phát hiện Deadlock nâng cao:** Hiện tại chủ yếu nhận diện Deadlock góc vuông (Corner Deadlock), chưa mở rộng cho Deadlock theo hàng (Line/Wall Deadlock) phức tạp.
- **Học máy / Minimax:** Agent đối kháng hiện hoạt động theo Heuristic trực tuyến; có thể mở rộng tích hợp Minimax cắt tỉa Alpha-Beta hoặc Q-Learning để dự đoán sâu hơn các nước cờ của đối thủ.

---

## SLIDE 11: TỔNG KẾT HOÀN THÀNH & VIDEO DEMO
* **Tiêu đề Slide:** TỔNG KẾT DỰ ÁN & DEMO

### Bảng Tổng hợp Mức độ Hoàn thành Yêu cầu:

| STT | Nhiệm vụ / Yêu cầu trong Đề bài | Trọng số | Mức độ hoàn thành |
| :---: | :--- | :---: | :---: |
| 1 | Yêu cầu 1: State-Space Formulation | 1.0 đ | **100%** |
| 2 | Yêu cầu 2: Cài đặt UCS & A* + Thiết kế Heuristic | 1.0 đ | **100%** |
| 3 | Yêu cầu 3: Thực nghiệm Benchmark thời gian & bộ nhớ | 1.0 đ | **100%** |
| 4 | Yêu cầu 4: Kiểm chứng tính Admissible & Consistent | 1.0 đ | **100%** |
| 5 | Yêu cầu 5: Giao diện đồ họa Pygame đơn lẻ | 1.0 đ | **100%** |
| 6 | Yêu cầu 6: Mô hình hóa bài toán đối kháng 2 Agent | 1.0 đ | **100%** |
| 7 | Yêu cầu 7: Thuật toán điều khiển Agent thi đấu | 1.0 đ | **100%** |
| 8 | Yêu cầu 8: Giao diện đối kháng và ghép đấu | 1.0 đ | **100%** |
| 9 | Task 2: Slide thuyết trình (4:3) & Video Demo | 2.0 đ | **100%** |
| **TỔNG** | **Toàn bộ Dự án Giữa kỳ môn Nhập môn AI** | **10.0 đ** | **100% HOÀN TẤT** |

* **Đường dẫn Video Demo ($\le 3$ phút):** [Dán đường link Youtube/Google Drive của nhóm vào đây]
* **Lời kết:** *"Cảm ơn Thầy và các bạn đã chú ý lắng nghe! Nhóm em xin sẵn sàng nhận câu hỏi phản biện."*

---

## 🎙️ KỊCH BẢN NÓI THUYẾT TRÌNH CHI TIẾT (LỜI THOẠI CHUẨN 5 PHÚT)

*(Bạn hãy cầm kịch bản này luyện nói thử 1-2 lần để khớp đúng 4 phút 45 giây nhé!)*

### [0:00 - 0:30] Mở đầu & Giới thiệu
> *"Kính chào Thầy và các bạn. Em đại diện cho nhóm [Tên nhóm] xin trình bày báo cáo đồ án giữa kỳ môn Nhập môn Trí tuệ Nhân tạo với đề tài: **Sokoban Search và Competitive Two-Agent AI**. Nhóm chúng em gồm 2 thành viên: Em là [Tên bạn] phụ trách phần mô hình hóa toán học, giải thuật tìm kiếm A*, kiểm chứng Heuristic và AI đối kháng; bạn [Tên bạn Thanh] phụ trách xây dựng engine môi trường, giao diện Pygame, thực nghiệm benchmark và slide báo cáo. Cả 2 thành viên đều hoàn thành 100% khối lượng công việc được giao."*

### [0:30 - 1:30] Mô hình hóa, Heuristic & Kiểm chứng Toán học
> *"Ở Task 1, chúng em mô hình hóa Sokoban thành bài toán tìm kiếm không gian trạng thái gồm 5 thành phần chuẩn, trong đó trạng thái là cặp tọa độ người chơi và tập hợp vị trí các thùng. Để giải quyết bài toán, chúng em đề xuất hàm Heuristic né tường dựa trên giải thuật **Multi-Source BFS**. Chúng em tuyệt đối không sử dụng khoảng cách Manhattan hay Euclidean theo đúng yêu cầu của Thầy, mà tính khoảng cách bước đi thực tế né vật cản từ mọi ô về đích, đồng thời tích hợp cơ chế phát hiện **Corner Deadlock** để cắt tỉa nhánh cụt với chi phí bằng vô cực.
> Về mặt toán học, hàm Heuristic đạt tính Admissible vì không bao giờ ước lượng quá chi phí thực tế, và đạt tính Consistent vì thỏa mãn bất đẳng thức tam giác. Kết quả thực nghiệm kiểm chứng trên 50 trạng thái và 117 bước chuyển đổi cho thấy hàm đạt **100% Admissible** và **100% Consistent**, đảm bảo A* luôn tìm ra lời giải tối ưu toàn cục."*

### [1:30 - 2:45] So sánh Benchmark & Demo Giao diện Đơn lẻ
> *"Để chứng minh tính vượt trội của A* so với UCS, chúng em xây dựng hệ thống benchmark tự động đo đạc thời gian, bộ nhớ RAM đỉnh và số node mở rộng. Trên bản đồ 4 thùng, A* giảm tới **4.3 lần số node mở rộng** và tiết kiệm **4.6 lần dung lượng RAM** so với UCS. Đặc biệt trên bản đồ 7 thùng của Thầy, trong khi UCS bị timeout quá 5 giây vì phải duyệt gần 500,000 node, thì A* của chúng em tìm ra lời giải 34 bước chỉ trong **0.24 giây**.
> Toàn bộ kết quả này được trực quan hóa trên giao diện Pygame với đầy đủ nút bấm, phím tắt lùi/tiến bước, pause và hiển thị thông số tìm kiếm thời gian thực. Giao diện được thiết kế cơ chế tự động co giãn và căn giữa nên tương thích hoàn hảo với mọi kích thước bản đồ."*

### [2:45 - 3:45] Bài toán Đối kháng 2 Agent & Chiến thuật AI
> *"Bước sang phần thi đấu đối kháng ở Task 2, chúng em mở rộng Sokoban thành trò chơi 2 Agent hành động đồng thời, có cơ chế va chạm vật lý và cướp điểm từ thùng của đối phương. Để Agent thi đấu đạt hiệu quả cao nhất dưới áp lực thời gian $\le 1000$ms, chúng em kết hợp **Reverse-Push BFS** và **Real-time Greedy Best-First Search**.
> Agent nhóm em sở hữu 4 chiến thuật nổi bật: ưu tiên giải quyết dứt điểm các thùng sân nhà trước, cam kết mục tiêu để không bị dao động đổi ý, né đối đầu trực diện khi đối thủ đứng chắn ở ô đích, và tự giác nhường 1 nhịp nếu xảy ra va chạm để phá vỡ thế kẹt cứng. Thời gian ra quyết định thực tế của Agent chỉ mất **dưới 1 mili-giây**, giúp Agent thi đấu áp đảo và giành chiến thắng thuyết phục trên bản đồ chiến trường lớn."*

### [3:45 - 4:45] Đánh giá & Kết luận
> *"Tóm lại, dự án của nhóm em đã hoàn thành trọn vẹn 100% tất cả 8 yêu cầu kỹ thuật của Task 1 cũng như các yêu cầu báo cáo của Task 2. Mặc dù còn hướng mở rộng như tích hợp Minimax hay học tăng cường cho Agent, giải pháp hiện tại đã đạt hiệu năng rất cao, chạy mượt mà trên cả macOS và Windows. Chi tiết màn chạy thử nghiệm được chúng em ghi lại trong video demo đính kèm. Em xin chân thành cảm ơn Thầy đã lắng nghe và nhóm em rất mong nhận được những nhận xét, câu hỏi từ Thầy ạ!"*
