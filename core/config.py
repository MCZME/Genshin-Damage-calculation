import json

class Config:
    _instance = None
    config = None

    def __new__(cls, config_path="config.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            Config.config = Config._load_config(config_path)
        return cls._instance

    @classmethod
    def _load_config(self,config_path):
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
            # 自动尝试加载默认位置的配置
            try:
                Config()
            except:
                return default
        
        keys = key.split('.')
        value = cls.config
        if value is None: return default
        
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
            except:
                cls.config = {}
                
        keys = key.split('.')
        current = cls.config
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    @classmethod
    def save(self):
        """保存配置到文件"""
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(Config.config, f, indent=2, ensure_ascii=False)

    def __str__(self):
        """返回配置的字符串表示"""
        return json.dumps(self.config, indent=2, ensure_ascii=False)
