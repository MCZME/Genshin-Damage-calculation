from setup.BaseClass import SkillBase
from setup.DamageCalculation import DamageType
from setup.Event import EventBus, EventType, GameEvent
from .character import Character,CharacterState

class RuishouDenggaolou(SkillBase):
    def __init__(self,lv):
        super().__init__(
            name="瑞兽登高楼",
            total_frames=120,  # 假设总帧数为120帧（2秒）
            lv=lv,
            element=("火",1)
        )
        self.damageMultipiler= [230.4,247.68,264.96,
                               288,305.28,322.56,345.6,
                               368.64,391.68,414.72,
                               437.76,460.8,518.4,547.2]
        self.has_jumped = False  # 是否已经腾跃

    def on_frame_update(self,target):
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
        damage = 2000  # 假设下落攻击造成2000点伤害
        final_hp_cost = 500  # 假设消耗500点生命值
        print(f"🔥 造成 {damage} 点无法被削魔覆盖的火元素伤害")
        print(f"❤️ 嘉明消耗了 {final_hp_cost} 点生命值")

    def on_interrupt(self):
        if self.has_jumped:
            print("💢 下落攻击被打断！")
        else:
            print("💢 扑击被打断！")

class NormalAttackSkill(SkillBase):
    def __init__(self,lv):
        self.segment_frames = [30, 40, 50, 60]  # 四段攻击的独立帧数
        
        # 计算总帧数（各段帧数之和）
        total_frames = sum(self.segment_frames)
        
        super().__init__(
            name="普通攻击",
            total_frames=total_frames,
            lv=lv,
            element=("物理",0),
            interruptible=True
        )
        self.damageMultipiler= [[83.86,90.68,97.51,
                                 107.26,114.08,121.88,132.61,
                                 143.34,154.06,165.76,177.46]]
        
        # 攻击阶段控制
        self.current_segment = 0               # 当前段数（0-based）
        self.segment_progress = 0              # 当前段进度帧数

    def start(self, caster,n):
        super().start(caster)
        self.current_segment = 0
        self.segment_progress = 0
        self.max_segments = min(n, 4)           # 实际攻击段数
        self.total_frames = sum(self.segment_frames[:self.max_segments])
        print(f"⚔️ 开始第{self.current_segment+1}段攻击")

    def update(self, target):
        self.current_frame += 1
        if self.on_frame_update(target):
            return True
        return False

    def on_frame_update(self,target): 
        # 更新段内进度
        self.segment_progress += 1
        
        # 检测段结束
        if self.segment_progress >= self.segment_frames[self.current_segment]:
            if self._on_segment_end(target):
                return True
        return False
    
    def on_finish(self): 
        pass 
        
    def _on_segment_end(self,target):
        """完成当前段攻击"""
        print(f"✅ 第{self.current_segment+1}段攻击完成")
        
        # 执行段攻击效果
        self._apply_segment_effect(target)
        
        # 进入下一段
        if self.current_segment < self.max_segments - 1:
            self.current_segment += 1
            self.segment_progress = 0
            print(f"⚔️ 开始第{self.current_segment+1}段攻击")
        else:
            self.on_finish()
            return True
        return False

    def _apply_segment_effect(self,target):
        
        # 发布伤害事件
        damage_event = GameEvent(
            EventType.BEFORE_DAMAGE,
            source=self.caster,
            target=target,
            damageType=DamageType.NORMAL,
            skill =self,
            damage = 0
        )
        EventBus.publish(damage_event)
        print(f"🎯 {self.caster.name} 对 {target.name} 造成了 {damage_event.data['damage']} 点伤害")

    def on_interrupt(self):
        print(f"💢 第{self.current_segment+1}段攻击被打断！")
        self.current_segment = self.max_segments  # 直接结束攻击链

    def getDamageMultipiler(self):
        return self.damageMultipiler[self.current_segment][self.lv-1]

class GaMing(Character):
    ID = 78
    def __init__(self,level,skill_params):
        super().__init__(self.ID,level,skill_params)
        self.Skill = RuishouDenggaolou(skill_params[1])
        self.Burst = RuishouDenggaolou(skill_params[2])
        self.NormalAttack = NormalAttackSkill(skill_params[0])
        
    def _normal_attack_impl(self,n):
        if self.state == CharacterState.IDLE:
            self.state = CharacterState.NORMAL_ATTACK
            self.NormalAttack.start(self,n)

    def _heavy_attack_impl(self):
        ...

    def _elemental_skill_impl(self):
        if self.state == CharacterState.IDLE:
            self.state = CharacterState.SKILL
            self.Skill.start(self)

    def _elemental_burst_impl(self):
        if self.state == CharacterState.IDLE:
            self.state = CharacterState.BURST
            self.Burst.start(self)

    def update(self,target):
        super().update(target)
        
        