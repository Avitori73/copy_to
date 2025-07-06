from typing import Dict, List, Tuple


def is_subsequence(query: str, text: str) -> bool:
    """
    检查query是否是text的子序列（保持字符顺序）
    """
    if not query:
        return True
    if not text:
        return False

    i = j = 0
    query_lower = query.lower()
    text_lower = text.lower()

    while i < len(query_lower) and j < len(text_lower):
        if query_lower[i] == text_lower[j]:
            i += 1
        j += 1

    return i == len(query_lower)


def calculate_subsequence_score(query: str, text: str) -> int:
    """
    计算子序列匹配的得分
    """
    if not is_subsequence(query, text):
        return 0

    query_lower = query.lower()
    text_lower = text.lower()

    # 基础得分
    base_score = 60

    # 计算字符间距离得分
    positions = []
    j = 0
    for i, char in enumerate(query_lower):
        while j < len(text_lower) and text_lower[j] != char:
            j += 1
        if j < len(text_lower):
            positions.append(j)
            j += 1

    if len(positions) == len(query_lower):
        # 计算平均间距
        if len(positions) > 1:
            total_distance = positions[-1] - positions[0]
            ideal_distance = len(query_lower) - 1
            if total_distance > 0:
                distance_ratio = ideal_distance / total_distance
                distance_score = min(30, int(distance_ratio * 30))
            else:
                distance_score = 30
        else:
            distance_score = 30

        return base_score + distance_score

    return 0


def fuzzy_search_files(
    query: str, file_cache: Dict[str, str], max_results: int = 20
) -> List[Tuple[str, str, int]]:
    """
    在文件缓存中进行模糊搜索
    返回格式: [(filename, filepath, score), ...]
    """
    if not query:
        return []

    query_lower = query.lower()
    results = []

    for filename, filepath in file_cache.items():
        filename_lower = filename.lower()
        score = 0

        # 精确匹配得分最高
        if query_lower == filename_lower:
            score = 100
        # 开头匹配
        elif filename_lower.startswith(query_lower):
            score = 90
        # 包含匹配
        elif query_lower in filename_lower:
            score = 80
        # 子序列匹配（保持字符顺序）
        else:
            score = calculate_subsequence_score(query, filename)

        if score > 0:
            results.append((filename, filepath, score))

    # 按得分排序并限制结果数量
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:max_results]
