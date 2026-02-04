# Genshin Damage Calculation - Project Overview

## Project Description
This project is a sophisticated damage calculator for the game *Genshin Impact*. It simulates combat scenarios, calculating damage based on character stats, weapons, artifacts, and elemental reactions. It features a modular architecture driven by an event bus system and includes a graphical user interface (GUI) built with PySide6.

## Key Technologies
*   **Language:** Python
*   **GUI Framework:** PySide6 (Qt for Python)
*   **Architecture:** Event-Driven (Custom `EventBus`)
*   **Data Storage:** JSON (configuration), potential for database integration (MySQL/Mongo drivers in requirements).
*   **Concurrency:** Multiprocessing for batch simulations.

## Architecture Overview
The project is organized into several key modules:

*   **`core/`**: The heart of the application.
    *   **`Event.py`**: Defines the `EventBus` and `EventType` enums. This is the central nervous system; all actions (damage, healing, reactions) are published as events.
    *   **`Config.py`**: Singleton configuration manager loading from `config.json`.
    *   **`calculation/`**: Handlers for damage, healing, and shield logic.
    *   **`elementalReaction/`**: Logic for elemental auras and reactions.
*   **`character/`**: Implementations of individual characters, organized by region (e.g., `FONTAINE`, `LIYUE`).
*   **`weapon/`**: Implementations of weapons, categorized by type (Bow, Sword, etc.).
*   **`artifact/`**: Implementations of artifact set effects.
*   **`ui/`**: The graphical user interface code.
*   **`Emulation.py`**: The simulation controller class, used to orchestrate combat scenarios.

## Building and Running

### Prerequisites
*   Python 3.x
*   Dependencies listed in `requirements.txt`

### Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
To launch the main GUI:
```bash
python main.py
```
This initializes the event handlers, configuration, and opens the main window.

### Running Simulations/Tests
Batch simulations and tests can be found in the `tests/` directory. For example:
```bash
python tests/batch_sim_test.py
```
*Note: Some tests may rely on specific data files in `data/`.*

## Configuration
The application uses a `config.json` file for settings. The `core.Config` class manages loading and saving these settings.

## Development Conventions

*   **Event-Driven Logic:** New game mechanics should likely be implemented as `EventHandler` subclasses and subscribed to the relevant `EventType` in the `EventBus`.
*   **Modular Entities:** Characters, Weapons, and Artifacts should inherit from their respective base classes in `core/` or parent modules.
*   **File Naming:**
    *   Classes often match filenames (PascalCase), e.g., `DamageCalculation.py`.
    *   Directories are generally lowercase.
*   **Logging:** A custom logging system is initialized in `core/Logger.py`.

## Directory Structure
*   `artifact/`: Artifact set logic.
*   `character/`: Character logic.
*   `core/`: Core engine (Events, Config, Base classes).
*   `data/`: Data files for simulations.
*   `docs/`: Documentation.
*   `ui/`: GUI components.
*   `weapon/`: Weapon logic.
