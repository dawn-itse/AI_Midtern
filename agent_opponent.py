"""Goal-directed opponent with bounded multi-box push planning."""

from collections import deque
import heapq
import itertools
import os
import sys
import time

from competitive_core import DIRECTIONS


_PUSH_DIRECTIONS = tuple(
    (action, delta) for action, delta in DIRECTIONS.items() if action != "Stay"
)
_MAX_SEARCH_STATES = 220
_MAX_PUSH_DEPTH = 6
_HISTORY_SIZE = 24
_MEMORY = {}
_DEBUG_LAST_TARGET = {}


def _debug_enabled():
    return os.environ.get("SOKOBAN_AGENT_OPPONENT_DEBUG", "").lower() in {
        "1", "true", "yes", "on"
    }


def _debug_report(agent_id, state, target_box, target_goal, action,
                  expanded, stop_reason):
    """Write one diagnostic line per decision when debug mode is enabled."""
    if not _debug_enabled():
        return

    target = (target_box, target_goal) if target_box is not None else None
    previous_info = _DEBUG_LAST_TARGET.get(agent_id)
    previous = previous_info["target"] if previous_info else None
    continued_moving_box = False
    if previous and target and previous[1] == target[1]:
        old_positions = set(previous_info["boxes"])
        new_positions = set(state.boxes)
        removed = old_positions - new_positions
        added = new_positions - old_positions
        continued_moving_box = (
            removed == {previous[0]} and added == {target[0]}
        )
    changed = previous != target and not continued_moving_box
    _DEBUG_LAST_TARGET[agent_id] = {
        "target": target,
        "boxes": dict(state.boxes),
    }
    print(
        "[agent_opponent] "
        f"step={state.current_step} agent={agent_id} "
        f"agent_pos={state.agent_positions.get(agent_id)} "
        f"boxes={sorted(state.boxes.items())} goals={sorted(state.goals)} "
        f"target_box={target_box} target_goal={target_goal} "
        f"target_changed={changed} target_box_moved={continued_moving_box} "
        f"previous_target={previous} action={action} "
        f"states_visited={expanded} stop={stop_reason}",
        file=sys.stderr,
        flush=True,
    )


def _box_key(boxes):
    return tuple(sorted((pos, owner) for pos, owner in boxes.items()))


def _state_key(pos, boxes):
    return pos, _box_key(boxes)


def _remember_state(agent_id, step, map_key, state_key, boxes):
    """Keep short per-agent memory and infer the last completed push."""
    memory = _MEMORY.get(agent_id)
    if (memory is None or memory["map_key"] != map_key
            or step <= memory["step"]):
        memory = {
            "map_key": map_key,
            "step": step,
            "states": deque(maxlen=_HISTORY_SIZE),
            "pushes": deque(maxlen=8),
            "last_boxes": None,
            "target": None,
        }
        _MEMORY[agent_id] = memory

    previous_boxes = memory["last_boxes"]
    if previous_boxes is not None:
        old_positions = set(previous_boxes)
        new_positions = set(boxes)
        removed = old_positions - new_positions
        added = new_positions - old_positions
        if len(removed) == 1 and len(added) == 1:
            source = next(iter(removed))
            destination = next(iter(added))
            memory["pushes"].append((source, destination))
            if memory["target"] and memory["target"][0] == source:
                memory["target"] = (destination, memory["target"][1])

    if memory["target"]:
        target_box, target_goal = memory["target"]
        scored_goals = {
            pos for pos, owner in boxes.items()
            if pos in map_key[1] and owner == agent_id
        }
        if (boxes.get(target_box) == agent_id or target_box not in boxes
                or target_goal in scored_goals):
            memory["target"] = None

    memory["step"] = step
    memory["last_boxes"] = dict(boxes)
    memory["states"].append(state_key)
    return memory


