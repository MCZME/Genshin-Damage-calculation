from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from character.character import CharacterState
from setup.DataHandler import clear_data
from setup.Event import EventBus, FrameEndEvent
from setup.Logger import get_emulation_logger
from setup.Map import CharacterClassMap, WeaponClassMap
from setup.Target import Target
from setup.Team import Team
from PySide6.QtCore import QThread, Signal
   
class Emulation(QThread):
    progress_updated = Signal(dict)
    finished = Signal(dict)
    error_occurred = Signal(str)

    # 游戏参数设计
    fps = 60  # 帧率
    target = None
    current_frame = 0
    team = None

    def __init__(self, team_data, action_sequence):
        super().__init__()
        self.team_data = team_data
        self.action_sequence = action_sequence
        Emulation.target = Target(0, 103)
        self.n = 0
        self.set_data()

    def run(self):
        self.simulate(Emulation._actions)

    def simulate(self,actions):
        """
        模拟执行一系列动作。
        参数:
        actions (list): 要执行的动作列表。
        {Name:actionName}
        """
        get_emulation_logger().new_log_file()
        action = iter(actions)
        self.next_character = next(action)
        Emulation.team.swap(self.next_character)
        Emulation.team.current_frame = 0 # 初始化当前帧数
        self.progress_updated.emit({"start": {
            "length": len(actions),
            "current": self.n + 1,
            "msg": f"{Emulation.team.current_character.name} 执行 {self.next_character}"
        }})
        self.n += 1
        try:
            self.next_character = next(action)
        except StopIteration:
            self.next_character = None
            get_emulation_logger().log("Team","最后一个动作开始执行")

        while True:
            Emulation.current_frame += 1
            if self._update(self.target,action):
                self.finished.emit({"result": "模拟完成"})
                break

    def _update(self, target, action):
        Emulation.team.update(target)
        Emulation.target.update()

        event = FrameEndEvent(Emulation.current_frame)
        EventBus.publish(event)

        if self.next_character is not None and Emulation.team.swap(self.next_character):
            get_emulation_logger().log("Team","切换成功")
            self.progress_updated.emit({"update": {
                "current": self.n + 1,
                "msg": f"{Emulation.team.current_character.name} 执行 {self.next_character[1]}"
            }})
            self.n += 1
            try:
                self.next_character = next(action)
            except StopIteration:
                self.next_character = None
                get_emulation_logger().log("Team","最后一个动作开始执行")

        if self.next_character is None and self.team.current_character.state[0] == CharacterState.IDLE:
            get_emulation_logger().log("Team","动作执行完毕")
            return True
        return False

    def init():
        Emulation.current_frame = 0

    def set_data(self):
        clear_data()
        Emulation.init()
        
        # 1. 创建角色和队伍
        characters = []
        for char_data in self.team_data:
            if not char_data or "error" in char_data:
                continue
            talents = char_data['character']['talents'].split('/')
            character = CharacterClassMap[char_data['character']['id']](
                level=char_data['character']['level'],
                skill_params=[
                    int(talents[0]),
                    int(talents[1]),
                    int(talents[2])
                ],
                constellation=char_data['character'].get('constellation', 0)
            )
            
            if char_data['weapon']:
                weapon_class = WeaponClassMap[char_data['weapon']['name']]
                weapon = weapon_class(
                    character=character,
                    level=char_data['weapon']['level'],
                    lv=char_data['weapon'].get('refinement', 1)
                )
                character.setWeapon(weapon)
            
            if char_data['artifacts']:
                artifacts = []
                for arti_data in char_data['artifacts']:
                    if arti_data['main_stat'] == {}:
                        continue
                    artifacts.append(Artifact(
                        name=arti_data['set_name'],
                        piece=self.get_Piece(arti_data),
                        main=arti_data['main_stat'],
                        sub=arti_data['sub_stats']
                    ))
                am = ArtifactManager(artifacts, character)
                character.setArtifact(am)
            
            characters.append(character)
        
        if not characters:
            raise ValueError("没有有效的角色配置")
        
        Emulation.team = Team(characters)
        
        # 2. 转换动作序列格式
        formatted_actions = []
        for action in self.action_sequence:
            method_name = self.get_action_name(action['action'])
            if not method_name:
                continue
                
            params = action.get('params', {})
            method_params = None
            if params:
                method_params = self.get_param(params)
            
            formatted_actions.append(
                (action['character'], method_name, method_params)
            )
        
        Emulation._actions = formatted_actions
        
    def get_param(self,param):
        if param is {}:
            return None
        else:
            for k,v in param.items():
                if k == '攻击次数':
                    return int(v)
                elif k == '攻击距离':
                    return True if v == '高空' else False
                elif k == '释放时间':
                    return True if v == '长按' else False
                elif k == '时间':
                    return int(v)
                else:
                    return None
                
    def get_Piece(self,arti_data):
        if arti_data['slot'] == '生之花':
            return ArtifactPiece.Flower_of_Life
        elif arti_data['slot'] == '死之羽':
            return ArtifactPiece.Plume_of_Death
        elif arti_data['slot'] == '时之沙':
            return ArtifactPiece.Sands_of_Eon
        elif arti_data['slot'] == '空之杯':
            return ArtifactPiece.Goblet_of_Eonothem
        elif arti_data['slot'] == '理之冠':
            return ArtifactPiece.Circlet_of_Logos
        else:
            return None
        
    def get_action_name(self,action):
        if action == '普通攻击':
            return 'normal_attack'
        elif action == '重击':
            return 'charged_attack'
        elif action == '下落攻击':
            return 'plunging_attack'
        elif action == '元素战技':
            return 'elemental_skill'
        elif action == '元素爆发':
            return 'elemental_burst'
        elif action == '跳过':
            return 'skip'
