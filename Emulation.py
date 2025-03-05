from character.character import CharacterState
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
        self.next_character = next(action)

        while True:
            if self._update(self.target,action):
                break

    def _update(self, target, action):
        if self.next_character is not None and self.team.swqp(self.next_character):
            print("切换成功")
            try:
                self.next_character = next(action)
            except StopIteration:
                self.next_character = None
                print("最后一个动作开始执行")
        
        self.team.update(target)
        self.target.update()

        if self.next_character is None and self.team.current_character.state == CharacterState.IDLE:
            print("动作执行完毕")
            return True
        return False
        
    