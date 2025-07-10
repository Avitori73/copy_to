from pathlib import Path
from typing import Any, Dict, Optional, List
import toml
from platformdirs import user_config_dir
from pydantic import BaseModel, Field, ValidationError, field_validator
from rich.console import Console

# 创建一个控制台实例，用于输出
console = Console()


# 定义配置模型
class ExcludeConfig(BaseModel):
    """排除配置模型"""

    patterns: List[str] = Field(
        default_factory=lambda: [
            "*.pyc",
            "__pycache__/",
            ".git/",
            ".vscode/",
            ".idea/",
            ".DS_Store",
            "node_modules/",
            "dist/",
            "build/",
            ".env",
            ".venv/",
            "venv/",
            "env/",
        ],
        description="排除的文件模式列表",
    )
    ignore_file: str = Field(default=".gitignore", description="忽略文件名")

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v):
        """验证模式列表并去重"""
        if not isinstance(v, list):
            raise ValueError("patterns 必须是一个列表")
        if not all(isinstance(pattern, str) for pattern in v):
            raise ValueError("patterns 中的所有项目都必须是字符串")
        # 去重并保持顺序
        seen = set()
        unique_patterns = []
        for pattern in v:
            if pattern not in seen:
                seen.add(pattern)
                unique_patterns.append(pattern)
        return unique_patterns

    @field_validator("ignore_file")
    @classmethod
    def validate_ignore_file(cls, v):
        """验证忽略文件名"""
        if not isinstance(v, str):
            raise ValueError("ignore_file 必须是字符串")
        if not v.strip():
            raise ValueError("ignore_file 不能为空")
        return v.strip()


class MarkInfo(BaseModel):
    """单个项目的信息模型"""

    path: str = Field(description="项目路径")
    description: Optional[str] = Field(default=None, description="项目描述")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v):
        """验证项目路径"""
        if not isinstance(v, str):
            raise ValueError("path 必须是字符串")
        if not v.strip():
            raise ValueError("path 不能为空")
        return v.strip()


class MarkConfig(BaseModel):
    """项目配置模型 - 使用字典存储项目信息"""

    marks: Dict[str, MarkInfo] = Field(default_factory=dict, description="项目配置字典")

    def add_mark(self, name: str, path: str, description: Optional[str] = None):
        """添加项目"""
        mark_info = MarkInfo(path=path, description=description)
        self.marks[name] = mark_info

    def remove_mark(self, name: str):
        """移除项目"""
        if name in self.marks:
            del self.marks[name]

    def get_mark(self, name: str) -> Optional[MarkInfo]:
        """获取项目信息"""
        return self.marks.get(name)

    def list_marks(self) -> Dict[str, MarkInfo]:
        """列出所有项目"""
        return self.marks.copy()

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """自定义序列化方法 - 直接返回项目字典而不是嵌套的 marks 键"""
        result = {}
        for name, mark_info in self.marks.items():
            result[name] = mark_info.model_dump(**kwargs)
        return result


class CP2ConfigModel(BaseModel):
    """主配置模型"""

    exclude: ExcludeConfig = Field(default_factory=ExcludeConfig)
    mark: MarkConfig = Field(default_factory=MarkConfig)

    model_config = {
        "extra": "allow",  # 允许额外字段
        "validate_assignment": True,  # 赋值时验证
    }


