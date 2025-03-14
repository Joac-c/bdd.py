from enum import Enum, EnumType as _EnumMeta, _EnumDict as _EnumDict

class EnumSQLMeta(_EnumMeta):
    """
    Metaclase para controlar las reglas personalizadas sobre las enumeraciones.
    Asegura que `_invalido` siempre tenga el valor 0 y ningún otro miembro lo tenga.
    """
    @classmethod
    def __prepare__(metacls, cls, bases, **kwds):
        """Copiado de enum.EnumType con la modificación de que esta metaclase no inhibe la herencia"""
        #metacls._check_for_existing_members_(cls, bases)
        enum_dict = _EnumDict()
        enum_dict._cls_name = cls
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        if first_enum is not None:
            enum_dict['_generate_next_value_'] = getattr(
                    first_enum, '_generate_next_value_', None,
                    )
        return enum_dict
    def __new__(cls, nombre, bases, diccionario):
        diccionario_enum = EnumSQLMeta.__prepare__(nombre,bases,**diccionario)
        diccionario_enum.update(diccionario)
        nueva_clase = _EnumMeta.__new__(cls, nombre, bases, diccionario_enum)

        # Verificar que la clase tiene '_invalido' con valor 0
        if '_invalido' not in nueva_clase.__members__: ...
            #raise ValueError(f"La enumeración {nombre} debe tener un miembro '_invalido' con valor 0.")
        
        # Verificar que ningún otro miembro tenga valor 0.
        for miembro in nueva_clase.__members__.values():
            if miembro.value == 0 and miembro.name != '_invalido':
                raise ValueError(f"{nombre} no puede tener otro miembro con valor 0 (reservado para '_invalido').")
        
        return nueva_clase

class EnumSQL(Enum,metaclass=EnumSQLMeta):
    """
    Clase base para enumeraciones que se lleva bien con SQL.
    """
    _invalido = 0  # Siempre debe ser 0 y no debe haber otro miembro con este valor.

    def __init__(self, *args, **kwds):
        pass

    @classmethod
    def desdeCadena(cls, cadena: str) -> 'EnumSQL':
        return cls.__members__.get(cadena, cls._invalido)

    def haciaCadena(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.haciaCadena()

    def __repr__(self) -> str:
        return self.haciaCadena()
