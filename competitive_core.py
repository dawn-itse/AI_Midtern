import sys
import copy

# Đảm bảo in tiếng Việt không bị lỗi charmap trên terminal Windows
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DIRECTIONS = {
    "North": (-1, 0),
    "South": (1, 0),
    "West":  (0, -1),
    "East":  (0, 1),
    "Stay":  (0, 0)
}

class CompetitiveState:
    """
    Trạng thái của trò chơi Sokoban đối kháng 2 Agent.
    Đáp ứng chuẩn State-Space Formulation cho bài toán cạnh tranh (Yêu cầu 6).
    """
    def __init__(self, walls, goals, agent_positions, boxes, current_step, max_steps, scores=None):
        self.walls: frozenset[tuple[int, int]] = walls
        self.goals: frozenset[tuple[int, int]] = goals
        # Tọa độ 2 Agent: {1: (r1, c1), 2: (r2, c2)}
        self.agent_positions: dict[int, tuple[int, int]] = copy.deepcopy(agent_positions)
        # Tọa độ thùng và người sở hữu: {(r, c): owner_id} (owner_id: 1, 2 hoặc None nếu chưa vào đích)
        self.boxes: dict[tuple[int, int], int | None] = copy.deepcopy(boxes)
        self.current_step: int = current_step
        self.max_steps: int = max_steps
        # Điểm số: số thùng đang nằm trên đích của mỗi bên
        if scores is None:
            self.scores: dict[int, int] = {1: 0, 2: 0}
            self.update_scores()
        else:
            self.scores = copy.deepcopy(scores)

    def update_scores(self):
        """Cập nhật lại điểm số hiện tại dựa trên quyền sở hữu thùng trên các ô đích."""
        s1 = sum(1 for pos, owner in self.boxes.items() if pos in self.goals and owner == 1)
        s2 = sum(1 for pos, owner in self.boxes.items() if pos in self.goals and owner == 2)
        self.scores = {1: s1, 2: s2}

    def clone(self):
        return CompetitiveState(
            self.walls,
            self.goals,
            self.agent_positions,
            self.boxes,
            self.current_step,
            self.max_steps,
            self.scores
        )


