from setup.DamageCalculation import DamageType
from setup.Event import EventBus, EventHandler, EventType
from setup.Logger import get_emulation_logger
from .weapon import Weapon

claymore = ['螭骨剑','焚曜千阳']

class SerpentSpine(Weapon):
    ID = 1
    def __init__(self,character,level,lv):
        super().__init__(character,self.ID,level,lv)
        self.skill_param = [6,7,8,9,10]

    def skill(self):
        attributePanel = self.character.attributePanel
        attributePanel['伤害加成'] += 5*self.skill_param[self.lv-1]

# 焚曜千阳
class AThousandBlazingSuns(Weapon, EventHandler):
    ID = 92
    def __init__(self, character, level, lv):
        super().__init__(character, self.ID, level, lv)
        self.skill_param = {
            '暴击伤害': [20, 25, 30, 35, 40],
            '攻击力%': [28, 35, 42, 49, 56]
        }
        self.fen_guang_active = False
        self.fen_guang_duration = 0      # 剩余持续时间（帧）
        self.fen_guang_cooldown = 0      # 剩余冷却时间（帧）
        self.max_extensions = 0          # 已延长时间（帧）
        self.last_extension_frame = 0    # 上次延长的时间戳（帧）
        self.nightsoul_active = False    # 夜魂加持状态
        
        # 注册事件监听
        EventBus.subscribe(EventType.BEFORE_SKILL, self)
        EventBus.subscribe(EventType.BEFORE_BURST, self)
        EventBus.subscribe(EventType.BEFORE_DAMAGE, self)
        EventBus.subscribe(EventType.BEFORE_NIGHTSOUL_BLESSING, self)
        EventBus.subscribe(EventType.AFTER_NIGHTSOUL_BLESSING, self)

    def handle_event(self, event):
        # 仅处理当前角色的相关事件
        if event.data['character'] != self.character:
            return
            
        # 触发焚光（技能/爆发前触发）
        if event.event_type in (EventType.BEFORE_SKILL, EventType.BEFORE_BURST):
            if self._can_activate():
                self._activate_fen_guang(event.frame)
                
        # 延长持续时间
        elif event.event_type == EventType.BEFORE_DAMAGE:
            if self.fen_guang_active and self._is_valid_damage(event.data['damage']):
                if event.frame - self.last_extension_frame >= 60:  # 1秒冷却
                    self._extend_fen_guang(event.frame, 120)  # 延长2秒
                    
        # 夜魂状态更新
        elif event.event_type == EventType.BEFORE_NIGHTSOUL_BLESSING:
            self.nightsoul_active = True
            get_emulation_logger().log_effect(f"{self.character.name}的焚曜千阳获得夜魂加持")
        elif event.event_type == EventType.AFTER_NIGHTSOUL_BLESSING:
            self.nightsoul_active = False
            get_emulation_logger().log_effect(f"{self.character.name}的焚曜千阳失去夜魂加持")

    def _can_activate(self):
        """判断是否满足触发条件"""
        return self.fen_guang_cooldown <= 0 and not self.fen_guang_active

    def _is_valid_damage(self, damage):
        """检查是否为普攻/重击元素伤害"""
        return (
            damage.damageType in (DamageType.NORMAL, DamageType.CHARGED) and 
            damage.element[0] != '物理'  # 通过元组第一个元素判断元素类型
        )

    def _activate_fen_guang(self, current_frame):
        """激活焚光效果"""
        lv = self.lv - 1
        get_emulation_logger().log_effect(f"{self.character.name}的焚曜千阳激活焚光效果")
        base_cd = self.skill_param['暴击伤害'][lv]
        base_atk = self.skill_param['攻击力%'][lv]
        
        # 夜魂加持提升
        if self.nightsoul_active:
            base_cd *= 1.75
            base_atk *= 1.75
            
        # 应用属性
        self.character.attributePanel['暴击伤害'] += base_cd
        self.character.attributePanel['攻击力%'] += base_atk
        
        # 初始化状态
        self.fen_guang_active = True
        self.fen_guang_duration = 360  # 6秒基础持续时间
        self.fen_guang_cooldown = 600  # 10秒冷却
        self.max_extensions = 0
        self.last_extension_frame = current_frame

    def _extend_fen_guang(self, current_frame, frames):
        """延长焚光持续时间"""
        if self.max_extensions < 360:  # 最多延长6秒
            get_emulation_logger().log_effect(f"{self.character.name}的焚曜千阳延长焚光持续时间 {frames/60:.1f}秒")
            self.fen_guang_duration += frames
            self.max_extensions += frames
            self.last_extension_frame = current_frame

    def update(self, target):
        if not self.character.on_field:
            return
        # 全局冷却计时
        if self.fen_guang_cooldown > 0:
            self.fen_guang_cooldown -= 1
            
        # 仅在前台或夜魂状态下计时
        if not self.fen_guang_active:
            return
            
        if self.character.on_field or self.nightsoul_active:
            self.fen_guang_duration -= 1
            if self.fen_guang_duration <= 0:
                self._deactivate_fen_guang()

    def _deactivate_fen_guang(self):
        """移除焚光效果"""
        lv = self.lv - 1
        get_emulation_logger().log_effect(f"{self.character.name}的焚曜千阳焚光效果结束")
        base_cd = self.skill_param['暴击伤害'][lv]
        base_atk = self.skill_param['攻击力%'][lv]
        
        if self.nightsoul_active:
            base_cd *= 1.75
            base_atk *= 1.75
            
        self.character.attributePanel['暴击伤害'] -= base_cd
        self.character.attributePanel['攻击力%'] -= base_atk
        
        # 重置状态
        self.fen_guang_active = False
        self.fen_guang_duration = 0
        self.max_extensions = 0
