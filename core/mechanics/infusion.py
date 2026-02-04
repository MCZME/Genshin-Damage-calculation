from core.tool import GetCurrentTime

class Infusion:
    def __init__(self, attach_sequence=[1, 0, 0], interval=2.5*60, max_attach=8):
        self.attach_sequence = attach_sequence
        self.sequence_pos = 0
        self.last_attach_time = 0
        self.interval = interval
        self.max_attach = max_attach
        self.infusion_count = 0

    def apply_infusion(self):
        current_time = GetCurrentTime()
        should_attach = False
        
        if self.sequence_pos < len(self.attach_sequence):
            should_attach = self.attach_sequence[self.sequence_pos] == 1
            self.sequence_pos += 1
        else:
            self.sequence_pos = 0
            should_attach = self.attach_sequence[self.sequence_pos] == 1
            self.sequence_pos += 1
        
        self.infusion_count += 1
        
        if current_time - self.last_attach_time >= self.interval:
            should_attach = True
            self.infusion_count = 0
            self.last_attach_time = current_time
        
        if self.infusion_count > self.max_attach:
            should_attach = False
        
        return 1 if should_attach else 0
