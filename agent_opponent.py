"""Agent đối kháng Sokoban dùng BFS và đánh giá nước đẩy tham lam."""

from collections import deque
import time

from competitive_core import DIRECTIONS


_MOVES = tuple((action, delta) for action, delta in DIRECTIONS.items()
              if action != "Stay")
_MEMORY = {}


def _layout_key(boxes):
    """Tạo khóa ổn định cho vị trí và chủ sở hữu các hộp."""
    return tuple(sorted(boxes.items()))


def _reverse_push_bfs(goal, walls, bounds, deadline):
    """Tính số lần đẩy tối thiểu từ các ô tới một goal."""
    min_row, max_row, min_col, max_col = bounds
    distances = {goal: 0}
    queue = deque([goal])
    while queue and time.perf_counter() < deadline:
        box = queue.popleft()
        for _, (dr, dc) in _MOVES:
            previous = (box[0] - dr, box[1] - dc)
            stance = (previous[0] - dr, previous[1] - dc)
            inside = (min_row <= previous[0] <= max_row
                      and min_col <= previous[1] <= max_col
                      and min_row <= stance[0] <= max_row
                      and min_col <= stance[1] <= max_col)
            if (not inside or previous in walls or stance in walls
                    or previous in distances):
                continue
            distances[previous] = distances[box] + 1
            queue.append(previous)
    return distances


def _reachable_cells(start, boxes, walls, other, bounds, deadline):
    """Tìm các ô agent đi bộ tới được và bước đầu tiên trên mỗi đường."""
    min_row, max_row, min_col, max_col = bounds
    first_action = {start: None}
    distance = {start: 0}
    queue = deque([start])
    while queue and time.perf_counter() < deadline:
        current = queue.popleft()
        for action, (dr, dc) in _MOVES:
            nxt = (current[0] + dr, current[1] + dc)
            inside = min_row <= nxt[0] <= max_row and min_col <= nxt[1] <= max_col
            if (not inside or nxt in walls or nxt in boxes or nxt == other
                    or nxt in distance):
                continue
            distance[nxt] = distance[current] + 1
            first_action[nxt] = action if current == start else first_action[current]
            queue.append(nxt)
    return first_action, distance


def _memory_for(agent_id, state, map_key):
    """Lưu target và một đoạn lịch sử ngắn để phát hiện vòng lặp."""
    memory = _MEMORY.get(agent_id)
    if (memory is None or memory["map"] != map_key
            or state.current_step <= memory["step"]):
        memory = {"map": map_key, "step": -1, "target": None, "boxes": {},
                  "push": None, "turns": deque(maxlen=12),
                  "layouts": deque(maxlen=6), "other": None}
        _MEMORY[agent_id] = memory

    old_positions = set(memory["boxes"])
    new_positions = set(state.boxes)
    removed, added = old_positions - new_positions, new_positions - old_positions
    if len(removed) == len(added) == 1:
        source, destination = next(iter(removed)), next(iter(added))
        memory["push"] = (source, destination)
        if memory["target"] and memory["target"][0] == source:
            memory["target"] = (destination, memory["target"][1])

    key = (state.agent_positions.get(agent_id), _layout_key(state.boxes),
           tuple(sorted(state.scores.items())))
    repeated_actions = {action for old_key, action in memory["turns"]
                        if old_key == key}
    other_id = 1 if agent_id == 2 else 2
    previous_other = memory["other"]
    memory["other"] = state.agent_positions.get(other_id)
    memory["step"] = state.current_step
    memory["boxes"] = dict(state.boxes)

    layout = _layout_key(state.boxes)
    if not memory["layouts"] or memory["layouts"][-1] != layout:
        memory["layouts"].append(layout)
    return memory, key, repeated_actions, previous_other


def _home_side(position, agent_id, center_column):
    """Xác định nửa sân gần vị trí xuất phát của từng agent."""
    return position[1] < center_column if agent_id == 1 else position[1] > center_column


def _safe_fallback():
    """Đứng yên khi không có cú đẩy hữu ích để tránh đi lang thang."""
    return "Stay"


