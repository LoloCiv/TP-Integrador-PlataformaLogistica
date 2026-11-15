from pydantic import BaseModel, Field


# Body del login
class LoginEntrada(BaseModel):
    user_name: str = Field(min_length=1)
    password: str = Field(min_length=1)


# Lo que devuelve el login
class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str


# Body para cambiar la contraseña
class CambiarPasswordEntrada(BaseModel):
    password_actual: str = Field(min_length=1)
    password_nueva: str = Field(min_length=8)
