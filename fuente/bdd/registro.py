from bdd.tipos import *
from bdd.utiles import *
from bdd.bdd import ProtocoloBaseDeDatos



class Registro: ...
class Registro:
    __slots__ = (
        '__bdd',
        '__id',
    )

    __bdd : ProtocoloBaseDeDatos
    __id : int

    @property
    def id(self):
        return self.__id
    
    def __new__(cls, *posicionales,**nominales):
        obj = super(Registro, cls).__new__(cls)
        obj.__tabla = cls.__name__
        return obj        

    @sobrecargar
    def __init__(self, bdd : ProtocoloBaseDeDatos, valores : dict):
        for atributo in self.__slots__:
            nombre = atributoPublico(atributo)
            valor_SQL : Any = valores.get(nombre,None)
            if valor_SQL is not None:
                valor = valor_SQL
                tipo_esperado : type = self.__class__.__annotations__[atributo]
                if issubclass(tipo_esperado, Decimal):
                    valor : Decimal = Decimal(valor_SQL)
                elif issubclass(tipo_esperado, dict):
                    valor : dict = loads(valor_SQL)
                elif issubclass(tipo_esperado,bool):
                    valor : bool = bool(valor_SQL)
                elif issubclass(tipo_esperado,EnumSQL):
                    valor : tipo_esperado = tipo_esperado.desdeCadena(valor_SQL)
                else:
                    valor = valor_SQL
                setattr(self, atributoPrivado(self,atributo) if '__' in atributo else atributo, valor)

    @sobrecargar
    def __init__(self, bdd : ProtocoloBaseDeDatos, id : int):
        resultado : Resultado
        atributos : tuple[str] = (atributoPublico(atr) for atr in self.__slots__ if atr not in ('__bdd','__tabla'))
        
        with bdd as bdd:
            resultado = bdd\
                        .SELECT(*atributos)\
                        .FROM(self.tabla)\
                        .WHERE(id=id)\
                        .Ejecutar()\
                        .DevolverUnResultado()

        self.__init__(
            bdd,
            resultado
        )
        self.__id = id

    def guardar(self) -> int:
        """Guarda el registro en la tabla correspondiente.
        Si tiene id, se edita un registro existente, 
        de lo contrario se agrega uno nuevo.   

        Devuelve:
        :arg Id int:
            El Id del registro.           

        Levanta:  
        :arg Exception: Propaga errores de la conexión con la BDD  
        :arg Exception: Levanta error si al editar la base con coinciden los id
        """
        match self.__id:
            case None:
                self.__id : int = self.__crear()
            case _: 
                self.__editar()

        return self.__id
    

    def __crear(self) -> int: 
        """Crea un nuevo registro en la tabla correspondiente""" 

        atributos : tuple[str] = (atr for atr in self.__slots__ if '__' not in atr)
        ediciones : dict[str,Any] = {
            atributo : getattr(self,atributo)
            for atributo in atributos
        }
    
        with self.__bdd as bdd:
            id : int = bdd\
                        .UPDATE(self.tabla)\
                        .SET(**ediciones)\
                        .WHERE(id=self.__id)\
                        .Ejecutar()\
                        .DevolverIdUltimaInsercion()
            self.__id = id
        
        return self.__id
    
    def __editar(self) -> None: 
        """
        Edita un registro ya existente, dado por el ID, en la tabla correspondiente.
        """


        atributos : tuple[str] = (atr for atr in self.__slots__ if '__' not in atr)
        ediciones : dict[str,Any] = {
            atributo : getattr(self,atributo)
            for atributo in atributos
        }

        with self.__bdd as bdd:
            bdd\
                .UPDATE(self.tabla)\
                .SET(**ediciones)\
                .WHERE(id=self.__id)\
                .Ejecutar()
