# Genshin Damage Calculation - Project Overview

## Project Description
This project is a sophisticated damage calculator for the game *Genshin Impact*. It simulates combat scenarios, calculating damage based on character stats, weapons, artifacts, and elemental reactions. It features a highly modular architecture driven by an event bus system and a System-Manager pattern, including a graphical user interface (GUI) built with PySide6.

## Key Technologies
*   **Language:** Python
*   **GUI Framework:** PySide6 (Qt for Python)
*   **Architecture:** Event-Driven (`EventBus`), System-Manager Pattern (`core/systems`)
*   **Data Storage:** JSON (configuration), Database support (MySQL, MongoDB)
*   **Concurrency/Async:** Multiprocessing for batch simulations, Trio for async operations.
*   **Automation:** Selenium (likely for data acquisition).

## Architecture Overview
The project has evolved into a structured core engine:

*   **`core/`**: The heart of the application.
    *   **`event.py`**: Defines `EventBus` and `EventType`. The central nervous system for decoupling logic.
    *   **`config.py`**: Singleton configuration manager.
    *   **`systems/`**: Core logic engines.
        *   `damage_system.py`: Damage calculation formulas.
        *   `reaction_system.py`: Elemental reaction logic.
        *   `energy_system.py`, `shield_system.py`, `health_system.py`, etc.
    *   **`action/`**: definitions and handlers for combat actions (Damage, Healing).
    *   **`effect/`**: Buffs, Debuffs, Elemental Resonances, and Stat Modifiers.
    *   **`entities/`**: Base definitions for Combat Entities, Elemental Entities, etc.
    *   **`factory/`**: Parsers and Factories (e.g., `team_factory.py`) for object creation.
    *   **`dataHandler/`**: Utilities for data analysis, automation, and transmission.
*   **`character/`**: Implementations of individual characters, organized by region (e.g., `FONTAINE`, `LIYUE`).
*   **`weapon/`**: Implementations of weapons, categorized by type (Bow, Sword, etc.).
*   **`artifact/`**: Implementations of artifact set effects.
*   **`ui/`**: The graphical user interface code.
*   **`Emulation.py`**: The top-level simulation controller.

## Building and Running

### Prerequisites
*   Python 3.13.3
*   虚拟环境: 使用 `virtualenv` 创建，环境名为 `genshin_damage_calculation`。
*   Dependencies listed in `requirements.txt`
*   开发环境的终端是Power Shell，如果需要执行多条命令请使用；而不是&&。

### Installation
1.  Clone the repository.
2.  激活虚拟环境并安装依赖:
    ```bash
    .\genshin_damage_calculation\Scripts\activate
    pip install -r requirements.txt
    ```

### Running the Application
To launch the main GUI:
```bash
python main.py
```
This initializes the event handlers, configuration, and opens the main window.

### Running Simulations/Tests
核心仿真与系统验证测试：
```bash
python test.py
```
该脚本是项目的主要仿真入口，用于验证伤害计算和系统逻辑。

## Configuration
The application uses `config.json` for settings, managed by `core.config.Config`.

## Development Conventions

*   **Event-Driven & System Logic:** New mechanics should be implemented within the appropriate `System` or as an `EventHandler`.
*   **Modular Entities:** Characters, Weapons, and Artifacts inherit from base classes in `core/entities` or `core/base_entity.py`.
*   **Naming Conventions:**
    *   **Core Modules:** Predominantly `snake_case` (e.g., `damage_system.py`, `event.py`).
    *   **Entities (Characters/Weapons):** Often `PascalCase` to match the entity name (e.g., `KaedeharaKazuha.py`), though some mixing exists.
    *   **Directories:** Generally lowercase.
*   **Logging:** Centralized logging via `core/logger.py`.

## Directory Structure
*   `artifact/`: Artifact set logic.
*   `character/`: Character logic.
*   `core/`: Core engine components.
    *   `action/`: Action definitions.
    *   `dataHandler/`: Data processing tools.
    *   `effect/`: Status effects.
    *   `entities/`: Entity definitions.
    *   `factory/`: Object creation factories.
    *   `mechanics/`: Game mechanics (Aura, Infusion).
    *   `skills/`: Skill logic.
    *   `systems/`: Logic Managers.
*   `data/`: Data files.
*   `docs/`: Documentation.
*   `ui/`: GUI components.
*   `weapon/`: Weapon logic.