from setup.BaseClass import CharacterState, SkillBase
from .character import Character

class RuishouDenggaolou(SkillBase):
    def __init__(self):
        super().__init__(
            name="瑞兽登高楼",
            total_frames=120,  # 假设总帧数为120帧（2秒）
            interruptible=False  # 假设技能不可打断
        )
        self.has_jumped = False  # 是否已经腾跃

    def on_frame_update(self):
        if self.current_frame < 60:
            # 前60帧为扑击阶段
            if self.current_frame == 30:
                print("🦁 嘉明向前扑击！")
        elif self.current_frame == 60:
            # 第60帧腾跃至空中
            print("🦁 嘉明高高腾跃至空中！")
            self.has_jumped = True
        elif self.current_frame > 60 and self.has_jumped:
            # 腾跃后等待下落攻击
            if self.current_frame == 90:
                print("🦁 嘉明准备施展下落攻击-踏云献瑞！")

    def on_finish(self):
        if self.has_jumped:
            print("🦁 嘉明完成下落攻击-踏云献瑞！")
            self._perform_tayun_xianrui()

    def _perform_tayun_xianrui(self):
        # 计算伤害和生命值消耗
        damage = self.caster.attack * 2.5  # 假设伤害为基础攻击的2.5倍
        hp_cost = self.caster.hp * 0.1  # 消耗10%生命值，但最低保留10%
        final_hp_cost = min(hp_cost, self.caster.hp - self.caster.max_hp * 0.1)
        
        # 应用伤害和生命值消耗
        self.caster.hp -= final_hp_cost
        print(f"🔥 造成 {damage} 点无法被削魔覆盖的火元素伤害")
        print(f"❤️ 嘉明消耗了 {final_hp_cost} 点生命值，当前生命值：{self.caster.hp}/{self.caster.max_hp}")

    def on_interrupt(self):
        if self.has_jumped:
            print("💢 下落攻击被打断！")
        else:
            print("💢 扑击被打断！")

class GaMing(Character):
    ID = 78
    def __init__(self,level,skill_level):
        super().__init__(self.ID,level,skill_level)
        self.ruishou_denggaolou = RuishouDenggaolou()
        
    def _normal_attack_impl(self):
        ...

    def _heavy_attack_impl(self):
        ...

    def _elemental_skill_impl(self):
        if self.state == CharacterState.IDLE:
            self.state = CharacterState.CASTING
            self.ruishou_denggaolou.start(self)

    def _elemental_burst_impl(self):
        ...

    def update(self):
        super().update()
        if self.state == CharacterState.CASTING:
            if self.ruishou_denggaolou.update():
                self.state = CharacterState.IDLE
        