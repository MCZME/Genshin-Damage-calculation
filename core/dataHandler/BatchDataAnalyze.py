from datetime import datetime, timezone
import json

from DataRequest import MongoDB
from core.Config import Config
from core.dataHandler.DataCompression import RestoreData


class BatchDataAnalyze:
    def __init__(self, uid):
        self.uid = uid
        self.num = 0
        self.result = None
        self.get_parameter()

    def get_parameter(self):
        """
        获取参数
        """
        with open(f'./data/sim/{self.uid}/config.json', 'r') as f:
            config = json.load(f)
            self.num = config['simulation_num']

    def initialize(self):
        """
        初始化
        """
        with open(f'./data/sim/{self.uid}/data/{self.uid}_0.json', 'r') as f:
            data = RestoreData(json.load(f))
            self.time = len(data)
            self.result = self.extract_dmg_data(data)
            for _, e in self.result.items():
                for event in e:
                    event['max_value'] = event['value']
                    event['min_value'] = event['value']
    
    def extract_dmg_data(self,data):
        """
        提取伤害数据
        """
        result = {}
        for k, e in {k:d['event'] for k, d in data.items()}.items():
            for event in e:
                if event['type'] == 'damage_event':
                    if k in result.keys():
                        result[k].append(event)
                    else:
                        result[k] = [event]
        return result

    def analyze(self):
        """
        分析数据
        """
        self.initialize()
        for i in range(1, self.num):
            with open(f'./data/sim/{self.uid}/data/{self.uid}_{i}.json', 'r') as f:
                data = json.load(f)
                self._analyze(RestoreData(data))
            print(f'分析数据 {i}/{self.num}')
        
        for k, e in self.result.items():
            for i in range(len(e)):
                e[i]['value'] = e[i]['value'] / self.num

        self.dps = sum([e1['value'] for e in self.result.values() for e1 in e]) / self.time * 60

    def _analyze(self, data):
        """
        分析数据
        """
        d = self.extract_dmg_data(data)
        for k, e in d.items():
            if k in self.result.keys():
                for i in range(len(e)):
                    if e[i]['value'] > self.result[k][i]['max_value']:
                        self.result[k][i]['max_value'] = e[i]['value']
                    if e[i]['value'] < self.result[k][i]['min_value']:
                        self.result[k][i]['min_value'] = e[i]['value']
                    self.result[k][i]['value'] += e[i]['value']
            else:
                print(f'Error: {k} 不在结果中')

    def send_to_MongoDB(self):
        """
        发送数据到MongoDB
        """
        db = MongoDB('genshin_damage_report','analytics')
        db.insert_document({
            'uid': self.uid,
            'version': '0.1.0',
            'name': Config.get('batch.name'),
            "created_at": datetime.now(timezone.utc).isoformat(),
            'simulation_num': self.num,
            'dps': self.dps,
            'simulation_duration': self.time,
            'frames': [{
                'frame': frame,
                'event': self.result[frame]
            } for frame in self.result.keys()],
        })
        print('分析结果数据插入成功')
        