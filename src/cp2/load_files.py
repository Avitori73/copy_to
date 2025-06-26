import os
import fnmatch
from pathlib import Path


def read_cp2ignore(start_path=None):
    """
    Read .cp2ignore file and return list of patterns to ignore.
    Similar to .gitignore syntax.
    """
    if start_path is None:
        start_path = os.getcwd()

    ignore_patterns = []
    cp2ignore_path = os.path.join(start_path, ".cp2ignore")

    if os.path.exists(cp2ignore_path):
        with open(cp2ignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith("#"):
                    ignore_patterns.append(line)

    return ignore_patterns


def should_ignore(path, ignore_patterns):
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


def load_files_to_cache():
    """
    Load files from the current directory into a cache.
    Uses .cp2ignore file for exclusion patterns.
    """
    cache = {}
    current_dir = os.getcwd()
    ignore_patterns = read_cp2ignore(current_dir)

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
                cache[file] = file_path

    return cache


def load_files_to_cache_with_stats():
    """
    Load files from the current directory into a cache with statistics.
    """
    cache = {}
    current_dir = os.getcwd()
    ignore_patterns = read_cp2ignore(current_dir)

    total_files = 0
    ignored_files = 0
    ignored_dirs = set()

    for root, dirs, files in os.walk(current_dir):
        # 检查当前目录是否应该被忽略
        rel_root = os.path.relpath(root, current_dir)
        if rel_root != "." and should_ignore(rel_root, ignore_patterns):
            ignored_dirs.add(rel_root)
            dirs.clear()  # 不继续遍历子目录
            continue

        # 过滤应该忽略的子目录
        original_dirs = dirs[:]
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore(
                os.path.join(rel_root, d) if rel_root != "." else d, ignore_patterns
            )
        ]

        # 记录被忽略的目录
        for d in original_dirs:
            if d not in dirs:
                dir_path = os.path.join(rel_root, d) if rel_root != "." else d
                ignored_dirs.add(dir_path)

        # 处理文件
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            rel_file_path = os.path.relpath(file_path, current_dir)

            # 检查文件是否应该被忽略
            if should_ignore(rel_file_path, ignore_patterns):
                ignored_files += 1
            else:
                cache[file] = file_path

    return cache, {
        "total_files": total_files,
        "ignored_files": ignored_files,
        "included_files": len(cache),
        "ignored_dirs": sorted(ignored_dirs),
        "ignore_patterns": ignore_patterns,
    }


if __name__ == "__main__":
    cache = load_files_to_cache()
    print(f"Loaded {len(cache)} files into cache.")
    for file, path in cache.items():
        print(f"{file}: {path}")
