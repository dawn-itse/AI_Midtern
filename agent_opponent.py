"""Goal-directed baseline opponent for the competitive Sokoban game."""

from collections import deque
import time

from competitive_core import CompetitiveState, DIRECTIONS


_PUSH_DIRECTIONS = tuple(
    (action, delta) for action, delta in DIRECTIONS.items() if action != "Stay"
)


def get_action(state: CompetitiveState, agent_id: int, time_limit_ms: int = 1000) -> str:
    """Return one step toward a reachable, useful box push using bounded BFS."""
    started = time.perf_counter()
    budget = max(0, time_limit_ms) / 1000.0
    deadline = started + budget

    def out_of_time():
        return time.perf_counter() >= deadline

    def fallback():
        """Prefer an unoccupied step; avoid an unplanned push on timeout."""
        pos = state.agent_positions[agent_id]
        other_id = 1 if agent_id == 2 else 2
        other_pos = state.agent_positions[other_id]
        boxes = set(state.boxes)
        for action, (dr, dc) in _PUSH_DIRECTIONS:
            nxt = (pos[0] + dr, pos[1] + dc)
            if nxt in state.walls or nxt == other_pos:
                continue
            if nxt not in boxes:
                return action
        return "Stay"

    my_pos = state.agent_positions.get(agent_id)
    other_id = 1 if agent_id == 2 else 2
    other_pos = state.agent_positions.get(other_id)
    if my_pos is None or other_pos is None or out_of_time():
        return fallback()

    boxes = set(state.boxes)
    targets = [pos for pos, owner in state.boxes.items() if owner != agent_id]
    if not targets:
        return "Stay"

    # Competitive maps are enclosed by walls. This finite map bound keeps BFS
    # finite even if an input map omits part of its outer wall.
    known = set(state.walls) | set(state.goals) | boxes | {my_pos, other_pos}
    min_row = min(r for r, _ in known)
    max_row = max(r for r, _ in known)
    min_col = min(c for _, c in known)
    max_col = max(c for _, c in known)

    def in_bounds(pos):
        return min_row <= pos[0] <= max_row and min_col <= pos[1] <= max_col

    # Reverse-push BFS from goals: gives a box distance that respects walls,
    # and marks cells from which a box can never reach any goal as dead squares.
    goal_distance = {}
    queue = deque()
    for goal in state.goals:
        goal_distance[goal] = 0
        queue.append(goal)
    while queue:
        if out_of_time():
            return fallback()
        box_pos = queue.popleft()
        distance = goal_distance[box_pos]
        for _, (dr, dc) in _PUSH_DIRECTIONS:
            prev_box = (box_pos[0] - dr, box_pos[1] - dc)
            player_stand = (prev_box[0] - dr, prev_box[1] - dc)
            if (not in_bounds(prev_box) or not in_bounds(player_stand)
                    or prev_box in state.walls or player_stand in state.walls
                    or prev_box in goal_distance):
                continue
            goal_distance[prev_box] = distance + 1
            queue.append(prev_box)
    dead_squares = set()
    for r in range(min_row, max_row + 1):
        if out_of_time():
            return fallback()
        for c in range(min_col, max_col + 1):
            pos = (r, c)
            if pos not in state.walls and pos not in goal_distance:
                dead_squares.add(pos)

    # Player BFS: for each reachable free cell retain the first action so a
    # selected push can be approached without walking through boxes/opponent.
    first_action = {my_pos: None}
    walk_distance = {my_pos: 0}
    queue = deque([my_pos])
    while queue:
        if out_of_time():
            break
        pos = queue.popleft()
        for action, (dr, dc) in _PUSH_DIRECTIONS:
            nxt = (pos[0] + dr, pos[1] + dc)
            if (not in_bounds(nxt) or nxt in state.walls or nxt in boxes
                    or nxt == other_pos or nxt in first_action):
                continue
            first_action[nxt] = action if pos == my_pos else first_action[pos]
            walk_distance[nxt] = walk_distance[pos] + 1
            queue.append(nxt)

    # Consider each reachable stance and legal push. Minimize walking plus
    # remaining box-to-goal distance; reject pushes into static dead squares.
    best_score = float("inf")
    best_action = None
    for box_pos in targets:
        if out_of_time():
            break
        current_goal_distance = goal_distance.get(box_pos, float("inf"))
        for push_action, (dr, dc) in _PUSH_DIRECTIONS:
            if out_of_time():
                break
            stand = (box_pos[0] - dr, box_pos[1] - dc)
            dest = (box_pos[0] + dr, box_pos[1] + dc)
            if stand not in first_action or dest in state.walls or dest in boxes or dest == other_pos:
                continue
            if dest in dead_squares and dest not in state.goals:
                continue
            next_goal_distance = goal_distance.get(dest, float("inf"))
            if next_goal_distance == float("inf"):
                continue

            # Give progress toward a goal the strongest weight. Walking cost
            # then chooses a nearby box among pushes with similar prospects.
            walk_cost = walk_distance[stand]
            score = 4 * next_goal_distance + walk_cost
            if next_goal_distance >= current_goal_distance:
                score += 2
            if score < best_score:
                best_score = score
                best_action = push_action if stand == my_pos else first_action[stand]

    if best_action in DIRECTIONS and not out_of_time():
        return best_action

    # If the budget expired during planning, use any first move found by BFS;
    # otherwise the simple fallback guarantees a valid direction or Stay.
    if len(first_action) > 1:
        return next(action for action in first_action.values() if action is not None)
    return fallback()