def get_action(state, agent_id: int, time_limit_ms: int = 1000) -> str:
    """Return a legal step using bounded search over complete box layouts."""
    started = time.perf_counter()
    # Reserve time for returning a safe action even on unusually large maps.
    budget = max(0, time_limit_ms - 100) / 1000.0
    deadline = started + budget

    def out_of_time():
        return time.perf_counter() >= deadline

    def finish(action, stop_reason, target_box=None, target_goal=None,
               expanded=0):
        _debug_report(agent_id, state, target_box, target_goal, action,
                      expanded, stop_reason)
        return action

    my_pos = state.agent_positions.get(agent_id)
    other_id = 2 if agent_id == 1 else 1
    other_pos = state.agent_positions.get(other_id)

    def fallback():
        """Return a legal non-pushing move, or Stay if none is available."""
        if my_pos is None:
            return "Stay"
        boxes_now = set(state.boxes)
        for action, (dr, dc) in _PUSH_DIRECTIONS:
            nxt = (my_pos[0] + dr, my_pos[1] + dc)
            if nxt not in state.walls and nxt != other_pos and nxt not in boxes_now:
                return action
        return "Stay"

    if my_pos is None or other_pos is None or out_of_time():
        reason = "time" if out_of_time() else "missing_agent_position"
        return finish(fallback(), reason)

    boxes = dict(state.boxes)
    goals = set(state.goals)
    if not boxes or not goals:
        if agent_id in _MEMORY:
            _MEMORY[agent_id]["target"] = None
        return finish("Stay", "no_boxes_or_goals")
    if not any(owner != agent_id for owner in boxes.values()):
        if agent_id in _MEMORY:
            _MEMORY[agent_id]["target"] = None
        return finish("Stay", "no_unowned_target_box")

    # Bound the search to the known board, including states with open borders.
    known = set(state.walls) | goals | set(boxes) | {my_pos, other_pos}
    min_row = min(r for r, _ in known)
    max_row = max(r for r, _ in known)
    min_col = min(c for _, c in known)
    max_col = max(c for _, c in known)

    def in_bounds(pos):
        return min_row <= pos[0] <= max_row and min_col <= pos[1] <= max_col

    # Reverse-push distances identify static dead squares and give a useful
    # lower bound. Other boxes are handled separately in the push search.
    goal_distance = {}
    queue = deque()
    for goal in goals:
        goal_distance[goal] = 0
        queue.append(goal)
    while queue:
        if out_of_time():
            return finish(fallback(), "time_reverse_push_bfs")
        box_pos = queue.popleft()
        distance = goal_distance[box_pos]
        for _, (dr, dc) in _PUSH_DIRECTIONS:
            prev_box = (box_pos[0] - dr, box_pos[1] - dc)
            stand = (prev_box[0] - dr, prev_box[1] - dc)
            if (not in_bounds(prev_box) or not in_bounds(stand)
                    or prev_box in state.walls or stand in state.walls
                    or prev_box in goal_distance):
                continue
            goal_distance[prev_box] = distance + 1
            queue.append(prev_box)

    # Keep per-goal distances for distinct box-to-goal assignment. A single
    # multi-source distance is useful for dead squares, but cannot distinguish
    # which particular goal a box is assigned to.
    goal_distances = {}
    for goal in goals:
        distances = {goal: 0}
        goal_queue = deque([goal])
        while goal_queue:
            if out_of_time():
                return finish(fallback(), "time_goal_distance_bfs")
            box_pos = goal_queue.popleft()
            distance = distances[box_pos]
            for _, (dr, dc) in _PUSH_DIRECTIONS:
                prev_box = (box_pos[0] - dr, box_pos[1] - dc)
                stand = (prev_box[0] - dr, prev_box[1] - dc)
                if (not in_bounds(prev_box) or not in_bounds(stand)
                        or prev_box in state.walls or stand in state.walls
                        or prev_box in distances):
                    continue
                distances[prev_box] = distance + 1
                goal_queue.append(prev_box)
        goal_distances[goal] = distances

    dead_squares = {
        (r, c)
        for r in range(min_row, max_row + 1)
        for c in range(min_col, max_col + 1)
        if (r, c) not in state.walls and (r, c) not in goal_distance
    }

    map_key = (frozenset(state.walls), frozenset(goals))
    current_key = _state_key(my_pos, boxes)
    memory = _remember_state(
        agent_id, state.current_step, map_key, current_key, boxes
    )
    recent_states = set(memory["states"])
    recent_pushes = tuple(memory["pushes"])
    preferred_target = memory.get("target")

    def completed_goals(layout):
        return {
            pos for pos, owner in layout.items()
            if pos in goals and owner == agent_id
        }

    def assigned_goal(layout, box_pos):
        """Return the same greedy goal assignment used by layout_score."""
        if box_pos in goals:
            return box_pos
        targets = [(p, owner) for p, owner in layout.items()
                   if owner != agent_id]
        remaining_goals = goals - completed_goals(layout)
        occupied_goals = {p for p in layout if p in goals}
        pairs = []
        for target, _owner in targets:
            for goal in remaining_goals:
                if goal in occupied_goals and goal != target:
                    continue
                dist = goal_distances[goal].get(target, float("inf"))
                if dist < float("inf"):
                    pairs.append((dist, target, goal))
        pairs.sort()
        assigned_boxes = set()
        assigned_goals = set()
        for _, target, goal in pairs:
            if target in assigned_boxes or goal in assigned_goals:
                continue
            assigned_boxes.add(target)
            assigned_goals.add(goal)
            if target == box_pos:
                return goal
        return None

    if preferred_target:
        preferred_box, preferred_goal = preferred_target
        if (preferred_box not in boxes or boxes[preferred_box] == agent_id
                or preferred_goal not in goals
                or preferred_goal in completed_goals(boxes)
                or preferred_box not in goal_distances[preferred_goal]):
            preferred_target = None
            memory["target"] = None

    locked_box = preferred_target[0] if preferred_target else None
    locked_goal = preferred_target[1] if preferred_target else None

    def reachable(player, box_positions):
        """BFS over walking cells; record distance and first action per cell."""
        first = {player: None}
        distance = {player: 0}
        walk_queue = deque([player])
        while walk_queue:
            if out_of_time():
                break
            pos = walk_queue.popleft()
            for action, (dr, dc) in _PUSH_DIRECTIONS:
                nxt = (pos[0] + dr, pos[1] + dc)
                if (not in_bounds(nxt) or nxt in state.walls
                        or nxt in box_positions or nxt == other_pos
                        or nxt in first):
                    continue
                first[nxt] = action if pos == player else first[pos]
                distance[nxt] = distance[pos] + 1
                walk_queue.append(nxt)
        return first, distance

    def layout_score(layout):
        """Score a complete layout, respecting occupied goals and box blocking."""
        own_goals = sum(1 for p, owner in layout.items()
                        if p in goals and owner == agent_id)
        occupied_goals = {p for p in layout if p in goals}
        targets = [p for p, owner in layout.items() if owner != agent_id]
        remaining_goals = goals - completed_goals(layout)

        # Greedy distinct assignment: a box cannot claim an already occupied
        # goal, and each free goal can be assigned to at most one box.
        pairs = []
        for box_pos in targets:
            for goal in remaining_goals:
                if goal in occupied_goals and goal != box_pos:
                    continue
                dist = goal_distances[goal].get(box_pos, float("inf"))
                if dist < float("inf"):
                    pairs.append((dist, box_pos, goal))
        assigned_boxes = set()
        assigned_goals = set()
        total_distance = 0
        pairs.sort()
        for dist, box_pos, goal in pairs:
            if box_pos in assigned_boxes or goal in assigned_goals:
                continue
            assigned_boxes.add(box_pos)
            assigned_goals.add(goal)
            total_distance += dist

        # Reward progress while preserving a strong preference for scoring.
        unassigned = max(0, len(targets) - len(assigned_boxes))
        return (-1000 * own_goals + 3 * total_distance + 20 * unassigned)

    # Search nodes are macro states after a push. Their box layout contains all
    # boxes, so a blocked goal or a box blocking another box is visible.
    initial = (my_pos, boxes, None, 0, 0, None, None, locked_box)
    frontier = []
    sequence = itertools.count()
    heapq.heappush(frontier, (layout_score(boxes), next(sequence), initial))
    visited = {(my_pos, _box_key(boxes))}
    best_action = None
    best_box = None
    best_goal = None
    best_score = layout_score(boxes)
    target_complete_action = None
    target_complete_score = float("inf")
    target_plan_action = None
    target_plan_score = (float("inf"), float("inf"))
    expanded = 0

    while frontier and expanded < _MAX_SEARCH_STATES and not out_of_time():
        _, _, node = heapq.heappop(frontier)
        (player, layout, first_action, depth, walking_cost,
         first_box, first_goal, node_target_pos) = node
        expanded += 1
        if depth >= _MAX_PUSH_DEPTH:
            continue

        occupied = set(layout)
        reachable_cells, walk_distance = reachable(player, occupied)
        if out_of_time():
            break

        for box_pos, owner in tuple(layout.items()):
            if owner == agent_id:
                continue
            for push_action, (dr, dc) in _PUSH_DIRECTIONS:
                if out_of_time():
                    break
                stand = (box_pos[0] - dr, box_pos[1] - dc)
                dest = (box_pos[0] + dr, box_pos[1] + dc)
                if (stand not in reachable_cells or dest in state.walls
                        or dest == other_pos or dest in occupied):
                    continue
                if dest in dead_squares and dest not in goals:
                    continue

                if (locked_goal is not None and box_pos == node_target_pos
                        and dest in goals and dest != locked_goal):
                    continue

                next_layout = dict(layout)
                del next_layout[box_pos]
                next_layout[dest] = agent_id if dest in goals else None
                next_player = box_pos
                next_depth = depth + 1
                action = (push_action if depth == 0 and stand == my_pos
                          else reachable_cells.get(stand) if depth == 0
                          else first_action)
                if action is None:
                    action = push_action if depth == 0 else first_action

                planned_box = box_pos if depth == 0 else first_box
                if depth == 0:
                    if (preferred_target and box_pos == preferred_target[0]
                            and preferred_target[1] in goals
                            and preferred_target[1] not in completed_goals(next_layout)):
                        planned_goal = preferred_target[1]
                    else:
                        planned_goal = assigned_goal(next_layout, dest)
                else:
                    planned_goal = first_goal

                key = (next_player, _box_key(next_layout))
                if key in visited:
                    continue
                visited.add(key)

                # Do not revisit a recent full state. This catches cycles that
                # span separate get_action calls, not just loops in this search.
                if key in recent_states and key != current_key:
                    continue

                # Penalize an immediate reversal of a recently observed push;
                # allow it only when no better plan is found.
                reversal_penalty = 0
                if any((dest, box_pos) == push for push in recent_pushes[-2:]):
                    reversal_penalty = 18

                step_cost = walk_distance.get(stand, 0) + 3
                total_walk = walking_cost + step_cost
                score = layout_score(next_layout) + total_walk + reversal_penalty
                if (preferred_target
                        and (planned_box, planned_goal) != preferred_target):
                    score += 80
                if (score < best_score or best_action is None
                        and score <= best_score + 12):
                    best_score = score
                    best_action = action
                    best_box = planned_box
                    best_goal = planned_goal

                next_target_pos = node_target_pos
                if node_target_pos == box_pos:
                    next_target_pos = dest
                    if next_layout.get(dest) == agent_id and dest == locked_goal:
                        if total_walk < target_complete_score:
                            target_complete_action = action
                            target_complete_score = total_walk
                    elif locked_goal is not None:
                        remaining_distance = goal_distances[locked_goal].get(
                            dest, float("inf")
                        )
                        plan_score = (remaining_distance,
                                      total_walk + reversal_penalty)
                        if (remaining_distance < float("inf")
                                and plan_score < target_plan_score):
                            target_plan_action = action
                            target_plan_score = plan_score

                if locked_goal is not None and next_target_pos is not None:
                    target_distance = goal_distances[locked_goal].get(
                        next_target_pos, float("inf")
                    )
                    priority = target_distance * 100 + total_walk
                    if (next_layout.get(next_target_pos) == agent_id
                            and next_target_pos == locked_goal):
                        priority -= 100000
                else:
                    priority = layout_score(next_layout) + total_walk
                heapq.heappush(
                    frontier,
                    (priority, next(sequence),
                     (next_player, next_layout, action, next_depth,
                      total_walk, planned_box, planned_goal,
                      next_target_pos)),
                )

    if out_of_time():
        stop_reason = "time"
    elif expanded >= _MAX_SEARCH_STATES and frontier:
        stop_reason = "state_limit"
    else:
        stop_reason = "exhausted"

    if preferred_target:
        if target_complete_action in DIRECTIONS:
            memory["target"] = preferred_target
            return finish(target_complete_action, stop_reason,
                          locked_box, locked_goal, expanded)
        if target_plan_action in DIRECTIONS:
            memory["target"] = preferred_target
            return finish(target_plan_action, stop_reason,
                          locked_box, locked_goal, expanded)
        if stop_reason != "exhausted":
            # The bounded search did not prove this target infeasible. Preserve
            # it and avoid switching merely because the state/time cap was hit.
            memory["target"] = preferred_target
            return finish(fallback(), stop_reason,
                          locked_box, locked_goal, expanded)
        # The search was exhausted without a legal path toward the incumbent.
        memory["target"] = None
        preferred_target = None

    valid_preferred = (
        preferred_target is not None
        and preferred_target[0] in boxes
        and boxes[preferred_target[0]] != agent_id
        and preferred_target[1] not in completed_goals(boxes)
    )
    if not valid_preferred:
        memory["target"] = (
            (best_box, best_goal)
            if best_box in boxes and boxes[best_box] != agent_id
            and best_goal is not None
            else None
        )

    if best_action in DIRECTIONS and not out_of_time():
        return finish(best_action, stop_reason, best_box, best_goal, expanded)

    # If planning runs out of time, return the first legal walking step found.
    if out_of_time():
        return finish(fallback(), stop_reason, expanded=expanded)
    action = best_action if best_action in DIRECTIONS else "Stay"
    return finish(action, stop_reason, best_box, best_goal, expanded)
