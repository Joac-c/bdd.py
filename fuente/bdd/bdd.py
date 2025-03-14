from typing import Protocol as Protocolo, Self, List, Dict, TypeAlias as AliasDeTipo, Optional as Opcional, Unpack, Any
from mysql.connector import connect
from mysql.connector.cursor import MySQLCursorBufferedDict, MySQLCursorBufferedNamedTuple
from mysql.connector.errors import DatabaseError as ErrorMySQL, ProgrammingError as ErrorMalaSintaxisSQL
from solteron import Solteron


from bdd.tipos import *
from bdd.errores import *
from bdd.utiles import *

@runtime_checkable
class ProtocoloBaseDeDatos(Protocol):
    def DESCRIBE(self: Self, base_de_datos:str, tabla :str) -> Self: ...
    
    def SELECT(self: Self, *columnas : str) -> Self: ...
    def FROM(self: Self, tabla : str) -> Self: ...
    def JOIN(self: Self, tipo: TipoUnion, tabla: str, columna_origen : str, columna_destino: str) -> Self: ...
    def WHERE(self: Self, **columnas : Unpack[dict[str,any]]) -> Self: ...
    def LIMIT(self: Self, desplazamiento : int, cantidad: int) -> Self: ...
    
    def UPDATE(self: Self, tabla: str) -> Self: ...
    def INSERT(self: Self, tabla: str) -> Self: ...
    def SET(self: Self, **valores : Unpack[dict[str,any]]) -> Self: ...

    def Ejecutar(self: Self) -> Self :...
    def DevolverUnResultado(self: Self) -> Resultado :...
    def DevolverResultados(self: Self) -> tuple[Resultado] :...
    def DevolverIdUltimaInsercion(self:Self) -> int :...

class BaseDeDatos_MySQL: ...




Resultado : AliasDeTipo = dict[str,Any]




class InstruccionPrincipal():
    ''' 
        Clase que permite definir la clausula principal de una consulta SQL. 
        Altamente acoplada con la clase Consulta y dependiente de la misma.    
    '''

    _slots__ = \
    (
        '__instruccion'
    )
    def __init__(self):
        self.__instruccion = ''
    
    def chequearOcupado(self):
        if self.__instruccion: raise ErrorMalaSintaxisSQL("La clausula principal ya ha sido definida.")
    def esInsert(self):
        self.__instruccion = 'INSERT'
    def esSelect(self):
        self.__instruccion = 'SELECT'
    def esDelete(self):
        self.__instruccion = 'DELETE'
    def esUpdate(self):
        self.__instruccion = 'UPDATE'
    def construirConsulta(self, parametrosPrincipales, condicion, union, limite):
        if not self.__instruccion: raise ErrorMalaSintaxisSQL("No se ha definido una clausula principal.")
        if self.__instruccion == 'INSERT':
            if condicion or union or limite: raise ErrorMalaSintaxisSQL("Las instrucciones INSERT no pueden tener clausulas WHERE, JOIN o LIMIT.")
        return self.__instruccion + '\n' + parametrosPrincipales + condicion + union + limite + ';'


