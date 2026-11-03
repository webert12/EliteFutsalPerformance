from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class AtletaCriacao(BaseModel):
    usuario_id: int
    nascimento: date
    posicao: Literal['goleiro','fixo','ala_direito','ala_esquerdo','pivo','universal']
    altura_cm: float = Field(gt=90, lt=230)
    peso_kg: float = Field(gt=20, lt=200)
    pe_dominante: Literal['direito','esquerdo','ambos'] | None = None
    observacoes: str | None = Field(default=None, max_length=1000)

class AtletaPublico(AtletaCriacao):
    model_config = ConfigDict(from_attributes=True)
    id: int

class RegistroCriacao(BaseModel):
    dia: date
    sono_horas: float | None = Field(default=None, ge=0, le=24)
    agua_ml: int | None = Field(default=None, ge=0, le=15000)
    esforco_0_10: int | None = Field(default=None, ge=0, le=10)
    duracao_treino_min: int | None = Field(default=None, ge=0, le=360)
    bem_estar_0_10: int | None = Field(default=None, ge=0, le=10)
    alimentacao_observacoes: str | None = Field(default=None, max_length=1000)
    dor_ou_lesao: bool = False

class RegistroPublico(RegistroCriacao):
    model_config = ConfigDict(from_attributes=True)
    id: int
    atleta_id: int
