from core.context import SimulationContext, set_context

def test_simulation_context_health():
    # 1. 准备环境
    with SimulationContext() as ctx:
        # 2. 执行健康检查
        is_healthy = ctx.health_check()
        
        # 3. 断言
        assert is_healthy is True
        print("Context Health Check Test Passed!")

if __name__ == "__main__":
    test_simulation_context_health()
