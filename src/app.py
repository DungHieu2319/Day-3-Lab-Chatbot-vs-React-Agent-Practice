"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer — Trần Tiến Dũng)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

ĐỀ TÀI: Trợ Lý Nắm Bắt Tính Cách & Chọn Quà Tặng Phù Hợp
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    GUARDRAIL_MESSAGE,
)
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════
# 🤖 CHATBOT BASELINE (Cấp 2 — Chỉ dùng LLM, không có Tool)
# ═══════════════════════════════════════════════════════════════

def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Chỉ gọi 1 lần LLM để so sánh với ReAct Agent.
    """
    print(f"\n{'='*60}")
    print(f"💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"{'='*60}")

    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# ═══════════════════════════════════════════════════════════════
# 🧠 REACT AGENT LOOP (Cấp 3 — Vòng lặp Thought → Action → Observation)
# ═══════════════════════════════════════════════════════════════

def parse_action(llm_response: str):
    """
    Parse phản hồi LLM để tìm Action và tham số.

    Hỗ trợ các format:
    - Action: tool_name[param1, param2]
    - Action: tool_name['param1', 'param2']
    - Action: tool_name["param1"]

    Returns:
        tuple: (tool_name, [args]) hoặc (None, None) nếu không tìm thấy Action
    """
    # Tìm dòng Action
    action_match = re.search(r"Action:\s*(\w+)\[(.+?)\]", llm_response)
    if not action_match:
        return None, None

    tool_name = action_match.group(1).strip()
    args_raw = action_match.group(2).strip()

    # Parse tham số — loại bỏ quotes và split by comma
    args = []
    for arg in re.split(r",\s*", args_raw):
        arg = arg.strip().strip("'\"")
        # Thử chuyển thành số nếu có thể
        try:
            arg = int(arg)
        except ValueError:
            pass
        args.append(arg)

    return tool_name, args


def execute_tool(tool_name: str, args: list) -> str:
    """
    Thực thi một tool từ AVAILABLE_TOOLS registry.
    Tự động xử lý trường hợp LLM truyền nhiều args nhưng tool chỉ nhận 1 string.

    Returns:
        str: Kết quả từ tool hoặc thông báo lỗi
    """
    if tool_name not in AVAILABLE_TOOLS:
        available = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ: [{available}]"

    tool_func = AVAILABLE_TOOLS[tool_name]

    try:
        result = tool_func(*args)
        return result
    except TypeError as e:
        # Fallback: Nếu tool nhận 1 param nhưng LLM truyền nhiều args,
        # thử nối lại thành 1 string
        if "positional argument" in str(e) and len(args) > 1:
            try:
                combined = ", ".join(str(a) for a in args)
                result = tool_func(combined)
                return result
            except Exception as e2:
                return f"LỖI: Sai tham số khi gọi {tool_name}: {str(e2)}"
        return f"LỖI: Sai tham số khi gọi {tool_name}: {str(e)}"
    except Exception as e:
        return f"LỖI: Lỗi khi thực thi {tool_name}: {str(e)}"


def check_final_answer(llm_response: str) -> str:
    """
    Kiểm tra xem phản hồi LLM có chứa Final Answer không.

    Returns:
        str: Nội dung Final Answer hoặc None
    """
    match = re.search(r"Final Answer:\s*(.+)", llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.

    Flow:
    1. Gửi system prompt + user query + conversation history cho LLM
    2. Parse response tìm Action hoặc Final Answer
    3. Nếu Action → execute tool → append Observation → lặp lại
    4. Nếu Final Answer → return
    5. Nếu đạt MAX_ITERATIONS → Guardrail fallback
    """
    print(f"\n{'='*60}")
    print(f"🧠 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"{'='*60}")

    # Conversation history để accumulate Thought-Action-Observation
    conversation = f"Question: {user_query}\n"
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        # Gọi LLM với toàn bộ conversation history
        full_prompt = conversation
        llm_response = provider.generate(full_prompt, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"📝 LLM Response:\n{llm_response}")

        # Kiểm tra Final Answer trước
        final_answer = check_final_answer(llm_response)
        if final_answer:
            print(f"\n🏁 FINAL ANSWER: {final_answer}")
            return final_answer

        # Parse Action
        tool_name, args = parse_action(llm_response)

        if tool_name:
            print(f"🛠️ Action: {tool_name}{args}")

            # Execute tool
            observation = execute_tool(tool_name, args)
            print(f"👁️ Observation: {observation}")

            # Append vào conversation history cho bước tiếp theo
            conversation += f"{llm_response}\nObservation: {observation}\n"
        else:
            # LLM không sinh ra Action cũng không có Final Answer
            print("⚠️ LLM không sinh Action hợp lệ. Thêm hướng dẫn và thử lại...")
            conversation += (
                f"{llm_response}\n"
                "Observation: Hệ thống không nhận diện được Action hợp lệ. "
                "Vui lòng dùng đúng format: Action: tên_tool[tham_số] "
                "hoặc Final Answer: câu trả lời.\n"
            )

    # Guardrail triggered
    print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước.")
    print(f"📢 {GUARDRAIL_MESSAGE}")
    return GUARDRAIL_MESSAGE


# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN — Chạy so sánh Chatbot vs Agent trên toàn bộ Test Cases
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Đề tài: Trợ Lý Nắm Bắt Tính Cách & Chọn Quà Tặng Phù Hợp")
    print("=" * 60)

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    # Cho phép chọn chạy 1 case hoặc tất cả
    print("Bạn muốn chạy test case nào?")
    for t in tests:
        print(f"  [{t['id']}] {t['category']}: {t['question'][:50]}...")
    print(f"  [0] Chạy tất cả {len(tests)} test cases")

    try:
        choice = input("\n👉 Nhập số (0-5): ").strip()
        choice = int(choice)
    except (ValueError, EOFError):
        choice = 3  # Default: chạy test case #3

    if choice == 0:
        selected_tests = tests
    elif 1 <= choice <= len(tests):
        selected_tests = [tests[choice - 1]]
    else:
        print(f"⚠️ Lựa chọn không hợp lệ. Chạy mặc định test case #3.")
        selected_tests = [tests[2]]

    for test in selected_tests:
        query = test["question"]
        print(f"\n{'#'*60}")
        print(f"📝 TEST CASE #{test['id']}: {test['category']}")
        print(f"❓ Câu hỏi: {query}")
        print(f"🎯 Kỳ vọng: {test['expected_behavior']}")
        print(f"{'#'*60}")

        print("\n--- 🅰️ DEMO: CHATBOT BASELINE ---")
        baseline_response = run_baseline_chatbot(query, provider)

        print("\n--- 🅱️ DEMO: REACT AGENT ---")
        agent_response = run_react_agent(query, provider)

        print(f"\n{'─'*60}")
        print("📊 SO SÁNH NHANH:")
        print(f"  🤖 Chatbot: {str(baseline_response)[:100]}...")
        print(f"  🧠 Agent:   {str(agent_response)[:100]}...")
        print(f"{'─'*60}")
