from pathlib import Path
from typing import Any, Dict, Optional
import toml
from platformdirs import user_config_dir


class CP2Config:
    def __init__(self, config_filename: str = "config.toml"):
        """
        初始化配置管理器

        :param app_name: 应用名称，用于确定配置目录
        :param config_filename: 配置文件名，默认为 config.toml
        """
        # 获取跨平台配置目录
        self.config_dir = Path(user_config_dir("copy_to"))
        self.config_file = self.config_dir / config_filename

        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则获取默认值并创建配置文件，返回默认值"""
        try:
            if self.config_file.exists():
                # 如果配置文件存在，读取并解析
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return toml.load(f)
            else:
                # 如果配置文件不存在，使用默认配置并创建文件
                default_config = self._cp2_default_config()
                with open(self.config_file, "w", encoding="utf-8") as f:
                    toml.dump(default_config, f)
                return default_config
        except toml.TomlDecodeError:
            raise RuntimeError("配置文件格式错误，请检查 config.toml 文件的语法")
        except Exception as e:
            raise RuntimeError(f"加载配置文件失败: {e}")

    def _cp2_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "exclude": {
                "patterns": [
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
                "config_file": ".gitignore",
            }
        }

    def _save_config(self):
        """保存当前配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(self._config, f)
        except Exception as e:
            raise RuntimeError(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取配置值，支持点分隔符 (如 'database.host')

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
        设置配置值，支持点分隔符 (如 'database.host')

        :param key: 配置键，可以使用点表示法访问嵌套值
        :param value: 要设置的值
        :param save: 是否立即保存到文件
        """
        keys = key.split(".")
        current = self._config

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        if save:
            self._save_config()

    def delete(self, key: str, save: bool = True):
        """
        删除配置键

        :param key: 要删除的配置键
        :param save: 是否立即保存到文件
        """
        keys = key.split(".")
        current = self._config

        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return
            current = current[k]

        if keys[-1] in current:
            del current[keys[-1]]
            if save:
                self._save_config()

    def get_config_path(self) -> Path:
        """获取配置文件完整路径"""
        return self.config_file

    def reload(self):
        """重新加载配置文件"""
        self._config = self._load_config()

    def save(self):
        """显式保存当前配置到文件"""
        self._save_config()

    def reset(self):
        """重置 config 文件恢复为默认"""
        self._config = self._cp2_default_config()
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
if __name__ == "__main__":
    # 初始化配置管理器
    config = CP2Config()

    config.reset()

    # 打印配置文件路径
    print(f"配置文件位置: {config.get_config_path()}")

    # 打印当前所有配置
    print("\n当前所有配置:")
    print(toml.dumps(config._config))
