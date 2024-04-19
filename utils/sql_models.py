from sqlalchemy import create_engine, Column, Integer, String,  ForeignKey, Text, DateTime, DECIMAL, Enum
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
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text)
    visitas = Column(Integer, default=0)
    localizacion = Column(String(255), nullable=False)
    categoria_id = Column(Integer, ForeignKey('Categorias.categoria_id'))
    
    categoria = relationship("Categoria", back_populates="productos")
    anuncios = relationship("Anuncio", back_populates="producto")
    transacciones = relationship("Transaccion", back_populates="producto")

class Anuncio(Base):
    __tablename__ = 'Anuncios'
    anuncio_id = Column(Integer, primary_key=True)
    vendedor_id = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    producto_id = Column(Integer, ForeignKey('Productos.producto_id'))
    precio = Column(DECIMAL(10,2), nullable=False)
    fecha_publicacion = Column(DateTime, nullable=False)
    estado = Column(Enum('disponible', 'reservado', 'vendido'), default='disponible')

    vendedor = relationship("Usuario", back_populates="anuncios")
    producto = relationship("Producto", back_populates="anuncios")

class Mensaje(Base):
    __tablename__ = 'Mensajes'
    mensaje_id = Column(Integer, primary_key=True)
    id_usuario_envia = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    id_usuario_recibe = Column(Integer, ForeignKey('Usuarios.usuario_id'))
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(DateTime, nullable=False)

    usuario_envia = relationship("Usuario", back_populates="mensajes_enviados", foreign_keys=[id_usuario_envia])
    usuario_recibe = relationship("Usuario", back_populates="mensajes_recibidos", foreign_keys=[id_usuario_recibe])

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
    producto = relationship("Producto", back_populates="transacciones")

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
    nombre_usuario = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    hash_contraseña = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    ubicacion = Column(String(255))
    intereses = Column(Text)
    historial = Column(Text)
    
    # Relaciones
    anuncios = relationship("Anuncio", back_populates="vendedor")
    mensajes_enviados = relationship("Mensaje", foreign_keys="Mensaje.id_usuario_envia", back_populates="usuario_envia")
    mensajes_recibidos = relationship("Mensaje", foreign_keys="Mensaje.id_usuario_recibe", back_populates="usuario_recibe")
    transacciones_compradas = relationship("Transaccion", foreign_keys="Transaccion.comprador_id", back_populates="comprador")
    transacciones_vendidas = relationship("Transaccion", foreign_keys="Transaccion.vendedor_id", back_populates="vendedor")
    valoraciones_dadas = relationship("Valoracion", foreign_keys="Valoracion.de_usuario_id", back_populates="de_usuario")
    valoraciones_recibidas = relationship("Valoracion", foreign_keys="Valoracion.para_usuario_id", back_populates="para_usuario")


# Completing the relationship in 'Transaccion'
Transaccion.envios = relationship("Envio", back_populates="transaccion")