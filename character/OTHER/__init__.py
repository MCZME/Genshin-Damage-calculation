__all__ = ['sumeru_character']

def add(name,character,table):
    __all__.append(character)
    table['skip'] = {'时间':9999}
    other_character[name] = table

other_character = {}

from .Skirk import skirk_table
add('丝柯克', '', skirk_table)