class CompetitiveGame:
    """
    Môi trường mô phỏng trò chơi đối kháng 2 Agent (Yêu cầu 6 & 8).
    Xử lý tương tác, va chạm đồng thời và cơ chế tính điểm / cướp thùng.
    """
    def __init__(self, map_path: str, max_steps: int = 50):
        self.map_path = map_path
        self.max_steps = max_steps
        self.grid_rows = 0
        self.grid_cols = 0
        self.state = self._load_map(map_path, max_steps)

    def _load_map(self, map_path: str, max_steps: int) -> CompetitiveState:
        walls = set()
        goals = set()
        boxes = {}
        agent_positions = {}

        with open(map_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\r\n") for line in f.readlines()]

        self.grid_rows = len(lines)
        self.grid_cols = max(len(line) for line in lines) if lines else 0

        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                pos = (r, c)
                if ch == '%':
                    walls.add(pos)
                elif ch == 'D':
                    goals.add(pos)
                elif ch == 'B':
                    boxes[pos] = None
                elif ch == 'C':  # Thùng đã nằm sẵn trên đích
                    goals.add(pos)
                    boxes[pos] = None
                elif ch == '1' or ch == 'A':
                    agent_positions[1] = pos
                elif ch == '2':
                    agent_positions[2] = pos

        # Đảm bảo có đủ 2 Agent
        if 1 not in agent_positions or 2 not in agent_positions:
            raise ValueError("Bản đồ đối kháng bắt buộc phải có vị trí của cả Agent 1 ('1' hoặc 'A') và Agent 2 ('2')!")

        return CompetitiveState(
            walls=frozenset(walls),
            goals=frozenset(goals),
            agent_positions=agent_positions,
            boxes=boxes,
            current_step=0,
            max_steps=max_steps
        )

    def get_state(self) -> CompetitiveState:
        """Trả về bản sao của trạng thái trò chơi hiện tại."""
        return self.state.clone()

    def get_legal_actions(self, agent_id: int, state: CompetitiveState = None) -> list[str]:
        """
        Lấy danh sách các hành động hợp lệ đơn lẻ của 1 Agent (chưa tính va chạm với Agent kia).
        """
        if state is None:
            state = self.state

        pos = state.agent_positions[agent_id]
        legal = ["Stay"]

        for action, (dr, dc) in DIRECTIONS.items():
            if action == "Stay":
                continue
            new_pos = (pos[0] + dr, pos[1] + dc)

            # Đụng tường
            if new_pos in state.walls:
                continue

            # Đụng thùng
            if new_pos in state.boxes:
                new_box_pos = (new_pos[0] + dr, new_pos[1] + dc)
                # Sau lưng thùng là tường hoặc một thùng khác -> Không đẩy được
                if new_box_pos in state.walls or new_box_pos in state.boxes:
                    continue
                legal.append(action)
            else:
                legal.append(action)

        return legal

    def step(self, action1: str, action2: str) -> tuple[CompetitiveState, dict[int, int], bool]:
        """
        Thực hiện đồng thời (Simultaneously) hành động của cả 2 Agent trong 1 lượt chơi.
        Giải quyết xung đột va chạm và cập nhật điểm số.
        
        Trả về:
            tuple (next_state, scores, is_game_over)
        """
        if self.is_game_over():
            return self.get_state(), self.state.scores, True

        actions = {1: action1, 2: action2}
        cur_pos = copy.deepcopy(self.state.agent_positions)
        cur_boxes = copy.deepcopy(self.state.boxes)

        # 1. Tính toán ý định di chuyển của từng Agent độc lập
        intent_agent = {}  # {agent_id: intended_pos}
        intent_push = {}   # {agent_id: (old_box_pos, new_box_pos)}

        for aid in [1, 2]:
            act = actions.get(aid, "Stay")
            dr, dc = DIRECTIONS.get(act, (0, 0))
            new_pos = (cur_pos[aid][0] + dr, cur_pos[aid][1] + dc)

            # Kiểm tra va chạm với tường
            if new_pos in self.state.walls or act == "Stay":
                intent_agent[aid] = cur_pos[aid]
                continue

            # Kiểm tra đẩy thùng
            if new_pos in cur_boxes:
                new_box = (new_pos[0] + dr, new_pos[1] + dc)
                if new_box in self.state.walls or new_box in cur_boxes:
                    # Không đẩy được thùng -> Đứng yên
                    intent_agent[aid] = cur_pos[aid]
                else:
                    intent_agent[aid] = new_pos
                    intent_push[aid] = (new_pos, new_box)
            else:
                intent_agent[aid] = new_pos

        # 2. Xử lý va chạm đồng thời giữa 2 Agent (Simultaneous Collision Resolution)
        
        # 2.1. Cùng đẩy 1 thùng -> Cả hai bị kẹt, đứng yên
        if 1 in intent_push and 2 in intent_push:
            if intent_push[1][0] == intent_push[2][0]:
                intent_agent[1] = cur_pos[1]
                intent_agent[2] = cur_pos[2]
                intent_push.clear()

        # 2.2. Đẩy 2 thùng khác nhau vào CÙNG 1 ô trống -> Cả hai thùng và Agent đều đứng yên
        if 1 in intent_push and 2 in intent_push:
            if intent_push[1][1] == intent_push[2][1]:
                intent_agent[1] = cur_pos[1]
                intent_agent[2] = cur_pos[2]
                intent_push.clear()

        # 2.3. Hai Agent cùng đi vào 1 ô (Head-on Collision) -> Cả hai đứng yên
        if intent_agent[1] == intent_agent[2]:
            intent_agent[1] = cur_pos[1]
            intent_agent[2] = cur_pos[2]
            intent_push.clear()

        # 2.4. Đổi chỗ cho nhau (Swapping Collision: A đi vào chỗ B, B đi vào chỗ A) -> Đứng yên
        if intent_agent[1] == cur_pos[2] and intent_agent[2] == cur_pos[1]:
            intent_agent[1] = cur_pos[1]
            intent_agent[2] = cur_pos[2]
            intent_push.clear()

        # 2.5. Agent 1 đi vào chỗ Agent 2 nhưng Agent 2 lại không di chuyển đi đâu
        if intent_agent[1] == intent_agent[2]:
            intent_agent[1] = cur_pos[1]
        if intent_agent[2] == intent_agent[1]:
            intent_agent[2] = cur_pos[2]

        # 3. Cập nhật vị trí thùng và quyền sở hữu (Chiếm điểm / Cướp thùng)
        for aid, (old_b, new_b) in intent_push.items():
            if intent_agent[aid] != cur_pos[aid]:  # Agent này thực sự được di chuyển
                old_owner = cur_boxes.pop(old_b)
                
                # Nếu đẩy vào ô đích -> Thuộc quyền sở hữu của Agent này
                if new_b in self.state.goals:
                    cur_boxes[new_b] = aid
                else:
                    # Đẩy ra ngoài ô đích -> Thùng mất chủ quyền (về màu trung tính)
                    cur_boxes[new_b] = None

        # 4. Cập nhật lại trạng thái trò chơi
        self.state.agent_positions = intent_agent
        self.state.boxes = cur_boxes
        self.state.current_step += 1
        self.state.update_scores()

        return self.get_state(), self.state.scores, self.is_game_over()

    def is_game_over(self) -> bool:
        """Trò chơi kết thúc khi số bước đạt giới hạn max_steps."""
        return self.state.current_step >= self.max_steps

    def get_winner(self) -> int | None:
        """
        Xác định người chiến thắng:
        - Trả về 1: Agent 1 thắng (nhiều thùng hơn).
        - Trả về 2: Agent 2 thắng.
        - Trả về None: Hòa cờ.
        """
        s1 = self.state.scores[1]
        s2 = self.state.scores[2]
        if s1 > s2:
            return 1
        elif s2 > s1:
            return 2
        return None

    def print_board(self):
        """In bàn cờ ASCII ra màn hình console để dễ theo dõi."""
        grid = [[" " for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]

        for r, c in self.state.walls:
            grid[r][c] = "%"
        for r, c in self.state.goals:
            grid[r][c] = "D"

        for (r, c), owner in self.state.boxes.items():
            if (r, c) in self.state.goals:
                grid[r][c] = f"C{owner}" if owner else "C"
            else:
                grid[r][c] = "B"

        p1 = self.state.agent_positions[1]
        p2 = self.state.agent_positions[2]
        grid[p1[0]][p1[1]] = "1"
        grid[p2[0]][p2[1]] = "2"

        print(f"\n[Bước {self.state.current_step}/{self.max_steps}] Điểm: Agent 1 = {self.state.scores[1]} | Agent 2 = {self.state.scores[2]}")
        for row in grid:
            print("".join(row))


if __name__ == "__main__":
    import os
    map_p = os.path.join("maps", "battle_map.txt")
    print("=== Khởi tạo Môi trường Game Đối kháng (Yêu cầu 6) ===")
    game = CompetitiveGame(map_p, max_steps=10)
    game.print_board()

    print("\n[*] Thử nghiệm di chuyển đồng thời:")
    print(" - Agent 1 đi 'East' (tiến sang phải)")
    print(" - Agent 2 đi 'West' (tiến sang trái -> đối đầu)")
    
    next_s, sc, over = game.step("East", "West")
    game.print_board()
    print(f"\n[+] Kết quả kiểm tra va chạm: 2 Agent đối đầu và dừng đúng quy tắc!")
