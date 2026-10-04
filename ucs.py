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

def solution(node):
    actions = []
    curr = node
    while curr.parent is not None:
        actions.append(curr.action)
        curr = curr.parent
    actions.reverse()
    return actions


def uniform_cost_search(problem: SokobanProblem, timeout_seconds: float = None, verbose: bool = False):
    start_time = time.perf_counter()
    node = Node(state=problem.initial_state, path_cost=0, parent=None, action= None)
    frontier = []
    counter = 0
    heapq.heappush(frontier, (node.path_cost, counter, node))
    frontier_states = {node.state: node.path_cost} # Ghi nhớ state hiện tại đang bao nhiêu
    explored = set()
    max_frontier_size = 1

    while True:
        if not frontier:
            execution_time = time.perf_counter() - start_time
            return None, len(explored), max_frontier_size, execution_time

        cost, _, candidate_node = heapq.heappop(frontier)
        node = candidate_node

        if problem.is_goal(node.state):
            execution_time = time.perf_counter() - start_time
            return (solution(node), node.path_cost), len(explored), max_frontier_size, execution_time

        explored.add(node.state)

        for action, new_state in problem.get_successors(node.state):
            child = Node(state=new_state, path_cost=node.path_cost + 1, parent=node, action=action)
            if (child.state not in explored) and (child.state not in frontier_states):
                frontier_states[child.state] = child.path_cost
                heapq.heappush(frontier, (child.path_cost, counter, child))
                counter += 1
            elif (child.state in frontier_states) and (frontier_states[child.state] > child.path_cost):
                frontier_states[child.state] = child.path_cost
                heapq.heappush(frontier, (child.path_cost, counter, child))
                counter += 1

        if len(frontier_states) > max_frontier_size:
            max_frontier_size = len(frontier_states)
    
class UCSSolver:
    
    def __init__(self, problem: SokobanProblem):
        self.problem = problem
        self.nodes_explored = 0
        self.max_frontier_size = 0
        self.execution_time = 0.0

    def search(self, timeout_seconds: float = None, verbose: bool = False):
        result, explored_count, max_front, exec_time = uniform_cost_search(
            self.problem,
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

    print(f"=== Đang chạy thử UCS (chuẩn mã giả slide) trên {map_path} ===")
    prob = SokobanProblem(map_path)
    solver = UCSSolver(prob)
    res = solver.search(timeout_seconds=10, verbose=True)

    if res:
        actions, cost = res
        print(f"\n[+] TÌM THẤY LỜI GIẢI!")
        print(f" -> Tổng chi phí (Total cost): {cost}")
        print(f" -> Số hành động: {len(actions)}")
        print(f" -> Danh sách hành động: {actions}")
        print(f" -> Thời gian thực thi: {solver.execution_time:.4f}s")
        print(f" -> Số node mở rộng (Explored): {solver.nodes_explored:,}")
        print(f" -> Frontier max: {solver.max_frontier_size:,}")
    else:
        print(f"[-] Không tìm thấy lời giải hoặc quá thời gian ({solver.execution_time:.2f}s).")
