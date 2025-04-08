import json
import os

def recrusivePrint(path, indent=0):
    for item in path.iterdir():
        if item.is_file():
            print("  " * indent, end="")
            print("文件:", item)
        elif item.is_dir():
            print("  " * indent, end="")
            print("目录:", item)
            recrusivePrint(item, indent + 1)

def dump(path, output):
    json_to_latex(path, output)
    # 执行shell脚本
    os.system("bash ./latexify.sh")
    print("\nreport generated at {}".format(output))
    


# def latexify(path): 
#     """
#     生成 LaTeX 表格
#     path: data.json 文件路径
#     """
#     with open(path, "r") as f:
#         data = json.load(f)
#     for tool in data["tools"]:
#         print(f"\\multirow{{2}}{{*}}{{{tool}}}", end=" ")
#         for case in data["cases"]:
#             print(f"& {case['case']}", end=" ")
#         print("\\\\")
#         print("\\cline{2-6}")
#         print("&", end=" ")
#         for case in data["cases"]:
#             print(f"& {case['average'][data['tools'].index(tool)]}", end=" ")
#         print("\\\\")


def json_to_latex(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tools = data["tools"]
    cases = data["cases"]
    
    latex_output = [
        "\\documentclass{article}", "\\usepackage{booktabs}", "\\begin{document}",
        "\\title{Graph Similarity Analysis}", "\\author{}", "\\date{}", "\\maketitle"
    ]
    
    for case in cases:
        latex_output.append(f"\\section{{Case: \\texttt{{\\detokenize{{{case['case']}}}}} }}")
        
        for func in case["functions"]:
            func_index = func["index"]
            matrix = func["matrix"]
            latex_output.append(f"\\subsection{{Function {func_index}}}")
            latex_output.append(matrix_to_latex(matrix, tools, f"Frobenius Norm for Function {func_index} in \\texttt{{\\detokenize{{{case['case']}}}}}"))
        
        # 添加平均相似度矩阵
        latex_output.append("\\subsection{Average}")
        latex_output.append(matrix_to_latex(case["average"], tools, f"Average Frobenius Norm for \\texttt{{\\detokenize{{{case['case']}}}}}"))
    
    latex_output.append("\\end{document}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_output))

def matrix_to_latex(matrix, tools, caption):
    """ 将矩阵转换为 LaTeX 表格格式 """
    table = ["\\begin{table}[h]", "    \\centering", "    \\begin{tabular}{l" + "c" * len(tools) + "}", "        \\toprule"]
    table.append("        & " + " & ".join(tools) + " \\\\")
    table.append("        \\midrule")
    
    for tool, row in zip(tools, matrix):
        row_str = " & ".join(f"{val:.4f}" for val in row)
        table.append(f"        {tool}  & {row_str} \\\\")
    
    table.append("        \\bottomrule")
    table.append("    \\end{tabular}")
    table.append(f"    \\caption{{{caption}}}")
    table.append("\\end{table}")
    
    return '\n'.join(table)