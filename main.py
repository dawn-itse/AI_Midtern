import sys
import os
import time

# Đảm bảo terminal Windows không bị lỗi UnicodeEncodeError khi in tiếng Việt
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sokoban_core import SokobanProblem
from ucs import UCSSolver
from astar import AStarSolver

def print_banner():
    print("=" * 70)
    print("      ĐỒ ÁN GIỮA KỲ: NHẬP MÔN TRÍ TUỆ NHÂN TẠO - SOKOBAN SEARCH")
    print("=" * 70)

def print_map_info(problem: SokobanProblem, map_path: str):
    agent_pos, box_positions = problem.initial_state
    print(f"\n[+] Bản đồ: {map_path}")
    print(f" - Tường (%): {len(problem.walls)} ô")
    print(f" - Điểm đích (D): {len(problem.targets)} ô tại {sorted(list(problem.targets))}")
    print(f" - Số lượng thùng (B): {len(box_positions)} thùng tại {sorted(list(box_positions))}")
    print(f" - Vị trí khởi đầu Agent (A): {agent_pos}")
    print("-" * 70)

def run_single_algo(solver_class, algo_name: str, problem: SokobanProblem, timeout_seconds: float = None):
    print(f"\n[*] Đang thực thi thuật toán {algo_name}...")
    solver = solver_class(problem)
    result = solver.search(timeout_seconds=timeout_seconds, verbose=False)

    print("-" * 70)
    print(f"                      KẾT QUẢ TÌM KIẾM ({algo_name})")
    print("-" * 70)

    if result:
        actions, total_cost = result
        print(f"[THÀNH CÔNG] Đã tìm thấy lời giải tối ưu!")
        print(f" -> Tổng chi phí (Total Cost): {total_cost}")
        print(f" -> Số bước hành động (Action count): {len(actions)}")
        print(f" -> Thời gian thực thi: {solver.execution_time:.4f} giây")
        print(f" -> Số node đã mở rộng (Explored nodes): {solver.nodes_explored:,}")
        print(f" -> Kích thước Frontier cực đại: {solver.max_frontier_size:,}")
        print(f" -> Danh sách hành động: {actions}")
        return solver, total_cost, len(actions)
    else:
        print(f"[THẤT BẠI / TIMEOUT] Không tìm thấy lời giải trong {solver.execution_time:.2f} giây.")
        print(f" -> Số node đã duyệt: {solver.nodes_explored:,}")
        print(f" -> Kích thước Frontier: {solver.max_frontier_size:,}")
        return solver, None, None

def compare_algorithms(problem: SokobanProblem, timeout_seconds: float = 30):
    print("\n" + "=" * 70)
    print("            SO SÁNH HIỆU NĂNG TRỰC TIẾP: UCS VS A*")
    print("=" * 70)

    solver_ucs, cost_ucs, steps_ucs = run_single_algo(UCSSolver, "UCS", problem, timeout_seconds=timeout_seconds)
    solver_astar, cost_astar, steps_astar = run_single_algo(AStarSolver, "A*", problem, timeout_seconds=timeout_seconds)

    print("\n" + "=" * 70)
    print("                    BẢNG SO SÁNH THỰC NGHIỆM")
    print("=" * 70)
    print(f"{'Tiêu chí':<25} | {'UCS (Uniform Cost)':<20} | {'A* (Heuristic)':<20}")
    print("-" * 70)
    print(f"{'Trạng thái':<25} | {'Thành công' if cost_ucs else 'Timeout/Thất bại':<20} | {'Thành công' if cost_astar else 'Timeout/Thất bại':<20}")
    print(f"{'Tổng chi phí (Cost)':<25} | {str(cost_ucs):<20} | {str(cost_astar):<20}")
    print(f"{'Thời gian thực thi':<25} | {f'{solver_ucs.execution_time:.4f}s':<20} | {f'{solver_astar.execution_time:.4f}s':<20}")
    print(f"{'Số node duyệt (Explored)':<25} | {f'{solver_ucs.nodes_explored:,}':<20} | {f'{solver_astar.nodes_explored:,}':<20}")
    print(f"{'Bộ nhớ Max Frontier':<25} | {f'{solver_ucs.max_frontier_size:,}':<20} | {f'{solver_astar.max_frontier_size:,}':<20}")
    print("=" * 70)

def main():
    print_banner()

    # Nhận đường dẫn map từ terminal nếu có: python main.py <map_path>
    map_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("maps", "map_single.txt")

    if not os.path.exists(map_path):
        print(f"[Lỗi] Không tìm thấy file bản đồ: {map_path}")
        return

    problem = SokobanProblem(map_path)
    print_map_info(problem, map_path)

    print("Chọn chế độ kiểm thử:")
    print("  1. Chạy thuật toán UCS")
    print("  2. Chạy thuật toán A* (với Heuristic né tường & Deadlock)")
    print("  3. So sánh trực tiếp cả 2 thuật toán (UCS vs A*)")
    
    choice = input("\nNhập lựa chọn của bạn (1/2/3, mặc định 3): ").strip()

    if choice == "1":
        run_single_algo(UCSSolver, "UCS", problem, timeout_seconds=15)
    elif choice == "2":
        run_single_algo(AStarSolver, "A*", problem, timeout_seconds=15)
    else:
        compare_algorithms(problem, timeout_seconds=15)

if __name__ == "__main__":
    main()
