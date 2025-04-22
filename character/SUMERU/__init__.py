__all__ = ['sumeru_character']

def add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    sumeru_character[name] = table

sumeru_character = {}

from .Nahida import nahida_table
add('纳西妲','',nahida_table)