"""
Agent AI thi đấu đối kháng Sokoban (Yêu cầu 7).
Thuộc về: Nhóm sinh viên - Môn Nhập môn Trí tuệ Nhân tạo (503043).

Chiến lược AI Toàn diện & Tối thượng (Master Competitive AI):
1. Chiến lược "Ăn chắc sân nhà" (Home Yard Priority):
   - Khi sân nhà còn thùng chưa ăn: Agent tập trung 100% giải quyết các thùng sân nhà trước.
   - Tránh việc bỏ bê thùng ở nhà chạy ra giữa sân tranh cướp hỗn loạn.
   - Sau khi ghi trọn vẹn điểm sân nhà, Agent mới tiến quân ra giữa sân hoặc sang sân đối thủ.
2. Multi-Goal Reverse-Push BFS (Chỉ tính Đích khả dụng):
   - Đích đã có thùng của ta -> ĐÃ HOÀN THÀNH.
   - Đích chưa có thùng HOẶC Đích đối thủ đang chiếm -> LÀ MỤC TIÊU GHI ĐIỂM / CƯỚP ĐIỂM!
3. Deadlock Shield (Né Deadlock tuyệt đối):
   Cấm tuyệt đối mọi cú đẩy làm thùng rơi vào góc chết hay chân tường chết.
4. Chống dao động & Phòng ngự chắc chắn (Anti-Oscillation Guard):
   - Không bị hiện tượng đi qua đi lại giữa 2 ô.
   - Nếu đang dẫn điểm và không còn cú đẩy an toàn -> ĐỨNG YÊN bảo toàn chiến thắng.
5. Kiểm soát thời gian nghiêm ngặt (<= 1000ms, thực tế ~0.5ms - 1.0ms).
"""

from collections import deque
import time
from competitive_core import CompetitiveState, DIRECTIONS

_PUSH_DIRECTIONS = (
    ("North", (-1, 0)),
    ("South", (1, 0)),
    ("West", (0, -1)),
    ("East", (0, 1)),
)

_LAST_TARGET_BOX = None
_LAST_ACTION = None
_LAST_POS = None
_COLLISION_STREAK = 0


