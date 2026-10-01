import sys
import time
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agents import build_city_agent

agent = build_city_agent(enable_human_approval=False)

test_questions = [
    ("🌦️ WEATHER", "What is the current weather in Mumbai?"),
    ("📅 FORECAST", "What is the 3-day weather forecast for Paris?"),
    ("📰 NEWS", "What is the latest news in San Francisco?"),
    ("🏛️ PLACES", "What are the top 3 tourist places to visit in Rome?"),
    ("📚 WIKIPEDIA", "Give me a brief summary of Alan Turing from Wikipedia."),
    ("🧮 MATH", "Calculate sqrt(256) * 15 + 40"),
    ("🕒 TIME", "What is the current UTC date and time?")
]

print("===============================================================")
print("🚀 RUNNING FULL TOOL VERIFICATION SUITE")
print("===============================================================\n")

total_start = time.time()
passed = 0

for category, q in test_questions:
    print(f"[{category}] Question: \"{q}\"")
    t0 = time.time()
    try:
        res = agent.invoke({"messages": [{"role": "user", "content": q}]})
        elapsed = time.time() - t0
        raw_reply = res["messages"][-1].content
        if isinstance(raw_reply, list):
            reply = "".join(c.get("text", "") if isinstance(c, dict) else str(c) for c in raw_reply)
        else:
            reply = str(raw_reply)
        
        preview = reply.strip().replace("\n", " ")[:160]
        print(f"   ✔ [{elapsed:.2f}s] Response: {preview}...\n")
        passed += 1
    except Exception as e:
        print(f"   ✖ Failed: {e}\n")

total_time = time.time() - total_start
print("===============================================================")
print(f"🏁 RESULT: {passed}/{len(test_questions)} TESTS PASSED in {total_time:.2f}s")
print("===============================================================")