class CP2Config:
    def __init__(self, config_filename: str = "config.toml"):
        """
        初始化配置管理器

        :param config_filename: 配置文件名，默认为 config.toml
        """
        # 获取跨平台配置目录
        self.config_dir = Path(user_config_dir("copy_to"))
        self.config_file = self.config_dir / config_filename

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self._config_model = self._load_config()

    def _load_config(self) -> CP2ConfigModel:
        """加载配置文件，返回验证后的配置模型"""
        try:
            if self.config_file.exists():
                # 如果配置文件存在，读取并解析
                with open(self.config_file, "r", encoding="utf-8") as f:
                    raw_config = toml.load(f)

                # 使用 Pydantic 验证配置
                try:
                    # 处理项目配置的特殊结构
                    config_model = CP2ConfigModel()

                    # 设置排除配置
                    if "exclude" in raw_config:
                        config_model.exclude = ExcludeConfig(**raw_config["exclude"])

                    # 设置项目配置
                    if "mark" in raw_config and isinstance(raw_config["mark"], dict):
                        mark_config = MarkConfig()
                        for mark_name, mark_data in raw_config["mark"].items():
                            if isinstance(mark_data, dict) and "path" in mark_data:
                                mark_config.add_mark(
                                    name=mark_name,
                                    path=mark_data["path"],
                                    description=mark_data.get("description"),
                                )
                        config_model.mark = mark_config

                    # 保存验证后的配置回文件（修正任何格式问题）
                    self._save_config(config_model)
                    return config_model
                except ValidationError:
                    console.print("[red]配置文件验证失败[/red]")
                    console.print("[yellow]使用默认配置并重新创建配置文件[/yellow]")
                    config_model = CP2ConfigModel()
                    self._save_config(config_model)
                    return config_model
            else:
                # 如果配置文件不存在，使用默认配置并创建文件
                config_model = CP2ConfigModel()
                self._save_config(config_model)
                return config_model
        except toml.TomlDecodeError:
            console.print("[red]配置文件格式错误[/red]")
            raise SystemExit()
        except Exception:
            console.print("[red]加载配置文件失败[/red]")
            raise SystemExit()

    def _save_config(self, config_model: Optional[CP2ConfigModel] = None):
        """保存配置到文件"""
        try:
            if config_model is None:
                config_model = self._config_model

            # 将 Pydantic 模型转换为字典
            config_dict = {
                "exclude": config_model.exclude.model_dump(),
                "mark": config_model.mark.model_dump(),
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(config_dict, f)
        except Exception:
            console.print("[red]保存配置文件失败[/red]")
            raise SystemExit()

    @property
    def _config(self) -> Dict[str, Any]:
        """获取配置字典（向后兼容）"""
        return {
            "exclude": self._config_model.exclude.model_dump(),
            "mark": self._config_model.mark.model_dump(),
        }

    def has_mark(self, name: str) -> bool:
        """
        检查项目是否存在

        :param name: 项目名称
        :return: 如果项目存在返回 True，否则返回 False
        """
        return name in self._config_model.mark.marks

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取配置值，支持点分隔符 (如 'exclude.patterns')

        :param key: 配置键，可以使用点表示法访问嵌套值
        :param default: 如果键不存在时返回的默认值
        :return: 配置值或默认值
        """
        keys = key.split(".")
        value = self._config

        try:
            for k in keys:
                if not isinstance(value, dict):
                    return default
                value = value.get(k, {})
            return value if value != {} else default
        except Exception:
            return default

    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值，支持点分隔符和类型验证

        :param key: 配置键，可以使用点表示法访问嵌套值
        :param value: 要设置的值
        :param save: 是否立即保存到文件
        """
        # 获取当前配置字典
        config_dict = self._config_model.model_dump()

        # 设置新值
        keys = key.split(".")
        current = config_dict

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        # 使用 Pydantic 验证新配置
        try:
            self._config_model = CP2ConfigModel(**config_dict)
            if save:
                self._save_config()
        except ValidationError as e:
            raise ValueError(f"配置验证失败: {e}")

    def delete(self, key: str, save: bool = True):
        """
        删除配置键

        :param key: 要删除的配置键
        :param save: 是否立即保存到文件
        """
        config_dict = self._config_model.model_dump()
        keys = key.split(".")
        current = config_dict

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]
            try:
                self._config_model = CP2ConfigModel(**config_dict)
                if save:
                    self._save_config()
            except ValidationError as e:
                raise ValueError(f"删除配置项后验证失败: {e}")

    def validate_config(self) -> bool:
        """验证当前配置是否有效"""
        try:
            # 重新验证当前配置
            config_dict = self._config_model.model_dump()
            CP2ConfigModel(**config_dict)
            return True
        except ValidationError:
            return False

    def get_validation_errors(self) -> Optional[str]:
        """获取配置验证错误信息"""
        try:
            config_dict = self._config_model.model_dump()
            CP2ConfigModel(**config_dict)
            return None
        except ValidationError as e:
            return str(e)

    # 项目管理的便捷方法
    def add_mark(
        self, name: str, path: str, description: Optional[str] = None, save: bool = True
    ):
        """添加项目"""
        self._config_model.mark.add_mark(name, path, description)
        if save:
            self._save_config()

    def remove_mark(self, name: str, save: bool = True):
        """移除项目"""
        self._config_model.mark.remove_mark(name)
        if save:
            self._save_config()

    def get_mark(self, name: str) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        mark_info = self._config_model.mark.get_mark(name)
        return mark_info.model_dump() if mark_info else None

    def list_marks(self) -> Dict[str, Dict[str, Any]]:
        """列出所有项目"""
        marks = self._config_model.mark.list_marks()
        return {name: info.model_dump() for name, info in marks.items()}

    def mark_exists(self, name: str) -> bool:
        """检查项目是否存在"""
        return self._config_model.mark.get_mark(name) is not None

    def get_config_path(self) -> Path:
        """获取配置文件完整路径"""
        return self.config_file

    def get_ignore_file(self) -> str:
        """获取忽略文件名"""
        return self._config_model.exclude.ignore_file

    def get_exclude_patterns(self) -> List[str]:
        """获取排除模式列表"""
        return self._config_model.exclude.patterns

    def reload(self):
        """重新加载配置文件"""
        self._config_model = self._load_config()

    def save(self):
        """显式保存当前配置到文件"""
        self._save_config()

    def reset(self):
        """重置 config 文件恢复为默认"""
        self._config_model = CP2ConfigModel()
        self._save_config()

    def __contains__(self, key: str) -> bool:
        """检查配置键是否存在"""
        return self.get(key, None) is not None

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)

    def __delitem__(self, key: str):
        """支持字典式删除"""
        self.delete(key)


# 使用示例
def main():
    pass


if __name__ == "__main__":
    main()
