# CP2 配置文档

## 配置文件结构

CP2 使用 TOML 格式的配置文件，支持类型验证和自动纠正。配置文件的主要结构如下：

### 1. 排除配置 (`exclude`)

用于定义在复制文件时要排除的文件和目录模式。

```toml
[exclude]
patterns = [
    "*.pyc",           # Python 字节码文件
    "__pycache__/",    # Python 缓存目录
    ".git/",           # Git 仓库目录
    ".vscode/",        # VS Code 配置目录
    ".idea/",          # JetBrains IDE 配置目录
    ".DS_Store",       # macOS 系统文件
    "node_modules/",   # Node.js 依赖目录
    "dist/",           # 构建输出目录
    "build/",          # 构建目录
    ".env",            # 环境变量文件
    ".venv/",          # Python 虚拟环境目录
    "venv/",           # Python 虚拟环境目录
    "env/"             # Python 虚拟环境目录
]
ignore_file = ".gitignore"  # 忽略文件名
```

**字段说明：**

- `patterns`: 字符串列表，包含要排除的文件和目录模式
- `ignore_file`: 字符串，指定忽略文件的名称（如 `.gitignore`）

### 2. 项目配置 (`project`)

项目配置是一个字典结构，其中：

- **键**: 项目名称（字符串）
- **值**: 项目信息对象，包含 `path` 和可选的 `description` 字段

```toml
[project.web_app]
path = "/path/to/web/application"
description = "我的 Web 应用项目"

[project.api_server]
path = "/path/to/api/server"
description = "后端 API 服务器"

[project.mobile_app]
path = "/path/to/mobile/app"
description = "移动应用项目"
```

**字段说明：**

- `path`: 字符串，项目的绝对路径（必需）
- `description`: 字符串，项目描述（可选）

## 配置验证

配置文件支持以下验证规则：

### 排除配置验证

- `patterns` 必须是字符串列表
- `ignore_file` 必须是非空字符串

### 项目配置验证

- 项目名称必须是有效的字符串
- `path` 必须是非空字符串
- `description` 可以为空或字符串

## 使用方式

### 1. 通过代码使用

```python
from cp2.cp2_config import CP2Config

# 初始化配置
config = CP2Config()

# 添加项目
config.add_project("my_project", "/path/to/project", "项目描述")

# 获取项目信息
project_info = config.get_project("my_project")
print(project_info)  # {'path': '/path/to/project', 'description': '项目描述'}

# 列出所有项目
projects = config.list_projects()
for name, info in projects.items():
    print(f"{name}: {info['path']}")

# 移除项目
config.remove_project("my_project")

# 检查项目是否存在
exists = config.project_exists("my_project")
```

### 2. 配置文件操作

```python
# 获取配置值
patterns = config.get("exclude.patterns")
ignore_file = config.get("exclude.ignore_file")

# 设置配置值
config.set("exclude.ignore_file", ".cp2ignore")

# 添加排除模式
current_patterns = config.get("exclude.patterns", [])
current_patterns.append("*.backup")
config.set("exclude.patterns", current_patterns)

# 保存配置
config.save()

# 重新加载配置
config.reload()

# 重置为默认配置
config.reset()
```

## 配置文件位置

配置文件自动保存在用户配置目录中：

- **Windows**: `%LOCALAPPDATA%\copy_to\copy_to\config.toml`
- **macOS**: `~/Library/Application Support/copy_to/config.toml`
- **Linux**: `~/.config/copy_to/config.toml`

可以通过以下方式获取配置文件路径：

```python
config = CP2Config()
config_path = config.get_config_path()
print(f"配置文件位置: {config_path}")
```

## 错误处理

配置系统包含自动错误处理机制：

1. **格式错误**: 如果配置文件格式错误，会自动使用默认配置重新创建文件
2. **类型错误**: 如果配置值类型不正确，会提供详细的错误信息
3. **验证失败**: 如果配置验证失败，会自动回退到默认配置

```python
# 验证配置
is_valid = config.validate_config()
print(f"配置有效: {is_valid}")

# 获取验证错误
errors = config.get_validation_errors()
if errors:
    print(f"验证错误: {errors}")
```

## 示例配置文件

参见 `examples/config_example.toml` 获取完整的配置示例。
