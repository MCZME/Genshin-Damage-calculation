# 原神伤害计算项目说明

## 项目概述
这是一个用于计算《原神》游戏中角色伤害的计算工具，支持不同角色、武器、圣遗物组合的伤害模拟计算。

## 主要功能模块
- **角色模块(character/)**: 包含各地区角色实现
  - 枫丹(FONTAINE): 芙宁娜、那维莱特、夏沃蕾等
  - 璃月(LIYUE): 香菱、行秋等
  - 蒙德(MONDSTADT): 班尼特等
  - 稻妻(INAZUMA): 枫原万叶、久岐忍等
  - 须弥(SUMERU): 纳西妲等
  - 纳塔(NATLAN): 西洛伦、伊安珊等新角色
- **武器模块(weapon/)**: 实现各类武器类型
  - 弓(Bow)
  - 法器(Catalyst)
  - 大剑(Claymore) 
  - 长柄武器(Polearm)
  - 单手剑(Sword)
- **圣遗物模块(artifact/)**: 圣遗物套装效果实现
- **UI模块(ui/)**: 图形用户界面实现
- **核心计算模块(core/)**: 
  - 基础类(BaseClass)
  - 伤害计算(DamageCalculation)
  - 元素反应(ElementalReaction)
  - 事件处理(EventHandler)

## 代码结构
```
project/
├── artifact/        # 圣遗物相关
├── character/       # 角色相关 
├── weapon/          # 武器相关
├── core/            # 核心计算逻辑
│   ├── calculation/ # 伤害/治疗/护盾计算
│   ├── effect/      # 效果系统
│   └── elementalReaction/ # 元素反应
├── ui/             # 用户界面
├── data/           # 数据文件
├── docs/           # 项目文档
└── tests/          # 测试用例
```

## 使用说明
1. 运行main.py启动应用程序
2. 在界面中选择角色、武器、圣遗物组合
3. 查看伤害计算结果和详细数据
4. 详细API文档请参考docs/core/目录下的文档
