import time
import os
import sys

# Đảm bảo in tiếng Việt không bị lỗi charmap trên terminal Windows
if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from competitive_core import CompetitiveGame
import agent_team
import agent_opponent

def run_match(map_path: str = "maps/battle_map.txt", max_steps: int = 30, delay: float = 0.2):
    print("=" * 65)
    print("      TRẬN ĐẤU ĐỐI KHÁNG 2 AGENT - SOKOBAN BATTLE (YÊU CẦU 6, 7)")
    print("=" * 65)
    print(f"[+] Bản đồ thi đấu: {map_path}")
    print(f"[+] Giới hạn số bước (n): {max_steps} bước")
    print(f"[+] Agent 1: agent_team.py (Nhóm mình)")
    print(f"[+] Agent 2: agent_opponent.py (Đối thủ)")
    print("-" * 65)

    game = CompetitiveGame(map_path, max_steps=max_steps)
    game.print_board()

    for step in range(1, max_steps + 1):
        state = game.get_state()

        # Agent 1 ra quyết định
        t0 = time.perf_counter()
        act1 = agent_team.get_action(state, 1, time_limit_ms=1000)
        time1 = (time.perf_counter() - t0) * 1000

        # Agent 2 ra quyết định
        t0 = time.perf_counter()
        act2 = agent_opponent.get_action(state, 2, time_limit_ms=1000)
        time2 = (time.perf_counter() - t0) * 1000

        # Kiểm tra vi phạm giới hạn thời gian (<= 1000ms)
        if time1 > 1000:
            print(f"[CẢNH BÁO] Agent 1 vi phạm timeout ({time1:.1f}ms > 1000ms)!")
        if time2 > 1000:
            print(f"[CẢNH BÁO] Agent 2 vi phạm timeout ({time2:.1f}ms > 1000ms)!")

        # Môi trường thực hiện đồng thời 2 hành động
        next_s, scores, is_over = game.step(act1, act2)

        print(f"\n>>> Lượt {step}/{max_steps}: Agent 1 ({act1}, {time1:.1f}ms) | Agent 2 ({act2}, {time2:.1f}ms)")
        game.print_board()

        if delay > 0:
            time.sleep(delay)

        if is_over:
            break

    winner = game.get_winner()
    print("\n" + "=" * 65)
    print("                       KẾT THÚC TRẬN ĐẤU")
    print("=" * 65)
    print(f" Tỉ số chung cuộc: Agent 1 = {game.state.scores[1]} | Agent 2 = {game.state.scores[2]}")
    if winner:
        print(f" 🏆 NGƯỜI CHIẾN THẮNG: AGENT {winner}!")
    else:
        print(" 🤝 KẾT QUẢ: HÒA CỜ (DRAW)!")
    print("=" * 65)

if __name__ == "__main__":
    steps = 20
    if len(sys.argv) > 1:
        try:
            steps = int(sys.argv[1])
        except ValueError:
            pass
    run_match(max_steps=steps, delay=0.05)
