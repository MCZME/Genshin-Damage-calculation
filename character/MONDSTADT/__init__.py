__all__ = ['mondstadt_table']

mondstadt_table = {}

def _add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    mondstadt_table[name] = table

from character.MONDSTADT.BENNETT import bennett_table
_add('班尼特', 'Bennett', bennett_table)