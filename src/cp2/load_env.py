import os
import questionary
from rich.console import Console
from dotenv import load_dotenv

console = Console()


def read_exclude_dirs():
    """
    读取排除目录列表，支持从多个环境变量中合并
    """
    # 加载 .env 文件
    load_dotenv()

    exclude_dirs = []

    # 从主要的 EXCLUDE_DIRS 变量读取
    main_dirs = os.environ.get("EXCLUDE_DIRS", "")
    if main_dirs:
        exclude_dirs.extend([d.strip() for d in main_dirs.split(",") if d.strip()])

    # 从分类的环境变量中读取（可选）
    category_vars = ["EXCLUDE_DIRS_DEPS", "EXCLUDE_DIRS_VCS", "EXCLUDE_DIRS_BUILD"]
    for var in category_vars:
        dirs = os.environ.get(var, "")
        if dirs:
            exclude_dirs.extend([d.strip() for d in dirs.split(",") if d.strip()])

    # 去重并返回
    return list(set(exclude_dirs))


def read_projects():
    # 加载 .env 文件
    load_dotenv()

    # 获取 PJ_ 开头的变量名
    return {
        key[3:]: value for key, value in os.environ.items() if key.startswith("PJ_")
    }


def ask_to_pick_project():
    projects = read_projects()
    if not projects:
        console.print("No projects found.")
        return None

    # 排除当前目录
    current_dir = os.getcwd()
    projects = {name: path for name, path in projects.items() if path != current_dir}

    project_choices = list(projects.keys())
    choice = questionary.checkbox("Select projects:", choices=project_choices).ask()
    if choice:
        return choice
    else:
        console.print("[red]Invalid choice! Exiting...[/red]")
        raise SystemExit()


if __name__ == "__main__":
    ask_to_pick_project()
