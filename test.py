from core.dataHandler.Automator import SimAutomator, SimConfigAutomator
from main import init


if __name__ == '__main__':
    init()
    s = SimConfigAutomator("./data/草行久.json", ["team_data[2].weapon.name", ['息燧之笛','祭礼剑']])
    s.create_new_config()
    sim = SimAutomator('./data/草行久.json', s.new_config, 'team_data[2].weapon.name')
    sim.automate()