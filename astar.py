import heapq
import time
import sys

# Đảm bảo in tiếng Việt không bị lỗi charmap trên terminal Windows
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sokoban_core import Node, SokobanProblem
from heuristic import SokobanHeuristic

def solution(node):
    """Truy vết chuỗi hành động từ node đích ngược về node gốc."""
    actions = []
    curr = node
    while curr.parent is not None:
        actions.append(curr.action)
        curr = curr.parent
    actions.reverse()
    return actions


def astar_search(problem: SokobanProblem, heuristic: SokobanHeuristic = None, timeout_seconds: float = None, verbose: bool = False):
    """
    Thuật toán tìm kiếm A* (A-Star Search) cho Sokoban.
    Hàm đánh giá: f(n) = g(n) + h(n)
        - g(n): Chi phí đường đi thực tế tích lũy từ gốc đến node hiện tại (path_cost).
        - h(n): Ước lượng khoảng cách từ node hiện tại đến đích (Heuristic né tường + Deadlock).
    """
    start_time = time.perf_counter()

    if heuristic is None:
        heuristic = SokobanHeuristic(problem)

    # Node ban đầu: g(n) = 0
    start_node = Node(
        state=problem.initial_state,
        path_cost=0,
        parent=None,
        action=None
    )

    initial_h = heuristic.compute(start_node.state)
    if initial_h == float('inf'):
        # Bản đồ ban đầu đã bị deadlock ngay từ đầu
        return None, 0, 0, time.perf_counter() - start_time

    # Khởi tạo hàng đợi ưu tiên theo f_cost = g + h
    initial_f = start_node.path_cost + initial_h
    frontier = []
    counter = 0
    heapq.heappush(frontier, (initial_f, counter, start_node))
    counter += 1

    # frontier_states lưu g(n) tốt nhất từng biết của các state đang trong hàng đợi
    frontier_states = {start_node.state: start_node.path_cost}
    explored = set()
    max_frontier_size = 1

    while True:
        current_time = time.perf_counter()
        if timeout_seconds and (current_time - start_time) > timeout_seconds:
            if verbose:
                print(f"\n[A* Timeout] Đã hết thời gian cho phép ({timeout_seconds}s)!")
            return None, len(explored), max_frontier_size, current_time - start_time

        if not frontier:
            execution_time = time.perf_counter() - start_time
            return None, len(explored), max_frontier_size, execution_time

        # Bốc node có f_cost nhỏ nhất
        valid_node = None
        while frontier:
            f_cost, _, candidate_node = heapq.heappop(frontier)
            if candidate_node.state in explored:
                continue
            # Nếu node này có g(n) lớn hơn g(n) tốt nhất đã cập nhật -> bỏ qua
            if candidate_node.path_cost > frontier_states.get(candidate_node.state, float('inf')):
                continue
            valid_node = candidate_node
            if valid_node.state in frontier_states:
                del frontier_states[valid_node.state]
            break

        if valid_node is None:
            execution_time = time.perf_counter() - start_time
            return None, len(explored), max_frontier_size, execution_time

        node = valid_node

        # Kiểm tra đích (Goal Test)
        if problem.is_goal(node.state):
            execution_time = time.perf_counter() - start_time
            return (solution(node), node.path_cost), len(explored), max_frontier_size, execution_time

        explored.add(node.state)

        if verbose and len(explored) % 10000 == 0:
            print(f"[A*] Explored: {len(explored):,} nodes | Frontier: {len(frontier_states):,} | Time: {time.perf_counter() - start_time:.2f}s", flush=True)

        # Mở rộng các trạng thái con
        for action, new_state in problem.get_successors(node.state):
            child = Node(
                state=new_state,
                path_cost=node.path_cost + 1,
                parent=node,
                action=action
            )

            # Tính Heuristic h(child)
            h_cost = heuristic.compute(child.state)
            # Nếu rơi vào Deadlock (h = inf) -> Loại bỏ ngay lập tức (Pruning)!
            if h_cost == float('inf'):
                continue

            f_cost = child.path_cost + h_cost

            # Trường hợp 1: Trạng thái mới toanh
            if (child.state not in explored) and (child.state not in frontier_states):
                frontier_states[child.state] = child.path_cost
                heapq.heappush(frontier, (f_cost, counter, child))
                counter += 1

            # Trường hợp 2: Đã có trong frontier nhưng tìm thấy đường mới có g(n) rẻ hơn
            elif (child.state in frontier_states) and (frontier_states[child.state] > child.path_cost):
                frontier_states[child.state] = child.path_cost
                heapq.heappush(frontier, (f_cost, counter, child))
                counter += 1

        if len(frontier_states) > max_frontier_size:
            max_frontier_size = len(frontier_states)


class AStarSolver:
    """
    Lớp bao đóng OOP cho thuật toán A* (Requirement 2 & Requirement 5).
    """

    def __init__(self, problem: SokobanProblem):
        self.problem = problem
        self.heuristic = SokobanHeuristic(problem)
        self.nodes_explored = 0
        self.max_frontier_size = 0
        self.execution_time = 0.0

    def search(self, timeout_seconds: float = None, verbose: bool = False):
        result, explored_count, max_front, exec_time = astar_search(
            self.problem,
            heuristic=self.heuristic,
            timeout_seconds=timeout_seconds,
            verbose=verbose
        )
        self.nodes_explored = explored_count
        self.max_frontier_size = max_front
        self.execution_time = exec_time
        return result


if __name__ == "__main__":
    import os

    import sys
    map_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("maps", "map_single.txt")

    print(f"=== Đang chạy thử thuật toán A* trên {map_path} ===")
    prob = SokobanProblem(map_path)
    solver = AStarSolver(prob)
    res = solver.search(timeout_seconds=10, verbose=True)

    if res:
        actions, cost = res
        print(f"\n[+] TÌM THẤY LỜI GIẢI BẰNG A*!")
        print(f" -> Tổng chi phí (Total cost): {cost}")
        print(f" -> Số hành động: {len(actions)}")
        print(f" -> Danh sách hành động: {actions}")
        print(f" -> Thời gian thực thi: {solver.execution_time:.4f}s")
        print(f" -> Số node mở rộng (Explored): {solver.nodes_explored:,}")
        print(f" -> Frontier max: {solver.max_frontier_size:,}")
    else:
        print(f"[-] Không tìm thấy lời giải hoặc quá thời gian ({solver.execution_time:.2f}s).")
