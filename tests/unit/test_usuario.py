from app.models import Cliente


# Cliente con la contraseña ya hasheada
def crear_usuario(password: str = "secreta123") -> Cliente:
    usuario = Cliente(user_name="ana")
    usuario.cambiar_password(password)
    return usuario


# La contraseña se guarda con bcrypt y nunca en texto plano. La misma clave da hashes distintos (salt)
def test_hash():
    usuario = crear_usuario("secreta123")
    otro = crear_usuario("secreta123")

    assert usuario.password.startswith("$2b$")
    assert usuario.password != "secreta123"
    assert usuario.password != otro.password


# Valida usuario y contraseña juntos
def test_credenciales():
    usuario = crear_usuario("secreta123")

    assert usuario.validar_credenciales("secreta123", "ana") is True
    assert usuario.validar_credenciales("otra", "ana") is False
    assert usuario.validar_credenciales("secreta123", "otro_usuario") is False


# Después de cambiarla sirve la nueva y no la vieja
def test_cambiar_password():
    usuario = crear_usuario("vieja123")

    usuario.cambiar_password("nueva456")

    assert usuario.validar_credenciales("nueva456", "ana") is True
    assert usuario.validar_credenciales("vieja123", "ana") is False
