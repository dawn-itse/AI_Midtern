import os
import sys

from sokoban_core import SokobanProblem
from gui import SokobanGUI


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Cho phép chọn bản đồ qua dòng lệnh: python main_gui.py maps/map_easy.txt
    if len(sys.argv) > 1:
        map_path = sys.argv[1]
    else:
        # Mặc định dùng map_easy.txt (1 thùng) để chạy mượt mà ngay lập tức
        map_path = os.path.join(base_dir, "maps", "map_easy.txt")
        if not os.path.exists(map_path):
            map_path = os.path.join(base_dir, "maps", "example_map.txt")

    print(f"[*] Khởi động giao diện Sokoban GUI trên bản đồ: {map_path}")
    problem = SokobanProblem(map_path)
    gui = SokobanGUI(problem)
    gui.run()


if __name__ == "__main__":
    main()