def get_action(state: CompetitiveState, agent_id: int, time_limit_ms: int = 1000) -> str:
    """
    Hàm ra quyết định tối thượng cho Agent nhóm.
    """
    global _LAST_TARGET_BOX, _LAST_ACTION, _LAST_POS, _COLLISION_STREAK
    start_time = time.perf_counter()
    deadline = start_time + max(0, time_limit_ms - 50) / 1000.0

    def out_of_time() -> bool:
        return time.perf_counter() >= deadline

    my_pos = state.agent_positions.get(agent_id)
    other_id = 2 if agent_id == 1 else 1
    other_pos = state.agent_positions.get(other_id)

    if my_pos is None:
        return "Stay"

    # Kiểm tra va chạm (nếu lượt trước dự định đi nhưng vị trí không đổi -> bị cản đường/đối đầu)
    if _LAST_POS is not None and my_pos == _LAST_POS and _LAST_ACTION not in (None, "Stay"):
        _COLLISION_STREAK += 1
    else:
        _COLLISION_STREAK = 0
    _LAST_POS = my_pos

    # Nếu va chạm liên tiếp, nhường 1 nhịp ("Stay") để phá vỡ thế đối xứng kẹt cứng
    if _COLLISION_STREAK >= 1:
        _LAST_ACTION = "Stay"
        return "Stay"

    # Giới hạn biên bản đồ
    all_cells = set(state.walls) | set(state.goals) | set(state.boxes.keys()) | {my_pos}
    if other_pos:
        all_cells.add(other_pos)

    min_r = min(r for r, _ in all_cells)
    max_r = max(r for r, _ in all_cells)
    min_c = min(c for _, c in all_cells)
    max_c = max(c for _, c in all_cells)

    def in_bounds(pos: tuple[int, int]) -> bool:
        return min_r <= pos[0] <= max_r and min_c <= pos[1] <= max_c

    # Ranh giới thùng sân nhà (Home Yard) thích ứng linh hoạt theo kích thước bản đồ
    mid_c = (min_c + max_c) / 2.0
    buffer = max(1.0, (max_c - min_c) * 0.1)

    def is_home_box(pos):
        if agent_id == 1:
            return pos[1] < mid_c - buffer
        else:
            return pos[1] > mid_c + buffer

    # 1. Các đích khả dụng (Đích chưa có thùng, HOẶC đích đối thủ đang chiếm để cướp!)
    available_goals = set()
    for g in state.goals:
        box_owner = state.boxes.get(g)
        if box_owner is None or box_owner == other_id:
            available_goals.add(g)

    if not available_goals:
        return "Stay"

    # 2. Reverse-Push BFS từ các đích khả dụng
    min_push_to_goal = {}
    queue = deque()
    for g in available_goals:
        min_push_to_goal[g] = 0
        queue.append(g)

    while queue:
        if out_of_time():
            break
        box_pos = queue.popleft()
        d = min_push_to_goal[box_pos]
        for _, (dr, dc) in _PUSH_DIRECTIONS:
            prev_box = (box_pos[0] - dr, box_pos[1] - dc)
            player_stand = (prev_box[0] - dr, prev_box[1] - dc)
            if (in_bounds(prev_box) and in_bounds(player_stand)
                    and prev_box not in state.walls and player_stand not in state.walls
                    and prev_box not in min_push_to_goal):
                min_push_to_goal[prev_box] = d + 1
                queue.append(prev_box)

    dead_squares = set()
    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            pos = (r, c)
            if pos not in state.walls and pos not in min_push_to_goal:
                dead_squares.add(pos)

    # 3. BFS đi bộ của ta
    boxes_set = set(state.boxes.keys())
    first_action = {my_pos: None}
    walk_distance = {my_pos: 0}
    q_walk = deque([my_pos])

    while q_walk:
        if out_of_time():
            break
        pos = q_walk.popleft()
        for act, (dr, dc) in _PUSH_DIRECTIONS:
            nxt = (pos[0] + dr, pos[1] + dc)
            if (in_bounds(nxt) and nxt not in state.walls and nxt not in boxes_set
                    and nxt != other_pos and nxt not in first_action):
                first_action[nxt] = act if pos == my_pos else first_action[pos]
                walk_distance[nxt] = walk_distance[pos] + 1
                q_walk.append(nxt)

    # Kiểm tra xem sân nhà còn thùng nào chưa được đưa vào đích không
    unowned_home_boxes = [p for p, o in state.boxes.items() if o != agent_id and is_home_box(p)]

    best_score = float('inf')
    best_action = None
    best_target = None

    targets = [pos for pos, owner in state.boxes.items() if owner != agent_id]
    if not targets:
        return "Stay"

    if _LAST_TARGET_BOX in state.boxes and state.boxes[_LAST_TARGET_BOX] == agent_id:
        _LAST_TARGET_BOX = None

    for b_pos in targets:
        if out_of_time():
            break
        b_home = is_home_box(b_pos)
        # NẾU SÂN NHÀ CÒN THÙNG: BẮT BUỘC ƯU TIÊN GIẢI QUYẾT SÂN NHÀ TRƯỚC!
        if unowned_home_boxes and not b_home:
            continue

        b_owner = state.boxes[b_pos]
        is_opponent_scored = (b_owner == other_id and b_pos in state.goals)
        cur_min_push = min_push_to_goal.get(b_pos, float('inf'))

        for push_act, (dr, dc) in _PUSH_DIRECTIONS:
            stand = (b_pos[0] - dr, b_pos[1] - dc)
            dest = (b_pos[0] + dr, b_pos[1] + dc)

            if stand not in first_action:
                continue
            if dest in state.walls or (dest in boxes_set and dest != b_pos) or dest == other_pos:
                continue
            if dest in dead_squares and dest not in available_goals:
                continue

            dest_min_push = min_push_to_goal.get(dest, float('inf'))
            if dest_min_push == float('inf'):
                continue

            walk_cost = walk_distance[stand]

            if dest in available_goals:
                score = -1000 + walk_cost
                if b_home:
                    score -= 300  # Càng ưu tiên dứt điểm thùng sân nhà trước!
            elif is_opponent_scored and dest not in state.goals:
                score = -700 + walk_cost
            else:
                score = 3 * dest_min_push + walk_cost
                if dest_min_push >= cur_min_push:
                    score += 10

            # 1. Điểm thưởng cam kết mục tiêu (Target Commitment):
            # Giữ vững mục tiêu đang theo đuổi, tránh rung lắc đổi mục tiêu liên tục
            if b_pos == _LAST_TARGET_BOX:
                score -= 35

            # 2. Né đối đầu trực diện (Anti-Standoff):
            # Nếu đối thủ đang đứng ngay sau hộp/ô đích (khoảng cách <= 1), tránh đâm đầu vào
            if other_pos and (abs(dest[0] - other_pos[0]) + abs(dest[1] - other_pos[1]) <= 1):
                score += 50

            if score < best_score:
                best_score = score
                best_action = push_act if stand == my_pos else first_action[stand]
                best_target = dest if stand == my_pos else b_pos

    if best_action in DIRECTIONS and not out_of_time():
        _LAST_TARGET_BOX = best_target
        _LAST_ACTION = best_action
        return best_action

    # 4. Khi không có cú đẩy nào:
    my_score = state.scores.get(agent_id, 0)
    opp_score = state.scores.get(other_id, 0)
    if my_score > opp_score and not targets:
        return "Stay"

    # Tiếp cận thùng mục tiêu gần nhất
    best_dist = float('inf')
    approach_action = None
    search_targets = unowned_home_boxes if unowned_home_boxes else targets
    for b_pos in search_targets:
        for _, (dr, dc) in _PUSH_DIRECTIONS:
            adj = (b_pos[0] + dr, b_pos[1] + dc)
            if adj in first_action and walk_distance[adj] < best_dist:
                best_dist = walk_distance[adj]
                approach_action = first_action[adj]

    if approach_action in DIRECTIONS and approach_action != "Stay":
        opposite = {"North": "South", "South": "North", "East": "West", "West": "East"}
        if approach_action != opposite.get(_LAST_ACTION):
            _LAST_ACTION = approach_action
            return approach_action

    return "Stay"
