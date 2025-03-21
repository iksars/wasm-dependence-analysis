

def recrusivePrint(path, indent=0):
    for item in path.iterdir():
        if item.is_file():
            print("  " * indent, end="")
            print("文件:", item)
        elif item.is_dir():
            print("  " * indent, end="")
            print("目录:", item)
            recrusivePrint(item, indent + 1)