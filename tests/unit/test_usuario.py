from app.models import Cliente


def crear_usuario(password: str = "secreta123") -> Cliente:
    usuario = Cliente(user_name="ana")
    usuario.cambiar_password(password)
    return usuario


def test_hash():
    usuario = crear_usuario("secreta123")
    otro = crear_usuario("secreta123")

    assert usuario.password.startswith("$2b$")
    assert usuario.password != "secreta123"
    assert usuario.password != otro.password


def test_credenciales():
    usuario = crear_usuario("secreta123")

    assert usuario.validar_credenciales("secreta123", "ana") is True
    assert usuario.validar_credenciales("otra", "ana") is False
    assert usuario.validar_credenciales("secreta123", "otro_usuario") is False


def test_cambiar_password():
    usuario = crear_usuario("vieja123")

    usuario.cambiar_password("nueva456")

    assert usuario.validar_credenciales("nueva456", "ana") is True
    assert usuario.validar_credenciales("vieja123", "ana") is False
