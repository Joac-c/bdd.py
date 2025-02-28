from typing import Protocol, runtime_checkable, Self, TypeAlias, Optional, Any, AnyStr, Unpack
from decimal import Decimal
from datetime import datetime,date,time,timedelta,timezone
from re import Match

from bdd.tipos.enum_sql import *

### BDD
Resultado : TypeAlias = dict[str,Any]

class TipoJoin(EnumSQL):
    LEFT_JOIN = 1
    RIGHT_JOIN = 2
    INNER_JOIN = 3
