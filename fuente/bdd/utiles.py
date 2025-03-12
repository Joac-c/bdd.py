from json import dumps,loads
from re import match,findall
from secrets import token_urlsafe

from bdd.tipos import *
from sobrecargar import sobrecargar

def formatearValorParaSQL(valor: Any, html : bool = False) -> str:
    """
    Formatea un valor de Python a una representación adecuada para SQL.
    """
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, (list, tuple)):
        return f"'[{','.join(f"\"{str(v)}\"" for v in valor)}]'"
    if isinstance(valor, Decimal):
        return str(valor.to_eng_string())
    if isinstance(valor, (date, datetime, time)):
        return f"'{valor.isoformat()}'"
    if isinstance(valor, dict):
        return f"'{dumps(valor)}'"
    if isinstance(valor, bytes):
        return f"X'{valor.hex()}'"
    if isinstance(valor, Enum):
        return str(valor.value) if isinstance(valor.value, int) else f"'{valor.name}'"
    if isinstance(valor, str):
        return f"'{valor.replace("'", "''")}'"
        
    return f"'{str(valor).replace("'", "''")}'"

def atributoPublico(nombreAtributo: str) -> str:
    return nombreAtributo.replace('__','',1)

def atributoPrivado(obj: Any, nombreAtributo: str) -> str:
    return f"_{obj.__class__.__name__}__{atributoPublico(nombreAtributo)}"
