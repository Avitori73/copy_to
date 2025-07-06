import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Set

from .fuzzy_search import fuzzy_search_files
from .cp2_config import CP2Config


def read_ignore_pattern(
    start_path=None, ignore_file=".gitignore", default_patterns: List[str] = []
) -> Set[str]:
    """
    read ignore patterns from ignore file (default is .gitignore)
    """
    if start_path is None:
        start_path = os.getcwd()

    ignore_patterns: Set[str] = set()

    ignore_file_path = os.path.join(start_path, ignore_file)

    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith("#"):
                    ignore_patterns.add(line)

    # 一些大型目录默认排除
    if default_patterns:
        set_default_patterns = set(default_patterns)
        ignore_patterns.update(set_default_patterns)

    return ignore_patterns


def should_ignore(path, ignore_patterns) -> bool:
    """
    Check if a path should be ignored based on patterns.
    """
    path = Path(path)

    for pattern in ignore_patterns:
        # 处理目录模式（以 / 结尾）
        if pattern.endswith("/"):
            pattern = pattern[:-1]
            # 检查路径中的任何部分是否匹配
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        else:
            # 文件模式匹配
            if fnmatch.fnmatch(path.name, pattern):
                return True
            # 也检查完整路径匹配
            if fnmatch.fnmatch(str(path), pattern):
                return True
            # 检查路径的任何部分
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

    return False


def load_files_to_cache(cp2_config: CP2Config) -> Dict[str, str]:
    """
    Load files from the current directory into a cache.
    """
    cache = {}
    current_dir = os.getcwd()

    ignore_patterns = read_ignore_pattern(
        current_dir, cp2_config.get_ignore_file(), cp2_config.get_exclude_patterns()
    )

    for root, dirs, files in os.walk(current_dir):
        # 检查当前目录是否应该被忽略
        rel_root = os.path.relpath(root, current_dir)
        if rel_root != "." and should_ignore(rel_root, ignore_patterns):
            dirs.clear()  # 不继续遍历子目录
            continue

        # 过滤应该忽略的子目录
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore(
                os.path.join(rel_root, d) if rel_root != "." else d, ignore_patterns
            )
        ]

        # 处理文件
        for file in files:
            file_path = os.path.join(root, file)
            rel_file_path = os.path.relpath(file_path, current_dir)

            # 检查文件是否应该被忽略
            if not should_ignore(rel_file_path, ignore_patterns):
                cache[file] = rel_file_path

    return cache


def main():
    cp2_config = CP2Config()
    cache = load_files_to_cache(cp2_config)
    print(f"Loaded {len(cache)} files into cache.")

    query = input("Enter a wildcard pattern to search (e.g., *.py): ")

    results = fuzzy_search_files(query, cache)
    print("\nFuzzy search results:")
    for filename, filepath, score in results[:10]:
        print(f"  {filename} (Path: '.\\{filepath}', Score: {score})")


if __name__ == "__main__":
    main()
