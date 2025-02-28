from bdd.tipos import *
from bdd.utiles import *
from bdd.tabla import Tabla  
from bdd.registro import Registro, BaseDeDatos_MySQL

class Discos(metaclass=Tabla):
    def devolverArtista(self):
        return self.idAutor

bdd = BaseDeDatos_MySQL()
usuario = Discos(bdd=bdd,id=2)

#print(usuario.nombreUsuario)
print(usuario.tabla)
print(usuario.id)
print(usuario.tipo.haciaCadena())
print(usuario.soporte)
print(usuario.devolverArtista())

print(f"{Discos.TipoSoporte.desdeCadena("DIGITAL").value=}")

