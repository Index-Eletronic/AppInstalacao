from sqlalchemy import Column, String, Date, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    criado_em = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    instalacoes = relationship("Instalacao", back_populates="usuario")


class Instalacao(Base):
    __tablename__ = "instalacoes"

    id = Column(INTEGER(unsigned=True), primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(
        INTEGER(unsigned=True),
        ForeignKey("usuarios.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    qr_id = Column(String(50), nullable=False)
    data_qr = Column(Date, nullable=True)
    cliente = Column(String(100), nullable=False)
    produto = Column(String(100), nullable=False)
    projetista = Column(String(100), nullable=True)
    data_inicial_instalacao = Column(Date, nullable=True)
    data_final_instalacao = Column(Date, nullable=True)
    criado_em = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    usuario = relationship("Usuario", back_populates="instalacoes")