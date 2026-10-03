from collections import deque
import sys
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sokoban_core import SokobanProblem

class SokobanHeuristic:
    def __init__(self, problem: SokobanProblem):
        self.problem = problem
        self.walls = problem.walls
        self.targets = problem.targets
        # Bảng khoảng cách: dict mapping (row, col) -> số bước ngắn nhất né tường về đích gần nhất
        self.distance_map = self._precompute_distance_map()

    def _precompute_distance_map(self) -> dict[tuple[int, int], int]:
        """
        Dùng BFS đa nguồn (Multi-source BFS) xuất phát đồng thời từ tất cả các ô đích 'D'
        để tính khoảng cách ngắn nhất né tường đến mọi ô trống có thể đi tới.
        Chỉ tính 1 lần duy nhất lúc khởi tạo (O(Rows * Cols)).
        """
        distance_map = {}
        queue = deque()

        # Ban đầu, khoảng cách từ mỗi ô đích về chính nó là 0
        for target in self.targets:
            distance_map[target] = 0
            queue.append((target, 0))

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while queue:
            (curr_r, curr_c), dist = queue.popleft()

            for dr, dc in directions:
                nr, nc = curr_r + dr, curr_c + dc
                neighbor = (nr, nc)

                # Không đi xuyên qua tường
                if neighbor in self.walls:
                    continue

                # Nếu ô này chưa được ghé thăm
                if neighbor not in distance_map:
                    distance_map[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))

        return distance_map

    def is_corner_deadlock(self, box_pos: tuple[int, int]) -> bool:
        """
        Kiểm tra xem một vị trí thùng có bị kẹt vào góc chết hay không.
        Một ô là góc chết nếu nó KHÔNG phải là đích VÀ bị kẹp giữa 2 bức tường vuông góc:
        - Góc trên-trái: (North là tường) và (West là tường)
        - Góc trên-phải: (North là tường) và (East là tường)
        - Góc dưới-trái: (South là tường) và (West là tường)
        - Góc dưới-phải: (South là tường) và (East là tường)
        """
        if box_pos in self.targets:
            return False  # Nằm trên đích thì không bị coi là deadlock

        r, c = box_pos
        wall_north = (r - 1, c) in self.walls
        wall_south = (r + 1, c) in self.walls
        wall_west  = (r, c - 1) in self.walls
        wall_east  = (r, c + 1) in self.walls

        if (wall_north and wall_west) or \
           (wall_north and wall_east) or \
           (wall_south and wall_west) or \
           (wall_south and wall_east):
            return True

        return False

    def has_any_deadlock(self, box_positions: frozenset[tuple[int, int]]) -> bool:
        """Kiểm tra xem có bất kỳ thùng nào trên bàn cờ bị rơi vào góc chết không."""
        for box in box_positions:
            if self.is_corner_deadlock(box):
                return True
        return False

    def compute(self, state: tuple[tuple[int, int], frozenset[tuple[int, int]]]) -> float:
        """
        Tính giá trị heuristic h(state) cho trạng thái bàn cờ hiện tại.
        
        Trả về:
            float: Ước lượng chi phí tối thiểu còn lại để đưa mọi thùng về đích.
                   Trả về float('inf') nếu trạng thái dẫn vào ngõ cụt bế tắc.
        """
        agent_pos, box_positions = state

        # 1. Nếu có thùng rơi vào góc chết -> Bế tắc vĩnh viễn, loại bỏ nhánh
        if self.has_any_deadlock(box_positions):
            return float('inf')

        total_heuristic = 0
        for box in box_positions:
            dist = self.distance_map.get(box, float('inf'))
            # Nếu thùng ở ô mà không có đường nào về được đích -> Deadlock
            if dist == float('inf'):
                return float('inf')
            total_heuristic += dist

        return float(total_heuristic)


if __name__ == "__main__":
    import os

    import sys
    map_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("maps", "map_single.txt")

    print(f"=== Kiểm thử Heuristic trên bản đồ: {map_path} ===")
    problem = SokobanProblem(map_path)
    h_calculator = SokobanHeuristic(problem)

    print(f"[+] Đã tạo bảng khoảng cách BFS né tường cho {len(h_calculator.distance_map)} ô trống.")
    initial_h = h_calculator.compute(problem.initial_state)
    print(f"[+] Giá trị Heuristic h(initial_state) = {initial_h}")

    # Thử kiểm tra một trạng thái đích (thắng cuộc)
    goal_state = (problem.initial_state[0], problem.targets)
    goal_h = h_calculator.compute(goal_state)
    print(f"[+] Giá trị Heuristic tại đích h(goal_state) = {goal_h} (Phải bằng 0)")