def get_action(state, agent_id: int, time_limit_ms: int = 1000) -> str:
    """Chọn một bước đi hoặc đẩy hợp lệ trong ngân sách thời gian."""
    started = time.perf_counter()
    deadline = started + max(1, time_limit_ms - 50) / 1000
    player = state.agent_positions.get(agent_id)
    other_id = 1 if agent_id == 2 else 2
    other = state.agent_positions.get(other_id)
    if player is None or other is None:
        return "Stay"

    boxes, goals = dict(state.boxes), set(state.goals)
    board = set(state.walls) | goals | set(boxes) | {player, other}
    min_row, max_row = min(r for r, _ in board), max(r for r, _ in board)
    min_col, max_col = min(c for _, c in board), max(c for _, c in board)
    bounds = (min_row, max_row, min_col, max_col)
    center_column = (min_col + max_col) / 2
    map_key = (frozenset(state.walls), frozenset(goals))
    memory, state_key, repeated_actions, previous_other = _memory_for(
        agent_id, state, map_key
    )

    targets = {pos for pos, owner in boxes.items() if owner != agent_id}
    finished_goals = {pos for pos, owner in boxes.items()
                      if pos in goals and owner == agent_id}
    free_goals = {goal for goal in goals - finished_goals if goal not in boxes}
    if not targets or not free_goals or time.perf_counter() >= deadline:
        memory["turns"].append((state_key, "Stay"))
        return _safe_fallback()

    distances = {}
    for goal in free_goals:
        distances[goal] = _reverse_push_bfs(goal, state.walls, bounds, deadline)
        if time.perf_counter() >= deadline:
            memory["turns"].append((state_key, "Stay"))
            return _safe_fallback()

    reachable, walk_distance = _reachable_cells(
        player, set(boxes), state.walls, other, bounds, deadline
    )
    if time.perf_counter() >= deadline:
        memory["turns"].append((state_key, "Stay"))
        return _safe_fallback()

    # Chỉ giữ các cặp hộp-goal có đường đẩy tĩnh; hộp nhà được ưu tiên mềm.
    pairs = []
    home_boxes = set()
    for box in targets:
        for goal, distance_map in distances.items():
            push_distance = distance_map.get(box)
            if push_distance is None:
                continue
            pairs.append((box, goal, distance_map, push_distance))
            if _home_side(box, agent_id, center_column):
                home_boxes.add(box)

    if not pairs:
        memory["target"] = None
        memory["turns"].append((state_key, "Stay"))
        return _safe_fallback()

    old_target = memory["target"]
    if old_target and not any(box == old_target[0] and goal == old_target[1]
                              for box, goal, _, _ in pairs):
        old_target = None

    recent_layouts = set(memory["layouts"])
    last_push = memory["push"]
    occupied = set(boxes)
    candidates = []

    for box, goal, distance_map, current_distance in pairs:
        for push_action, (dr, dc) in _MOVES:
            if time.perf_counter() >= deadline:
                memory["turns"].append((state_key, "Stay"))
                return _safe_fallback()
            stand = (box[0] - dr, box[1] - dc)
            destination = (box[0] + dr, box[1] + dc)
            if (stand not in reachable or destination in state.walls
                    or destination == other or destination in occupied):
                continue

            next_distance = distance_map.get(destination)
            if next_distance is None or next_distance >= current_distance:
                continue
            next_boxes = dict(boxes)
            del next_boxes[box]
            next_boxes[destination] = agent_id if destination in goals else None
            next_layout = tuple(sorted(next_boxes.items()))

            is_home = _home_side(box, agent_id, center_column)
            home_bias = -5 if is_home and home_boxes else 0
            commitment = -4 if old_target == (box, goal) else 0
            cycle_penalty = 12 if next_layout in recent_layouts else 0
            reverse_penalty = 10 if last_push == (destination, box) else 0

            action = reachable[stand] or push_action
            dr_action, dc_action = DIRECTIONS[action]
            next_player = (player[0] + dr_action, player[1] + dc_action)
            close_to_other = (
                abs(next_player[0] - other[0]) + abs(next_player[1] - other[1]) <= 1
            )
            standoff_penalty = 4 if close_to_other or next_player == previous_other else 0

            # Mỗi cú đẩy được so bằng khoảng cách còn lại, đường đi và ưu tiên sân.
            score = (8 * next_distance + walk_distance[stand] + home_bias
                     + commitment + cycle_penalty + reverse_penalty
                     + standoff_penalty)
            target_after = destination if stand == player else box
            candidates.append((score, action, target_after, goal, next_layout))

    candidates.sort(key=lambda item: item[0])
    chosen = next((item for item in candidates if item[1] not in repeated_actions), None)
    if chosen is None:
        memory["turns"].append((state_key, "Stay"))
        return _safe_fallback()

    _, action, target_box, goal, _ = chosen
    memory["target"] = (target_box, goal)
    memory["turns"].append((state_key, action))
    return action
