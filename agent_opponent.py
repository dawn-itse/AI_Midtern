import random
from competitive_core import CompetitiveState, DIRECTIONS

def get_action(state: CompetitiveState, agent_id: int, time_limit_ms: int = 1000) -> str:
    """
    Thuật toán AI đối thủ (Baseline Opponent Agent) dùng để kiểm thử đối kháng (Yêu cầu 7 & 8).
    Chiến lược: Tham lam đơn giản (Greedy approach) - tiến về ô thùng gần nhất.
    """
    my_pos = state.agent_positions[agent_id]
    other_id = 1 if agent_id == 2 else 2
    other_pos = state.agent_positions[other_id]

    # Tìm danh sách thùng chưa có chủ hoặc của đối thủ
    target_boxes = [pos for pos, owner in state.boxes.items() if owner != agent_id]

    if not target_boxes:
        return "Stay"

    # Chọn thùng có khoảng cách Manhattan gần mình nhất
    target_box = min(target_boxes, key=lambda b: abs(b[0] - my_pos[0]) + abs(b[1] - my_pos[1]))

    # Tìm hướng đi giúp giảm khoảng cách tới thùng
    possible_moves = []
    for act, (dr, dc) in DIRECTIONS.items():
        if act == "Stay":
            continue
        nxt = (my_pos[0] + dr, my_pos[1] + dc)
        if nxt in state.walls or nxt == other_pos:
            continue

        if nxt in state.boxes:
            # Kiểm tra xem có đẩy được không
            box_dest = (nxt[0] + dr, nxt[1] + dc)
            if box_dest in state.walls or box_dest in state.boxes or box_dest == other_pos:
                continue

        dist = abs(nxt[0] - target_box[0]) + abs(nxt[1] - target_box[1])
        possible_moves.append((dist, act))

    if possible_moves:
        possible_moves.sort(key=lambda x: x[0])
        return possible_moves[0][1]

    return "Stay"
