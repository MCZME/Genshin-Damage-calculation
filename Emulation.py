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
        while True:
            self._update()

    def _update(self):
        pass
    