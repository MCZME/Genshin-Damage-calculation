# Flet 异步应用 (Async Apps) 开发规范

Flet 原生支持 `asyncio`。为了充分利用系统资源并支持 WASM (Pyodide) 等环境，本项目推荐在复杂的 UI 交互和 I/O 操作中使用异步架构。

## 1. 异步入口 (Async Main)
将 `main` 函数标记为 `async`，以便在应用启动时即可使用 `await`。
```python
async def main(page: ft.Page):
    await some_async_init()
    page.add(ft.Text("异步应用已启动"))

ft.run(main)
```

## 2. 事件处理器 (Event Handlers)
事件处理器可以是同步的，也可以是异步的。
- **同步处理器**：如果逻辑中不包含 `await`，使用普通的 `def`。
- **异步处理器**：如果需要调用异步方法，**必须**使用 `async def`。
  ```python
  async def button_click(e):
      await asyncio.sleep(1) # 模拟 I/O
      page.add(ft.Text("执行完毕"))
  ```
- **注意**：Python 不支持异步 lambda。如果逻辑复杂，请定义完整的异步函数。

## 3. 延时操作 (Sleeping)
在异步 Flet 应用中，**严禁使用 `time.sleep()`**，因为它会阻塞整个事件循环。
- **必须使用** `await asyncio.sleep()`。

## 4. 后台任务 (Background Tasks)
对于需要长时间运行或自更新的逻辑，应使用 `page.run_task()`。

### 控件生命周期与任务管理
在自定义控件中，利用 `did_mount` 和 `will_unmount` 管理后台任务的生命周期：
```python
class AsyncControl(ft.Text):
    def did_mount(self):
        self.running = True
        self.page.run_task(self.background_logic)

    def will_unmount(self):
        self.running = False # 停止循环

    async def background_logic(self):
        while self.running:
            self.value = get_new_data()
            self.update()
            await asyncio.sleep(1)
```

## 5. 最佳实践
- **避免阻塞**：确保所有耗时操作（网络请求、大型计算）都已异步化，或在 `run_task` 中运行。
- **UI 更新**：在异步处理器中修改控件属性后，记得调用 `page.update()` 或 `control.update()`。
- **并发控制**：在处理高频事件（如滚动、输入）时，结合 `asyncio` 的锁或节流机制，防止竞态条件。

---
*来源：Flet 官方文档 - Async apps*
