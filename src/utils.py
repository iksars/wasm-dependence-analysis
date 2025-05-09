import re
from collections import defaultdict

# 读取日志文件路径
log_path = "log.log"

# 用于保存结果的嵌套字典：{tool: {program: total_time}}
tool_times = defaultdict(lambda: defaultdict(float))

# 正则表达式匹配每行信息
pattern = re.compile(r"(\w+)\s+analyse function \d+ in (\S+) took ([\d.]+) seconds")

with open(log_path, "r") as f:
    for line in f:
        match = pattern.search(line)
        if match:
            tool, program, time = match.groups()
            tool_times[tool][program] += float(time)

# 打印结果
for tool, programs in tool_times.items():
    t = 0
    print(f"Tool: {tool}")
    for program, total_time in programs.items():
        print(f"  Program: {program}, Total Time: {total_time:.2f} seconds")
        t += total_time
    print("total time:", t)