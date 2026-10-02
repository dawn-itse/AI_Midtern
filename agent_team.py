import time
from collections import deque
from competitive_core import CompetitiveState, DIRECTIONS

def get_action(state: CompetitiveState, agent_id: int, time_limit_ms: int = 1000) -> str:
    """
    Thuật toán AI điều khiển Agent của nhóm (Yêu cầu 7).
    
    Quy tắc & Giới hạn:
    - Mỗi quyết định bắt buộc thực hiện trong <= 1,000 ms.
    - Chiến lược: Sử dụng Tìm kiếm theo mục tiêu (Target-driven BFS/A* Pathfinding):
      1. Tìm chiếc thùng tiềm năng nhất: Ưu tiên thùng chưa vào đích gần mình nhất,
         hoặc thùng đã bị đối thủ chiếm để cướp điểm.
      2. Tìm ô đứng phù hợp phía sau thùng để đẩy thùng tiến về ô đích gần nhất.
      3. Tìm đường đi ngắn nhất né tường, thùng khác và đối thủ.
      4. Trả về bước đi đầu tiên hướng tới mục tiêu.
    """
    start_time = time.perf_counter()
    my_pos = state.agent_positions[agent_id]
    other_id = 2 if agent_id == 1 else 1
    other_pos = state.agent_positions[other_id]

    # Các ô bị chặn (tường, thùng khác, đối thủ)
    static_obstacles = state.walls | {other_pos}

    # 1. Phân loại thùng:
    # - Thùng chưa vào đích (owner == None)
    # - Thùng của đối thủ (owner == other_id) -> Có thể cướp
    target_boxes = []
    for b_pos, owner in state.boxes.items():
        if owner != agent_id:  # Chỉ nhắm vào thùng chưa có điểm hoặc thùng của đối thủ
            target_boxes.append((b_pos, owner))

    if not target_boxes:
        # Nếu tất cả thùng đều đã là của mình, đứng yên hoặc giữ vị trí an toàn
        return "Stay"

    # 2. Đánh giá và chọn thùng tiềm năng nhất (khoảng cách đi bộ từ mình tới thùng ngắn nhất)
    best_action = None
    min_dist_to_box = float('inf')

    # Hàm BFS tìm đường đi ngắn nhất từ start đến goal_pos
    def find_path(start, target_set, blocked):
        queue = deque([(start, [])])
        visited = {start}
        while queue:
            # Kiểm soát thời gian để không bao giờ bị timeout 1000ms
            if (time.perf_counter() - start_time) * 1000 > (time_limit_ms - 50):
                break
            curr, path = queue.popleft()
            if curr in target_set:
                return path
            for act, (dr, dc) in DIRECTIONS.items():
                if act == "Stay":
                    continue
                nxt = (curr[0] + dr, curr[1] + dc)
                if nxt not in blocked and nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [act]))
        return None

    # Tìm đường tới vị trí xung quanh thùng để chuẩn bị đẩy
    for b_pos, owner in target_boxes:
        # Các vị trí đứng xung quanh thùng và hướng đẩy tương ứng
        push_spots = []
        push_dirs = {}
        for act, (dr, dc) in [("North", (-1, 0)), ("South", (1, 0)), ("West", (0, -1)), ("East", (0, 1))]:
            stand_pos = (b_pos[0] - dr, b_pos[1] - dc)
            dest_pos = (b_pos[0] + dr, b_pos[1] + dc)
            # Chỉ hợp lệ nếu ô đứng và ô đích đẩy không phải tường và ô đích không có thùng khác
            all_boxes = set(state.boxes.keys())
            if stand_pos not in state.walls and dest_pos not in state.walls and dest_pos not in (all_boxes - {b_pos}):
                push_spots.append(stand_pos)
                push_dirs[stand_pos] = act

        if not push_spots:
            continue

        # Tìm đường tới một trong các ô đẩy
        all_box_positions = set(state.boxes.keys())
        blocked_for_walking = static_obstacles | (all_box_positions - {b_pos})
        path = find_path(my_pos, set(push_spots), blocked_for_walking)

        if path is not None:
            if len(path) == 0:
                # ĐÃ ĐỨNG TẠI VỊ TRÍ ĐẨY: Thực hiện hành động đẩy thùng ngay lập tức!
                push_act = push_dirs.get(my_pos)
                if push_act:
                    best_action = push_act
                    min_dist_to_box = -1
                    break
            elif len(path) < min_dist_to_box:
                min_dist_to_box = len(path)
                best_action = path[0]

    # Nếu đã đứng ngay vị trí đẩy và bước tiếp theo là đẩy thùng
    if not best_action:
        # Thử tìm một bước đi an toàn hợp lệ bất kỳ
        for act, (dr, dc) in DIRECTIONS.items():
            if act == "Stay":
                continue
            nxt = (my_pos[0] + dr, my_pos[1] + dc)
            if nxt not in state.walls and nxt != other_pos:
                if nxt not in state.boxes:
                    best_action = act
                    break
                else:
                    # Nếu là thùng, kiểm tra có đẩy được không
                    box_nxt = (nxt[0] + dr, nxt[1] + dc)
                    if box_nxt not in state.walls and box_nxt not in state.boxes and box_nxt != other_pos:
                        best_action = act
                        break

    return best_action if best_action else "Stay"
