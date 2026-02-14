import json

class Config:
    _instance = None
    config = None

    def __new__(cls, config_path="config.json"):
        if cls._instance is None:
            try:
                loaded_config = Config._load_config(config_path)
                cls._instance = super().__new__(cls)
                Config.config = loaded_config
            except Exception as e:
                # 如果加载失败，不设置 _instance，以便下次可以重试或回退
                Config.config = {}
                raise e
        return cls._instance

    @classmethod
    def _load_config(cls, config_path):
        """加载配置文件
        
        Returns:
            dict: 配置字典
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {config_path} 格式错误")

    @classmethod
    def get(cls, key, default=None):
        """获取配置值
        Args:
            key (str): 配置键，支持点分隔符如'project.name'
            default: 默认值，当键不存在时返回
            
        Returns:
            Any: 配置值或默认值
        """
        if cls.config is None:
            try:
                Config()
            except Exception:
                if cls.config is None:
                    cls.config = {}
        
        if not isinstance(cls.config, dict):
            return default
            
        keys = key.split('.')
        value = cls.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @classmethod
    def set(cls, key, value):
        """设置配置值
        
        Args:
            key (str): 配置键，支持点分隔符如'project.name'
            value: 要设置的值
        """
        if cls.config is None:
            try:
                Config()
            except Exception:
                if cls.config is None:
                    cls.config = {}
                
        keys = key.split('.')
        current = cls.config
        
        # 确保 current 是字典
        if not isinstance(current, dict):
            cls.config = {}
            current = cls.config

        for i, k in enumerate(keys[:-1]):
            if not isinstance(current, dict):
                break
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        if isinstance(current, dict):
            current[keys[-1]] = value

    @classmethod
    def save(cls):
        """保存配置到文件"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(Config.config, f, indent=2, ensure_ascii=False)

    def __str__(self):
        """返回配置的字符串表示"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
