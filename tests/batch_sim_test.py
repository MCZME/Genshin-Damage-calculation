import json
import multiprocessing

from Emulation import Emulation
from core.Config import Config
from main import init


def test_batch_sim():
    c = None
    a = None
    t = None
    with open('data/last_file_test.json', 'r') as f:
        data = json.load(f)
        c = data['team_data']
        a = data['action_sequence']
        t = data['target_data']
    
    for i in range(3):
        Emulation.emulation_init()
        init()
        e = Emulation(c, a, t)
        e.set_log_file()
        e.simulate()
        print("第{}次模拟".format(i+1))

def run_simulation(c,a,t,sim_file_path,sim_id):
    Emulation.emulation_init()
    init()
    e = Emulation(c, a, t)
    return e.simulate_multi(sim_file_path,sim_id)

def error_callback(error):
    print(f"[Error] {error}")

def test_batch_sim_multi():
    c = None
    a = None
    t = None
    with open('data/last_file_test.json', 'r') as f:
        data = json.load(f)
        c = data['team_data']
        a = data['action_sequence']
        t = data['target_data']

    PROCESSES = Config.get('emulation.batch_sim_processes')
    TOLAL = Config.get('emulation.batch_sim_num')
    
    with multiprocessing.Pool(
        processes=PROCESSES
    ) as pool:
        async_results = [
            pool.apply_async(
                run_simulation,
                args=(c, a, t,'./data/',sim_id),
                error_callback=error_callback,
            )
            for sim_id in range(TOLAL)
        ]

        # 等待所有任务完成并收集结果
        results = []
        for res in async_results:
            try:
                results.append(res.get(timeout=10))  # 设置超时防止卡死
            except multiprocessing.TimeoutError:
                print("任务超时")

    success_count = sum(1 for r in results if r.get("status") == "success")
    print(f"成功率: {success_count / len(results):.1%}")
