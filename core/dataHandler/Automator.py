from datetime import datetime, timezone
import json
import multiprocessing
import os
import uuid

from Emulation import Emulation
from core.Config import Config
from core.Logger import get_ui_logger
from core.dataHandler.BatchDataAnalyze import BatchDataAnalyze


class SimConfigAutomator:
    def __init__(self, config_path, conditional_parameters:list):
        """
        目前支持角色的武器（类型，等级和精炼），动作，目标（等级和抗性）的自动化生成\n
        :param config_path: 配置文件路径
        :param conditional_parameters: 条件参数，格式为['team_data[0].character.level', [10, 20, 30]]
        """
        with open(config_path, 'r') as f:
            data = json.load(f)
            self.team_data = data['team_data']
            self.action_sequence = data['action_sequence']
            self.target_data = data['target_data']
        
        self.condition = conditional_parameters[0]
        self.parameters = conditional_parameters[1]

        self.new_config = {}

    def create_new_config(self):
        d = self.condition.split('.')
        if d[0][:-3] not in ['team_data', 'action_sequence', 'target_data']:
            raise ValueError('Invalid parameter name')
        
        if d[0][:-3] == 'team_data':
            self.handle_team_data()
        elif d[0][:-3] == 'action_sequence':
            self.handle_action_sequence()
        elif d[0][:-3] == 'target_data':
            self.handle_target_data()
    
    def handle_team_data(self):
        d = self.condition.split('.')

        for i in self.parameters:
            index = d[0].replace('team_data', '').strip('[').strip(']')
            if d[1] == 'artifacts':
                # 圣遗物测试直接手动设置
                ...
            else:
                new_config = self.team_data.copy()
                new_config[int(index)][d[1]][d[2]] = i
                self.new_config[i] = new_config

    def handle_action_sequence(self):
        ...

    def handle_target_data(self):
        d = self.condition.split('.')

        for i in self.parameters:
            new_config = self.target_data.copy()
            new_config[d[1]] = i
            self.new_config[i] = new_config

class SimAutomator:
    def __init__(self, config_path, new_config:dict, conditional:str):
        """
        :param config_path: 配置文件路径
        :param new_config: 新配置 只有需要修改部分
        :param conditional: 条件参数 表示修改位置
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.new_config = new_config
        self.conditional = conditional

        self.sim_result = {}

    def automate(self):
        config = self.config.copy()
        for i in self.new_config.keys():
            get_ui_logger().log_info(f"开始模拟: {i}")
            config[self.conditional] = self.new_config[i]
            self.sim(i, config)
        get_ui_logger().log_info("所有模拟完成")

    def sim(self, id, config):
        uid = uuid.uuid4().hex
        os.mkdir(Config.get("batch.batch_sim_file_path") + uid + '/')
        os.mkdir(Config.get("batch.batch_sim_file_path") + uid + '/logs')
        os.mkdir(Config.get("batch.batch_sim_file_path") + uid + '/data')
        with open(Config.get("batch.batch_sim_file_path") + uid + '/config.json', "w", encoding="utf-8") as f:
            json.dump({
                'uid': uid,
                'version': Config.get('project.version'),
                "created_at": datetime.now(timezone.utc).isoformat(),
                'simulation_num': Config.get('batch.batch_sim_num'),
                'name': Config.get('batch.name'),
                "team_data": config['team_data'],
                "action_sequence": config['action_sequence'],
                "target_data": config['target_data']
            }, f)
        with multiprocessing.Pool(processes=Config.get("batch.batch_sim_processes")) as pool:
            async_results = [pool.apply_async(
                simulate_multi,
                args=(config['team_data'], 
                    config['action_sequence'], 
                    config['target_data'], 
                    Config.get("batch.batch_sim_file_path"),
                    sim_id,
                    uid),
                error_callback=error_callback,
                callback=callback
            ) for sim_id in range(Config.get("batch.batch_sim_num"))]
            results = []
            for res in async_results:
                try:
                    results.append(res.get(timeout=10))  # 设置超时防止卡死
                except multiprocessing.TimeoutError:
                    get_ui_logger().log_error("任务超时")
        success_count = sum(1 for r in results if r.get("status") == "success")
        get_ui_logger().log_info(f"--成功率: {success_count / len(results):.1%}")

        a = BatchDataAnalyze(uid)
        a.analyze()
        a.save_data()

        self.sim_result[id] = uid

def simulate_multi(team_data, action_sequence, target_data, sim_file_path, sim_id, uid):
    Emulation.emulation_init()
    from main import sim_init
    sim_init()
    e = Emulation(team_data, action_sequence, target_data)
    return e.simulate_multi(sim_file_path, sim_id, uid)

def error_callback(error):
    get_ui_logger().log_ui_error(error)

def callback(result):
    if result['status'] == 'success':
        get_ui_logger().log_info(f"--模拟完成: {result['sim_id']}")
    else:
        get_ui_logger().log_ui_error(f"--模拟失败: {result['sim_id']}")


