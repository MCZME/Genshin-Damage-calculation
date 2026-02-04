# Project Rules & Guidelines

## Architecture: Event-Driven System
*   **Central Bus:** All major game logic (damage, healing, reactions, energy changes) MUST be handled via the `core.Event.EventBus`.
*   **Handlers:** Implement logic in `EventHandler` subclasses. Register them in `main.py` or the relevant module initialization.
*   **EventType:** Always use the appropriate `EventType` from `core.Event.EventType`. Do not create redundant event types if one already exists.

## Code Style & Conventions
*   **Naming:**
    *   Classes: `PascalCase` (e.g., `DamageCalculation`).
    *   Methods/Functions: `snake_case` (e.g., `calculate_damage`).
    *   Files: Match the primary class name if applicable (`BaseClass.py`), otherwise `snake_case`.
*   **Documentation:** Use docstrings for classes and complex methods. Comments should explain *why*, not *what*.
*   **Dependencies:** Avoid adding new external dependencies unless absolutely necessary. Check `requirements.txt` first.

## Data Management
*   **Config:** Use the `core.Config.Config` singleton for all application settings. Do not hardcode paths or magic numbers that should be configurable.
*   **JSON Data:** Character, weapon, and artifact data are primarily stored in JSON format within the `data/` directory. Ensure any modifications to these files maintain schema consistency.

## UI Development
*   **Framework:** Use PySide6 for all UI components.
*   **Styling:** Follow the existing patterns in `ui/styles.py` and ensure new widgets are integrated into the main window via `ui/main_window.py`.

## Testing & Verification
*   **Simulations:** Verify changes to damage logic by running batch simulations in `tests/batch_sim_test.py`.
*   **Consistency:** Ensure that new characters or weapons do not break existing calculation logic.
