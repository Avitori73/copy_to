# sql_format

## 要求

- Python 3.11+

## 安装

```bash
# 克隆仓库
git clone https://github.com/Avitori73/copy_to.git

# 进入项目目录
cd copy_to

# 安装指令
pip install -e .
```

## 简洁

常用复制的目录需要标记为 mark，在后续复制的时候可以快速选择想要复制的目录。
复制文件会基于当前文件的目录结构，在目标目录中创建相同的文件路径。

## 使用

### 1. 添加 Mark

```bash
cp2 mark add <PATH> <MARK_NAME>

例如：将当前目录标记为 SD
cp2 mark add . SD
```

### 2. 复制文件

```bash
cp2 start
```

该命令会根据 `.gitignore` 过滤当前目录的所有文件，输入三个字符以上可以模糊查询文件，然后选中文件。

## FZF 使用

由于 python 的目录遍历不够块，在获取文件列表时会有明显的卡顿感，这是需要配合一些工具来提升体验。
使用 scoop 安装 fd 和 fzf，安装后可以使用下面的命令来替代 `cp2 start`。

```bash
cp2 fzf
```
