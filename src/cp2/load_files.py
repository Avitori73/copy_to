import os
from typing import Dict, List
from .cp2_config import CP2Config
from gitignore_parser import parse_gitignore


def init_gitignore_parser(root_dir: str, ignore_patterns: List[str]):
    """
    Initialize the gitignore parser.
    This function is a placeholder for any setup needed for gitignore parsing.
    """
    # Create a temporary file with the patterns in the root directory
    tmp_file_path = os.path.join(root_dir, ".gitignore.copy2.temp")
    with open(tmp_file_path, "w") as tmp_file:
        for pattern in ignore_patterns:
            tmp_file.write(pattern + "\n")

    matches = parse_gitignore(tmp_file_path)

    # Clean up the temporary file
    os.unlink(tmp_file_path)

    return matches


def filter_with_gitignore_parser(
    root_dir: str, ignore_patterns: List[str]
) -> List[str]:
    """
    Filter files and directories in the given root directory
    based on the provided gitignore patterns.
    """
    matches = init_gitignore_parser(root_dir, ignore_patterns)

    filtered_files = []
    for root, dirs, files in os.walk(root_dir):
        # 过滤目录
        dirs[:] = [d for d in dirs if not matches(os.path.join(root, d))]

        # 过滤文件
        for file in files:
            file_path = os.path.join(root, file)
            if not matches(file_path):
                filtered_files.append(file_path)

    return filtered_files


def search_files_with_gitignore(
    root_dir: str, search_term: str, ignore_patterns: List[str]
) -> List[str]:
    """
    Search for files in the given root directory that match the search term,
    while respecting the provided gitignore patterns.
    """
    matches = init_gitignore_parser(root_dir, ignore_patterns)
    results = []
    for root, dirs, files in os.walk(root_dir):
        # 过滤目录
        dirs[:] = [d for d in dirs if not matches(os.path.join(root, d))]

        # 搜索文件
        for file in files:
            file_path = os.path.join(root, file)
            if search_term.lower() in file.lower() and not matches(file_path):
                results.append(file_path)

    return results


def search_directory_with_gitignore(
    root_dir: str, search_term: str, ignore_patterns: List[str]
) -> List[str]:
    """
    Search for directories in the given root directory that match the search term,
    while respecting the provided gitignore patterns.
    """
    matches = init_gitignore_parser(root_dir, ignore_patterns)
    results = []
    for root, dirs, files in os.walk(root_dir):
        # 过滤目录
        dirs[:] = [d for d in dirs if not matches(os.path.join(root, d))]

        # 搜索目录
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if search_term.lower() in dir_name.lower() and not matches(dir_path):
                results.append(dir_path)

    return results


def read_ignore_file(ignore_file: str) -> List[str]:
    """
    Read ignore patterns from a file.
    """
    if not os.path.exists(ignore_file):
        return []

    with open(ignore_file, "r", encoding="utf-8") as f:
        patterns = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    return patterns


def load_files_to_cache(
    cp2_config: CP2Config, target_dir: str = os.getcwd()
) -> Dict[str, str]:
    """
    Load files from the current directory into a cache.
    """
    cache: Dict[str, str] = {}

    ignore_patterns = read_ignore_file(cp2_config.get_ignore_file())
    exclude_patterns = cp2_config.get_exclude_patterns()
    ignore_patterns.extend(exclude_patterns)

    filtered_files = filter_with_gitignore_parser(target_dir, ignore_patterns)

    for file_path in filtered_files:
        cache[os.path.basename(file_path)] = file_path

    return cache


def main():
    cp2_config = CP2Config()
    cache = load_files_to_cache(cp2_config)
    print(f"Loaded {len(cache)} files into cache.")


if __name__ == "__main__":
    main()
