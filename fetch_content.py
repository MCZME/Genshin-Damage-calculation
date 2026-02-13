import asyncio
import sys
import argparse
from core.data.automation.manager import AutomationManager
from core.context import create_context

async def main():
    parser = argparse.ArgumentParser(description="原神仿真引擎数据抓取工具")
    parser.add_argument("name", help="角色名称 (如 '芙宁娜')")
    parser.add_argument("--type", default="character", choices=["character", "weapon"], help="添加的内容类型")
    args = parser.parse_args()

    create_context()
    manager = AutomationManager()

    if args.type == "character":
        success = await manager.add_character(args.name)
        if success:
            print(f"SUCCESS: 角色 [{args.name}] 数据同步成功！")
        else:
            print(f"FAILED: 角色 [{args.name}] 同步失败")

if __name__ == "__main__":
    asyncio.run(main())
