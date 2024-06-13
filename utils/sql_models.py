from sqlalchemy import create_engine, Column, Integer, String,  ForeignKey, Text, DateTime, DECIMAL, Enum, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker  # Asumiendo uso de PostgreSQL para JSON
from utils.sql_connection import Base

class Categoria(Base):
    __tablename__ = 'Categorias'
    categoria_id = Column(Integer, primary_key=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)

    productos = relationship("Producto", back_populates="categoria")

class Producto(Base):
    __tablename__ = 'Productos'
    producto_id = Column(Integer, primary_key=True)
    nombre_producto = Column(String(255), nullable=False)  # Antes 'nombre_anuncio'
    marca = Column(String(255), nullable=False)
    modelo = Column(String(255), nullable=False)
    descripcion = Column(Text)
    precio = Column(DECIMAL(10,2), nullable=False)
    disponibilidad = Column(Enum('disponible', 'reservado', 'vendido'), default='disponible')
    localizacion = Column(String(255), nullable=False)  # Localización del vendedor
    categoria_id = Column(Integer, ForeignKey('Categorias.categoria_id'))
    vendedor_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    fecha_publicacion = Column(DateTime, nullable=False)

    categoria = relationship("Categoria", back_populates="productos")
    vendedor = relationship("Usuario", back_populates="productos")
    fotos = relationship("Foto", back_populates="producto")
    mensajes = relationship("Mensaje", back_populates="producto")

    # Indexes
    __table_args__ = (Index('ix_productos_categoria_id', 'categoria_id'),
                      Index('ix_productos_vendedor_id', 'vendedor_id'),)

class Mensaje(Base):
    __tablename__ = 'Mensajes'
    mensaje_id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('Productos.producto_id'))
    id_usuario_envia = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    id_usuario_recibe = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(DateTime, nullable=False)
    leido = Column(Boolean, default=False)  # Campo nuevo para indicar si el mensaje ha sido leído

    producto = relationship("Producto", back_populates="mensajes")
    usuario_envia = relationship("Usuario", foreign_keys=[id_usuario_envia], back_populates="mensajes_enviados")
    usuario_recibe = relationship("Usuario", foreign_keys=[id_usuario_recibe], back_populates="mensajes_recibidos")

    # Indexes
    __table_args__ = (Index('ix_mensajes_producto_id', 'producto_id'),)


class Transaccion(Base):
    __tablename__ = 'Transacciones'
    transaccion_id = Column(Integer, primary_key=True)
    comprador_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    vendedor_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    producto_id = Column(Integer, ForeignKey('Productos.producto_id'))
    fecha_transaccion = Column(DateTime, nullable=False)
    monto = Column(DECIMAL(10,2), nullable=False)
    stripe_payment_id = Column(String(255), nullable=False)

    comprador = relationship("Usuario", back_populates="transacciones_compradas", foreign_keys=[comprador_id])
    vendedor = relationship("Usuario", back_populates="transacciones_vendidas", foreign_keys=[vendedor_id])


class Valoracion(Base):
    __tablename__ = 'Valoraciones'
    valoracion_id = Column(Integer, primary_key=True)
    de_usuario_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    para_usuario_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text)
    fecha_valoracion = Column(DateTime, nullable=False)

    de_usuario = relationship("Usuario", back_populates="valoraciones_dadas", foreign_keys=[de_usuario_id])
    para_usuario = relationship("Usuario", back_populates="valoraciones_recibidas", foreign_keys=[para_usuario_id])

class Envio(Base):
    __tablename__ = 'Envios'
    envio_id = Column(Integer, primary_key=True)
    transaccion_id = Column(Integer, ForeignKey('Transacciones.transaccion_id'))
    estado_envio = Column(String(255), nullable=False)
    fecha_envio = Column(DateTime)

    transaccion = relationship("Transaccion", back_populates="envios")

class Usuario(Base):
    __tablename__ = 'Usuarios'
    usuario_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido1 = Column(String(255), nullable=False)
    apellido2 = Column(String(255))
    email = Column(String(255), nullable=False, unique=True)
    hash_contraseña = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    ubicacion = Column(String(255))
    
    # Relaciones
    productos = relationship("Producto", back_populates="vendedor")
    mensajes_enviados = relationship("Mensaje", foreign_keys="Mensaje.id_usuario_envia", back_populates="usuario_envia")
    mensajes_recibidos = relationship("Mensaje", foreign_keys="Mensaje.id_usuario_recibe", back_populates="usuario_recibe")
    transacciones_compradas = relationship("Transaccion", foreign_keys="Transaccion.comprador_id", back_populates="comprador")
    transacciones_vendidas = relationship("Transaccion", foreign_keys="Transaccion.vendedor_id", back_populates="vendedor")
    valoraciones_dadas = relationship("Valoracion", foreign_keys="Valoracion.de_usuario_id", back_populates="de_usuario")
    valoraciones_recibidas = relationship("Valoracion", foreign_keys="Valoracion.para_usuario_id", back_populates="para_usuario")

class Foto(Base):
    __tablename__ = 'Fotos'
    foto_id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('Productos.producto_id'))  # Cambiado de 'anuncio_id' a 'producto_id'
    url_foto = Column(String(255), nullable=False)

    producto = relationship("Producto", back_populates="fotos")  # Cambiado de 'anuncio' a 'producto'


# Completing the relationship in 'Transaccion'
Transaccion.envios = relationship("Envio", back_populates="transaccion")