class Consulta():
    '''
    Clase que permite generar consultas SQL de forma programática. Las consultas se construyen concatenando
    las clausulas principales (Select, Delete, Insert, Update) y las clausulas secundarias (Where, Join). Luego
    se espera que el objeto sea convertido a string para obtener la consulta SQL.


    METODOS PUBLICOS
    - Select(tabla : str, columnas : list[str] columnasSecundarias: Optional[Dict[str, List[str]] ] = {}) -> Self
    - Delete(tabla : str) -> Self
    - Insert(tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self
    - Update(tabla : str, **asignaciones : Unpack[dict[str, Any]]) -> Self
    - Where(tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]) -> Self
    - Join(tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER) -> Self
    - Limit(desplazamiento: int  , limite : int) -> Self
    Aclaracion: Los metodos From, Set y Limit no son metodos publicos, ya que son llamados internamente por los metodos que invocan clausulas principales.

    ATRIBUTOS PUBLICOS
    - TipoCondicion: Enumeracion que contiene los tipos de condiciones posibles.
    - TipoUnion: Enumeracion que contiene los tipos de joins posibles.

    EJEMPLOS DE USO:


    > consulta = Consulta().Select(tabla='Usuarios', columnas=['nombreUsuario', 'correo']).Where(id=1).Limit(10, 5)
    > print(consulta)


    SELECT 
    Usuarios.nombreUsuario, Usuarios.correo
    FROM Usuarios
    WHERE Usuarios.id = 1
    LIMIT 10, 5
    ;

    > consulta = Consulta().Delete(tabla='Usuarios').Where(id=1)
    > print(consulta)

    DELETE 
    FROM Usuarios
    WHERE Usuarios.PRIMARY_KEY != 'NULL'
    AND Usuarios.id = 1
    ;

    > consulta = Consulta().Insert(tabla='Usuarios', nombreUsuario='Juan')

    > consulta = Consulta().Select(tabla='Usuarios', columnas=['nombreUsuario', 'correo'], columnasSecundarias={'Discos': 'autor'})
    > consulta.Join(tablaSecundaria='Discos', columnaPrincipal='esPremium', columnaSecundaria ='esPremium', tipoUnion=TipoUnion.INNER)
    > print(consulta)

    SELECT Usuarios.nombreUsuario, Usuarios.correo, Discos.a, Discos.u, Discos.t, Discos.o, Discos.r
    FROM Usuarios
    INNER JOIN Discos ON Usuarios.esPremium = Discos.esPremium
    ;

    CASOS DE ERROR:

    La clase levanta errores de tipo ErrorMalaSintaxisSQL en los siguientes casos:
    - Se intenta invocar una clausula principal (Select, Delete, Insert, Update) más de una vez.
    - Se intenta convertir a string sin clausula principal
    - Se intenta pedir columnas secundarias de una tabla que no ha sido unida.

    La clase levanta errores de tipo ErrorMalaSolicitud en los siguientes casos:

    CASOS
    
    
    '''

    _slots__ = \
    (   '__parametros_principales',
        '__instruccionPrincipal',
        '__tabla_principal',
        '__tablas_secundarias',
        '__condicion',
        '__union',
        '__limite')

    

    def __init__(self):
        self.__instruccionPrincipal = InstruccionPrincipal()
        self.__parametros_principales = ''
        self.__condicion = ''
        self.__union = ''
        self.__limite = ''

        self.__tabla_principal = ''
        self.__tablas_secundarias = {}

    def Select(self, tabla : str, columnas : list[str], columnasSecundarias: Optional[dict[str, list[str]] ] = {}) -> Self:
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esSelect()
        self.__parametros_principales = self.etiquetar(tabla, columnas)
        for t2, c2 in columnasSecundarias.items():
            self.__tablas_secundarias[t2] = 0
            self.__parametros_principales += ', ' + self.etiquetar(t2, c2) 
        self.__parametros_principales += '\n'
        self.__From(tabla)
        return self
    def Delete(self, tabla : str):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esDelete()
        self.__From(tabla)
        self.Where(TipoCondicion.NO_ES, id = None)
        return self
    def Insert(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esInsert()
        self.__parametros_principales = 'INTO ' + tabla + '\n'
        self.__Set(**asignaciones)
        return self
    def Update(self, tabla : str, **asignaciones : Unpack[dict[str, Any]]):
        self.__tabla_principal = tabla
        self.__instruccionPrincipal.esUpdate()
        self.__parametros_principales = tabla + '\n'
        self.__Set(**asignaciones)
        self.Where(TipoCondicion.NO_ES, id = None)

        return self
    def Where(self, tipoCondicion : TipoCondicion = TipoCondicion.IGUAL , **columnaValor : Unpack[dict[str, Any]]):
        condiciones : str = '   AND '.join(f"{self.etiquetar(self.__tabla_principal, [columna]) } {tipoCondicion} {self.adaptar(valor)}" for columna, valor in columnaValor.items())
        if not self.__condicion: self.__condicion = f'WHERE {condiciones}\n'
        else: self.__condicion += f' AND {condiciones}\n'
        return self

    
    def Join(self,   tablaSecundaria, columnaPrincipal, columnaSecundaria, tipoUnion : TipoUnion = TipoUnion.INNER):
        self.__tablas_secundarias[tablaSecundaria] = 1
        nuevoJoin : str = tipoUnion +  ' JOIN ' + tablaSecundaria + ' ON ' + self.etiquetar(self.__tabla_principal, [columnaPrincipal]) + ' = ' + self.etiquetar(tablaSecundaria, [columnaSecundaria]) + '\n'
        self.__union += nuevoJoin        
        return self
    
    def Limit(self, desplazamiento: int  , limite : int):
        if self.__limite : raise ErrorMalaSintaxisSQL("La clausula LIMIT ya ha sido definida.")
        self.__limite  =  'LIMIT ' + str(desplazamiento) + ', ' + str(limite) + '\n'
        return self
    def __From(self, tabla : str):
        self.__parametros_principales += 'FROM ' + tabla + '\n'
        return self
    def __Set(self, **columnaValor : Unpack[dict[str, Any]]):
        asignaciones = ', '.join(f"{self.etiquetar(self.__tabla_principal, [columna]) } = {self.adaptar(valor)}" for columna, valor in columnaValor.items())
        self.__parametros_principales += f'SET {asignaciones}\n'
        return self

    
    
    def etiquetar(self, tabla: str, columnas : list[str]):
        # Recibe una tabla y columnas. devuelve cada columna en el namespace de la tabla 
        return ', '.join([tabla + '.' + columna  for columna in columnas])

    def adaptar(self, valor : Any) -> str:
        #En caso de que el valor sea de un tipo estpecial debe convertirse a string fuera del llamado para que la consulta no falle
        if not valor:
            return "NULL"
        if type(valor) == int:
            return str(valor)
        else:
            return "'" + str(valor) + "'"

    def reiniciar(self):
        self.consulta = ''
    
    def __str__(self):
        if not self.__parametros_principales: raise ErrorMalaSintaxisSQL("No se ha definido una clausula principal.") 
        for tabla, valor in self.__tablas_secundarias.items():
            if valor == 0:
                raise ErrorMalaSintaxisSQL(f"La tabla {tabla} no ha sido unida.")
        
        return self.__instruccionPrincipal.construirConsulta(self.__parametros_principales, self.__condicion, self.__union, self.__limite)
        


class ConfigBDDMysql(metaclass=Solteron):


    _slots__ = \
    (
        '__HOST',  
        '__USUARIO',  
        '__CONTRASENA',  
        '__NOMBRE_BDD'

    )


    @property
    def PARAMETROS_CONEXION(self) -> dict: 
        return \
        {
            "host" : self.__HOST,
            "user" : self.__USUARIO,
            "password" : self.__CONTRASENA,
            "database" : self.__NOMBRE_BDD,
            "use_pure" : False
        }

    @property
    def OPCION_CURSOR(self) -> dict:
        return \
        {
           "dictionary" : True,
           "named_tuple" : False,   
        }




class BaseDeDatos_MySQL():
    _slots__ = \
    (
        "__config",
        "__conexion",
        "__cursor"
    )
    def __init__(self, configuracion : ConfigBDDMysql = None) -> None:
        self.__conexion = None
        self.__cursor = None
        self.configurar(configuracion)
    
    def configurar(self, configuracion : ConfigBDDMysql = None) -> None:
        if configuracion:
            self.__config = configuracion
            return self
        # Agregar comportamiento usando las variables de ambiente

    def conectar(self) -> Self:
        if self.__conexion: return self
        self.__conexion = connect(**self.__config.PARAMETROS_CONEXION)
        self.__cursor = self.__conexion.cursor(buffered=True, **self.__config.OPCION_CURSOR)
        return self

    def desconectar(self) -> None:
        if self.__cursor: self.__cursor.close()
        if self.__conexion: self.__conexion.close()
        self.__cursor = None
        self.__conexion = None
    
    def reconectar(self) -> Self:
        self.desconectar()
        self.conectar()
        return self
    
    def __exit__(self, exc_type,excl_val,exc_tb) -> None:
        # ###print(f"[DEBUG] Saliendo {self.__cursor=}{self.__conexion=}{self.__pool=}")
        self.desconectar()

   

    def ejecutar(self, consulta : str | Consulta) -> Opcional[list[Resultado]] :
        if type(consulta) == Consulta:
            consulta = str(consulta)
        try:
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except ErrorBDD as e:
            ###print(f"[ERROR] {e}")
            self.reconectar()
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except AttributeError as e:
            ###print(f"[ERROR] {e}")
            self = BaseDeDatos_MySQL()
            self.conectar()
            self.__cursor.execute(consulta)
            self.__conexion.commit()
        except Exception as f:
            raise type(f)(f"No se pudo completar la consulta.\n Es probable que la consulta incluya carácteres prohibidos. \n {consulta.encode('utf-8').decode('unicode_escape')}\n") from f
        return self
   
    def devolverResultados(self, cantidad : Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        resultados = self.__cursor.fetchall()
        
        if not resultados: return None
        elif cantidad is None: return resultados
        elif cantidad == 0: return []
        elif cantidad > 0: return resultados[0:cantidad-1]
        else: raise IndexError("Se solicitó una cantidad negativa de resultados, lo cual es un sinsentido.")
    def devolverUnResultado(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve el primer resultado de la última consulta.
        """
        return self.__cursor.fetchone()
        
    # Estados
    def estaConectado (self):
            return self.__conexion.is_connected() if self.__conexion else False



  # with BaseDeDatos() as bdd
    def __enter__(self) -> 'BaseDeDatos_MySQL':
        if self.__conexion is None:
            return self.conectar()
        # ###print(f"[DEBUG] Entrando {self.__cursor=}{self.__conexion=}{self.__pool=}")
        return self

    def __exit__(self, exc_type,excl_val,exc_tb) -> None:
        # ###print(f"[DEBUG] Saliendo {self.__cursor=}{self.__conexion=}{self.__pool=}")
        self.desconectar()

