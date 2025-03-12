from bdd.tipos import *
from bdd.utiles import *
from bdd.bdd import ProtocoloBaseDeDatos
from bdd.registro import Registro

class Tabla(type):
    def __new__(mcs, nombre, bases, atributos):
        if Registro not in bases and nombre != 'Registro':
            bases = (Registro,) + bases
        
        cls = super().__new__(mcs, nombre, bases, atributos)
        
        cls.__tabla = nombre
        setattr(cls, "tabla", property(lambda cls : cls.__tabla))

        
        if not hasattr(cls, '__annotations__'):
            cls.__annotations__ = {}
        
        return cls

    def __init__(cls, nombre, bases, atributos): ...
        #print(cls.__slots__)

    def __call__(cls, bdd: ProtocoloBaseDeDatos, *posicionales, **nominales):


        slots :list[str] = []        
        anotaciones : dict[str,type] = {}
        with bdd as bdd:
            resultados = bdd.DESCRIBE(cls.__tabla).Ejecutar().DevolverResultados()
            
            for columna in resultados:
                nombre_campo = columna.get('Field')
                es_clave = columna.get('Key') == "PRI"
                #print(columna.get('Extra'))
                es_auto = "auto_increment" in columna.get("Extra", "").lower() or "default_generated" in columna.get("Extra", "").lower() or "auto_generated" in columna.get("Extra", "").lower()
                
                nombre_attr = f"__{nombre_campo}" if es_clave or es_auto else nombre_campo
                
                tipo = cls.__resolverTipo(columna.get('Type'), nombre_campo)
                
                if nombre_attr not in cls.__slots__:
                    slots.append(nombre_attr)
                anotaciones.update({
                    nombre_attr : tipo
                })
                
                
                if es_clave:
                    setattr(cls, nombre_campo, property(lambda self, name=nombre_campo: getattr(self, atributoPrivado(self,name))))
        
        
        cls.__slots__ = cls.__slots__ + tuple(slots)
        cls.__annotations__.update(anotaciones)
        print(cls.__slots__)
        instancia = super().__call__(bdd, *posicionales, **nominales)
        setattr(instancia, atributoPrivado(instancia,"__bdd"),bdd)
        return instancia
    
    @classmethod
    def __resolverTipo(cls, tipo_sql: str, nombre_columna: Optional[str]) -> type:
        """
        Deduce y devuelve un tipo de Python en base al tipo declarado en MySQL para la columna.
        Si encuentra un ENUM, crea un enum de Python y lo guarda como una constante de la clase.
        
        Parámetros:
            :arg tipo_sql str: El tipo definido en MySQL
            :arg nombre_columna Optional[str]: El nombre de la columna (útil para enums)
        
        Devuelve:
            :arg tipo `type`: el tipo python correspondiente (o `Any`)
        """
        tipo_declarado: Optional[Match[AnyStr]] = match(r'([a-z]+)(\(.*\))?', tipo_sql.lower())
        if not tipo_declarado:
            return Any

        tipo_base: str = tipo_declarado.group(1)
        parametros: str = tipo_declarado.group(2) if tipo_declarado.group(2) else ""
        tipo_completo: str = tipo_base + parametros

        tipos: dict[str, type] = {
            'tinyint': int,
            'smallint': int,
            'mediumint': int,
            'int': int,
            'bigint': int,
            'float': float,
            'double': float,
            'decimal': Decimal,
            'datetime': datetime,
            'timestamp': datetime,
            'date': date,
            'time': time,
            'char': str,
            'varchar': str,
            'text': str,
            'mediumtext': str,
            'longtext': str,
            'tinytext': str,
            'boolean': bool,
            'bool': bool,
            'tinyint(1)': Union[bool,int],
            'blob': Union[bytes,bytearray],
            'mediumblob': Union[bytes,bytearray],
            'longblob': Union[bytes,bytearray],
            'tinyblob': Union[bytes,bytearray],
            'binary': Union[bytes,bytearray],
            'varbinary': Union[bytes,bytearray],
            'json': Union[dict,list,tuple],
        }

        
        if tipo_base == 'enum':
            valores_enum: list[Any] = findall(r"'([^']*)'", tipo_sql)
            dicc_enum: dict[str, int] = {'_invalido': 0}
            for i, val in enumerate(valores_enum, 1):   
                dicc_enum[val] = i
            
            nombre_enum: str = f"Tipo{nombre_columna.capitalize()}" if nombre_columna else f"__ENUM_{token_urlsafe(4)}"
            clase_enum: type = type(
                nombre_enum,
                (EnumSQL, Enum),
                dicc_enum
            )
            
            setattr(cls,nombre_enum,clase_enum)
            return clase_enum

        
        if tipo_completo in tipos:
            return tipos[tipo_completo]
        return tipos.get(tipo_base, Any)