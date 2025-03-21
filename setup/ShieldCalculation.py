from setup.Event import EventBus, EventHandler, EventType, ShieldEvent

class Shield:
    def __init__(self, base_value, base_multiplier, element: str):
        self.base_value = base_value
        self.base_multiplier = base_multiplier
        self.element = element
        self.shield_value = 0
        self.base_value = '生命值'  # 默认为生命值基础
        self.absorption = 1.0  # 基础吸收系数

    def set_source(self, source):
        self.source = source

    def set_target(self, target):
        self.target = target

class ShieldCalculation:
    def __init__(self, source, target, shield: Shield):
        self.source = source
        self.target = target
        self.shield = shield

    def get_hp(self):
        """获取生命值"""
        attribute = self.source.attributePanel
        hp0 = attribute['生命值']
        hp1 = hp0 * attribute['生命值%'] / 100 + attribute['固定生命值']
        return hp0 + hp1

    def get_def(self):
        """获取防御力"""
        attribute = self.source.attributePanel
        def0 = attribute['防御力']
        def1 = def0 * attribute['防御力%'] / 100 + attribute['固定防御力']
        return def0 + def1

    def get_attack(self):
        """获取攻击力"""
        attribute = self.source.attributePanel
        atk0 = attribute['攻击力']
        atk1 = atk0 * attribute['攻击力%'] / 100 + attribute['固定攻击力']
        return atk0 + atk1

    def get_shield_strength_bonus(self):
        """获取护盾强效加成"""
        return self.source.attributePanel.get('护盾强效', 0) / 100

    def get_elemental_resistance(self):
        """获取目标元素抗性"""
        return self.target.current_resistance.get(self.shield.element, 10) / 100

    def calculation_by_hp(self):
        base_value = self.get_hp() * self.shield.base_multiplier / 100
        shield_value = base_value * (1 + self.get_shield_strength_bonus())
        shield_value *= (1 - self.get_elemental_resistance())
        self.shield.shield_value = shield_value * self.shield.absorption

    def calculation_by_def(self):
        base_value = self.get_def() * self.shield.base_multiplier / 100
        shield_value = base_value * (1 + self.get_shield_strength_bonus())
        shield_value *= (1 - self.get_elemental_resistance())
        self.shield.shield_value = shield_value * self.shield.absorption

    def calculation_by_attack(self):
        base_value = self.get_attack() * self.shield.base_multiplier / 100
        shield_value = base_value * (1 + self.get_shield_strength_bonus())
        shield_value *= (1 - self.get_elemental_resistance())
        self.shield.shield_value = shield_value * self.shield.absorption

class ShieldCalculationEventHandler(EventHandler):
    def handle_event(self, event: ShieldEvent):
        if event.event_type == EventType.BEFORE_SHIELD_CREATION:
            calculation = ShieldCalculation(
                event.data['source'],
                event.data['target'],
                event.data['shield']
            )
            
            if event.data['shield'].base_value == '生命值':
                calculation.calculation_by_hp()
            elif event.data['shield'].base_value == '防御力':
                calculation.calculation_by_def()
            elif event.data['shield'].base_value == '攻击力':
                calculation.calculation_by_attack()
            
            # 发布护盾生成后事件
            after_event = ShieldEvent(
                source=event.data['source'],
                target=event.data['target'],
                shield=event.data['shield'],
                frame=event.frame,
                before=False
            )
            EventBus.publish(after_event)
