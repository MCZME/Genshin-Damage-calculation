from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from character.character import CharacterState
from setup.DataHandler import clear_data
from setup.Event import EventBus, FrameEndEvent
from setup.Logger import get_emulation_logger
from setup.Map import CharacterClassMap, WeaponClassMap
from setup.Target import Target
from setup.Team import Team


class Emulation:
    # 游戏参数设计
    fps = 60  # 帧率
    target = None
    current_frame = 0
    team = None

    def __init__(self,team:Team,target_id,target_level):
        Emulation.target = Target(target_id, target_level)
        Emulation.team = team

    def simulate(self,actions):
        """
        模拟执行一系列动作。
        参数:
        actions (list): 要执行的动作列表。
        {Name:actionName}
        """
        get_emulation_logger().new_log_file()
        action = iter(actions)
        Emulation.team.swap(next(action))
        Emulation.team.current_frame = 0 # 初始化当前帧数
        try:
            self.next_character = next(action)
        except StopIteration:
            self.next_character = None
            print("最后一个动作开始执行")

        while True:
            Emulation.current_frame += 1
            if self._update(self.target,action):
                break

    def _update(self, target, action):
        Emulation.team.update(target)
        Emulation.target.update()

        event = FrameEndEvent(Emulation.current_frame)
        EventBus.publish(event)

        if self.next_character is not None and Emulation.team.swap(self.next_character):
            print("切换成功")
            try:
                self.next_character = next(action)
            except StopIteration:
                self.next_character = None
                print("最后一个动作开始执行")

        if self.next_character is None and self.team.current_character.state[0] == CharacterState.IDLE:
            print("动作执行完毕")
            return True
        return False

    def init():
        Emulation.current_frame = 0

def start_simulation(team_data, action_sequence):
    """
    开始模拟伤害计算
    参数:
        team_data: 从MainWindow收集的队伍信息列表
        action_sequence: 从MainWindow收集的动作序列列表
    """
    clear_data()
    Emulation.init()
    # 1. 创建角色和队伍
    characters = []
    for char_data in team_data:
        if not char_data or "error" in char_data:
            continue  # 跳过未配置的角色槽
        talents = char_data['character']['talents'].split('/')
        # 创建角色
        character = CharacterClassMap[char_data['character']['id']](
            level=char_data['character']['level'],
            skill_params=[
                 int(talents[0]) ,
                 int(talents[1]),
                 int(talents[2])
            ],
            constellation=char_data['character'].get('constellation', 0)
        )
        
        # 设置武器
        if char_data['weapon']:
            weapon_class = WeaponClassMap[char_data['weapon']['name']]
            weapon = weapon_class(
                character=character,
                level=char_data['weapon']['level'],
                lv=char_data['weapon'].get('refinement', 1)
            )
            character.setWeapon(weapon)
        
        # 设置圣遗物
        if char_data['artifacts']:
            artifacts = []
            for arti_data in char_data['artifacts']:
                if arti_data['main_stat'] == {}:
                    continue
                artifacts.append(Artifact(
                    name=arti_data['set_name'],
                    piece=get_Piece(arti_data),
                    main=arti_data['main_stat'],
                    sub=arti_data['sub_stats']
                ))
            am = ArtifactManager(artifacts, character)
            character.setArtifact(am)
        
        characters.append(character)
    
    if not characters:
        raise ValueError("没有有效的角色配置")
    
    team = Team(characters)
    
    # 2. 转换动作序列格式
    formatted_actions = []
    for action in action_sequence:
        # 格式: (角色名, 动作方法名, 参数)
        method_name = get_action_name(action['action'])
        if not method_name:
            continue  # 跳过无效动作
            
        params = action.get('params', {})
        # 将参数转换为适合方法调用的格式
        method_params = None
        if params:
            method_params = get_param(params)
        
        formatted_actions.append(
            (action['character'], method_name, method_params)
        )
    
    # 3. 创建模拟器并开始模拟
    emulator = Emulation(
        team=team,
        target_id=0,  # 可配置化
        target_level=90  # 可配置化
    )
    
    # 4. 执行模拟
    try:
        emulator.simulate(formatted_actions)
    except Exception as e:
        print(f"模拟过程中出错: {str(e)}")
        Emulation.init()
        raise

def get_param(param):
    if param is {}:
        return None
    else:
        for k,v in param.items():
            if k == '攻击次数':
                return int(v)
            elif k == '攻击距离':
                return True if v == '高空' else False
            elif k == '时间':
                return True if v == '长按' else False
            else:
                return None
            
def get_Piece(arti_data):
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
    
def get_action_name(action):
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