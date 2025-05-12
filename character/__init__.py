__all__ = ['Varesa','MAVUIKA','Iansan','CITLALI','XiangLing','CHEVREUSE','BENNETT',
         'Xilonen','KaedeharaKazuha','Furina','Neuvillette','KukiShinobu','XingQiu',
         'Nahida','Escoffier','Yelan','Skirk','Layla']

character_table = {}

def _add(table):
    for k, v in table.items():
        character_table[k] = v

from character.NATLAN import natlan_character
from character.NATLAN.VARESA import Varesa
from character.NATLAN.MAVUIKA import MAVUIKA
from character.NATLAN.IANSAN import Iansan
from character.NATLAN.CITLALI import CITLALI
from character.NATLAN.XILONEN import Xilonen
_add(natlan_character)
from character.LIYUE import liyue_table
from character.LIYUE.Xiangling import XiangLing
from character.LIYUE.Xingqiu import XingQiu
from character.LIYUE.Yelan import Yelan
_add(liyue_table)
from character.FONTAINE import fontaine_table
from character.FONTAINE.CHEVREUSE import CHEVREUSE
from character.FONTAINE.Furina import Furina
from character.FONTAINE.Neuvillette import Neuvillette
from character.FONTAINE.Escoffier import Escoffier
_add(fontaine_table)
from character.MONDSTADT import mondstadt_table
from character.MONDSTADT.BENNETT import BENNETT
_add(mondstadt_table)
from character.INAZUMA import inazuma_character
from character.INAZUMA.KaedeharaKazuha import KaedeharaKazuha
from character.INAZUMA.KukiShinobu import KukiShinobu
_add(inazuma_character)
from character.SUMERU import sumeru_character
from character.SUMERU.Nahida import Nahida
from character.SUMERU.Layla import Layla
_add(sumeru_character)
from character.OTHER import other_character
from character.OTHER.Skirk import Skirk
_add(other_character)

