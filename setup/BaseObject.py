from setup.Event import DamageEvent, EventBus
from setup.Team import Team
from setup.Tool import GetCurrentTime


class baseObject:
    def __init__(self,name, life_frame = 0):
        self.name = name

        self.current_frame = 0
        self.life_frame = life_frame

    def apply(self):
        Team.add_object(self)

    def update(self,target):
        self.current_frame += 1
        if self.current_frame >= self.life_frame:
            self.on_finish(target)
            Team.remove_object(self)

    def on_finish(self,target):
        ...
           
class ArkheObject(baseObject):
    def __init__(self, name, character, arkhe_type, damage, life_frame=0):
        super().__init__(name+':'+arkhe_type, life_frame)
        self.character = character
        self.arkhe_type = arkhe_type
        self.damage = damage

    def on_finish(self, target):
        event = DamageEvent(self.character, target, self.damage, GetCurrentTime())
        EventBus.publish(event)
        print(f'{self.name}对{target.name}造成{self.name} {self.damage.damage}点伤害')
