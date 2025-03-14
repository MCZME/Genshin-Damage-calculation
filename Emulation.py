import json
from artifact.artifact import Artifact, ArtifactManager, ArtifactPiece
from character.character import CharacterState
from setup.Map import CharacterClassMap, WeaponClassMap
from setup.Target import Target
from setup.Team import Team


class Emulation:
    # 游戏参数设计
    fps = 60  # 帧率
    target = None

    def __init__(self,team:Team,target_id,target_level):
        self.target = Target(target_id, target_level)
        self.team = team

    def simulate(self,actions):
        """
        模拟执行一系列动作。
        参数:
        actions (list): 要执行的动作列表。
        {Name:actionName}
        """
        action = iter(actions)
        self.team.swqp(next(action))
        self.team.current_frame = 0 # 初始化当前帧数
        try:
            self.next_character = next(action)
        except StopIteration:
            self.next_character = None
            print("最后一个动作开始执行")

        while True:
            if self._update(self.target,action):
                break

    def _update(self, target, action):
        self.team.update(target)
        self.target.update()

        if self.next_character is not None and self.team.swqp(self.next_character):
            print("切换成功")
            try:
                self.next_character = next(action)
            except StopIteration:
                self.next_character = None
                print("最后一个动作开始执行")

        if self.next_character is None and self.team.current_character.state == CharacterState.IDLE:
            print("动作执行完毕")
            return True
        return False
        
    def save_simulation(self,filename):
        data = {
            'characters': [char.to_dict() for char in self.team.team]
        }
        with open('./data/'+filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_simulation(self,filename):
        with open('./data/'+filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        team = []
        for char_data in data['characters']:
            # 创建角色
            character = CharacterClassMap[char_data['id']](  # 需要建立角色类映射
                level=char_data['level'],
                skill_params=char_data['skill_params']
            )
            
            # 创建武器
            if char_data['weapon']:
                weapon_class = WeaponClassMap[char_data['weapon']['id']]  # 需要武器类映射
                weapon = weapon_class(
                    character=character,
                    level=char_data['weapon']['level'],
                    lv=char_data['weapon']['lv']
                )
                character.setWeapon(weapon)
            
            # 创建圣遗物
            if char_data['artifacts']:
                artifacts = []
                for arti_data in char_data['artifacts']['set']:
                    artifacts.append(Artifact(
                        name=arti_data['name'],
                        piece=ArtifactPiece[arti_data['piece']],
                        main=arti_data['main'],
                        sub=arti_data['sub']
                    ))
                am = ArtifactManager(artifacts, character)
                character.setArtifact(am)
            
            team.append(character)
        
        self.team = Team(team)
