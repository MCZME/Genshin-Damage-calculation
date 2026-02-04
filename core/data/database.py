import mysql.connector
from mysql.connector import pooling
from typing import List, Any, Optional
from core.config import Config

class DatabaseManager:
    """
    MySQL 数据库连接管理器。
    负责从配置加载连接信息并管理数据库会话。
    """
    def __init__(self):
        self.config = Config.get('database')
        self.pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化数据库连接池"""
        try:
            db_config = {
                "host": self.config.get('host'),
                "user": self.config.get('username') or self.config.get('user'),
                "password": self.config.get('password'),
                "database": self.config.get('database', 'genshin_data'), # 默认库名
                "port": self.config.get('port', 3306)
            }
            # 创建连接池以支持多线程/并行模拟
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="genshin_pool",
                pool_size=5,
                **db_config
            )
        except Exception as e:
            from core.logger import get_emulation_logger
            get_emulation_logger().log_error(f"数据库连接池初始化失败: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Any]:
        """执行查询并返回所有结果"""
        if not self.pool:
            return []
        
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def execute_non_query(self, query: str, params: Optional[tuple] = None):
        """执行非查询 SQL (INSERT, UPDATE, DELETE)"""
        if not self.pool:
            return
            
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
        finally:
            cursor.close()
            conn.close()

# 单例实例
db_manager = DatabaseManager()
