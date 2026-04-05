import os
from core.data.automation.fetcher import AmberFetcher
from core.data.automation.transformer import DataTransformer
from core.data.automation.weapon_transformer import WeaponDataTransformer
from core.data.automation.generator import DataGenerator
from core.data.automation.db_sync import DatabaseSync
from core.logger import get_emulation_logger


class AutomationManager:
    """
    自动化流程管理器。
    串联 Fetcher, Transformer, DBSync 和 Generator，实现一键式数据产出。
    """

    def __init__(self) -> None:
        self.fetcher = AmberFetcher()
        self.transformer = DataTransformer()
        self.generator = DataGenerator()
        self.db_syncer = DatabaseSync()

    async def add_character(self, name: str, region: str = "OTHER") -> bool:
        """自动化添加一个新角色。"""
        get_emulation_logger().log_info(
            f"--- 开始自动化处理角色: {name} ---", sender="Automation"
        )

        # 1. 抓取数据
        char_id = self.fetcher.find_avatar_id(name)
        if not char_id:
            return False

        raw_data = self.fetcher.fetch_avatar_detail(char_id, vh="63F3")
        curve_data = self.fetcher.fetch_growth_curves(vh="63F3")

        if not raw_data or not curve_data:
            get_emulation_logger().log_error("网络数据抓取失败", sender="Automation")
            return False

        # 2. 转换数据
        get_emulation_logger().log_info("正在清洗并计算属性...", sender="Automation")
        clean_data = self.transformer.transform(raw_data, curve_data)

        # 3. 数据库同步并获取真实 ID
        real_id = self.db_syncer.sync_character(clean_data)
        if not real_id:
            get_emulation_logger().log_error(
                "数据库同步失败，停止文件生成", sender="Automation"
            )
            return False

        # 回填真实 ID 供 Generator 使用
        clean_data["metadata"]["id"] = real_id

        # 4. 确定输出路径
        dir_name = clean_data["metadata"].get("route", name).lower()
        api_region = raw_data.get("region", region)
        output_dir = f"character/{api_region}/{dir_name}"
        output_path = os.path.join(output_dir, "data.py")

        # 5. 生成文件
        get_emulation_logger().log_info(
            f"正在生成本地代码文件: {output_path}", sender="Automation"
        )
        return self.generator.generate_character_data(clean_data, output_path)

    async def add_weapon(self, name: str) -> bool:
        """自动化添加一个新武器。"""
        get_emulation_logger().log_info(
            f"--- 开始自动化处理武器: {name} ---", sender="Automation"
        )

        # 1. 抓取数据 (需要武器 API 支持)
        weapon_id = self.fetcher.find_weapon_id(name)
        if not weapon_id:
            get_emulation_logger().log_error(
                f"未找到武器: {name}", sender="Automation"
            )
            return False

        raw_data = self.fetcher.fetch_weapon_detail(weapon_id, vh="63F3")
        curve_data = self.fetcher.fetch_weapon_curve(vh="63F3")

        if not raw_data or not curve_data:
            get_emulation_logger().log_error("武器数据抓取失败", sender="Automation")
            return False

        # 2. 转换数据
        get_emulation_logger().log_info("正在清洗武器数据...", sender="Automation")
        weapon_transformer = WeaponDataTransformer()
        clean_data = weapon_transformer.transform(raw_data, curve_data)

        # 3. 数据库同步并获取真实 ID
        real_id = self.db_syncer.sync_weapon(clean_data)
        if not real_id:
            get_emulation_logger().log_error(
                "武器数据库同步失败，停止文件生成", sender="Automation"
            )
            return False

        # 回填真实 ID
        clean_data["metadata"]["id"] = real_id

        # 4. 确定输出路径 (直接放在 weapon/{TYPE}/ 目录下)
        output_path = "weapon/weapon.py"  # 传递基础路径，generator 会处理类型目录

        # 5. 生成文件
        get_emulation_logger().log_info(
            f"正在生成武器代码文件...", sender="Automation"
        )
        return self.generator.generate_weapon_data(clean_data, output_path)
