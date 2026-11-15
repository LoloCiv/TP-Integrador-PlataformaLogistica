# Plataforma de Logística y Rutas de Entrega

Backend de una plataforma de logística para comercio local: recibe órdenes de entrega, retira
la mercadería del depósito que la tiene, calcula la ruta óptima del repartidor y muestra su
ubicación en tiempo real. El frontend **no está incluido**: todo se usa a través de la API REST
(y del WebSocket de tracking), que está completamente desacoplada de cualquier cliente.

---

## 1. Arquitectura

### Servicios (`docker-compose.yml`)

| Servicio  | Qué hace | Puerto expuesto |
|-----------|----------|-----------------|
| `backend` | La API REST + WebSocket (FastAPI + Uvicorn) | `8000` |
| `db`      | Base de datos PostgreSQL | `5432` (para entrar con DBeaver u otro cliente) |
| `redis`   | Cola de mensajes entre el backend y el microservicio | — (solo dentro de la red; se consulta con `docker compose exec redis redis-cli`) |
| `rutas`   | Microservicio que calcula las rutas: escucha la cola de Redis y escribe el resultado en Postgres | — (no recibe pedidos de afuera) |

Los cuatro están en la misma red (`red-logistica`) y se encuentran por el nombre del servicio
(`db:5432`, `redis:6379`).

### El camino de una orden

```
Cliente ──POST /ordenes──► backend ──► Postgres          (orden PENDIENTE, stock descontado)
        ──PATCH /ordenes/{id}/asignar──► backend
                                          │ LPUSH cola_rutas (MensajeRuta en JSON)
                                          ▼
                                        Redis
                                          │ BRPOP cola_rutas
                                          ▼
                                    microservicio rutas
                                          │ vecino más cercano → nro_parada, distancia, tiempo
                                          ▼
                                       Postgres  ◄── GET /ordenes/{id} ya muestra la parada
```

El cálculo es **asíncrono**: la API publica el mensaje y responde enseguida, sin esperar la ruta.
Si el microservicio está caído, los mensajes quedan esperando en la lista de Redis y se procesan
cuando vuelve. El mensaje se publica al **asignar repartidor** (ver sección 6).

### Capas del backend

Un request recorre, en este orden:

| Capa | Dónde está | Qué hace |
|------|------------|----------|
| API (controladores) | `app/api/` | Un router por recurso: recibe el request, valida con los schemas y llama a la lógica |
| Middleware | `app/middleware/` | `auth.py` valida el token; `log_requests.py` registra cada request |
| Log | `app/core/logging.py` | Configuración única del `logging` (consola + `logs/app.log`) |
| Lógica de negocio | `app/services/` + métodos de `app/models/` | `GestorPedidos`, cola de mensajes, conexiones WebSocket |
| ORM | `app/models/` + `app/db.py` | Clases SQLAlchemy mapeadas a las tablas de Postgres |

## 2. Requisitos

- **Docker Desktop** (incluye Docker Compose). Con eso alcanza: Python, Postgres y Redis corren
  dentro de los contenedores.
- Opcional: un cliente HTTP (la página `/docs` ya sirve para probar todo) y DBeaver para mirar la base.

## 3. Cómo levantar el proyecto

Todos los comandos se corren desde la raíz del repositorio (donde está `docker-compose.yml`).

0. **Clonar el repositorio** (si no se tiene ya):

   ```bash
   git clone <url-del-repositorio>
   ```

1. **Crear el `.env`**: copiar el que se entrega aparte, o crearlo a partir de la plantilla y
   completar los valores (ver sección 4):

   ```bash
   cp .env.example .env
   ```

2. **Construir y levantar todo** en segundo plano:

   ```bash
   docker compose up -d --build
   ```

   La primera vez tarda un poco (descarga imágenes e instala dependencias). Las tablas se crean
   solas al arrancar el backend (`create_all`, sin migraciones).

3. **Comprobar que anda:**
   - `http://localhost:8000/health` → `{"status": 200, "data": {"api": "ok", "db": "ok"}}`
   - `http://localhost:8000/docs` → documentación interactiva. Con el botón **Authorize** se
     pega el token para probar los endpoints privados.

4. **Ver los logs:**

   ```bash
   docker compose logs -f
   ```

   ```bash
   docker compose logs -f rutas
   ```

   El primero muestra todos los servicios; el segundo solo el microservicio (sirve para verlo
   calcular cada ruta). Los logs del backend también quedan en `logs/app.log`.

5. **Apagar:**

   ```bash
   docker compose down
   ```

   ```bash
   docker compose down -v
   ```

   `down` borra los contenedores pero **conserva los datos** (quedan en el volumen `pgdata`).
   `down -v` borra además los volúmenes: la base arranca **vacía** la próxima vez.

### Imágenes

| Servicio | Imagen |
|----------|--------|
| `db`     | `postgres:16` (oficial de Docker Hub) |
| `redis`  | `redis:7` (oficial de Docker Hub) |
| `backend`| Se construye con `Dockerfile` (base `python:3.12-slim`) |
| `rutas`  | Se construye con `rutas/Dockerfile` (base `python:3.12-slim`) |

No hace falta descargar ni entregar imágenes: `docker compose up --build` baja las oficiales y
construye las otras dos a partir del código.

En desarrollo, el `backend` monta la carpeta del proyecto dentro del contenedor y corre con `--reload`:
los cambios en el código se aplican sin reconstruir. El microservicio `rutas` **no** tiene ese
montaje: si se cambia su código, hay que reconstruirlo (`docker compose up -d --build rutas`).

## 4. Variables del `.env`

| Variable | Para qué sirve | Obligatoria / valor por defecto |
|----------|----------------|---------------------------------|
| `POSTGRES_USER` | Usuario de Postgres (la imagen lo crea la primera vez) | **Obligatoria** |
| `POSTGRES_PASSWORD` | Contraseña de ese usuario | **Obligatoria** |
| `POSTGRES_DB` | Nombre de la base | **Obligatoria** |
| `POSTGRES_HOST` | Dónde está Postgres | `db` (el nombre del servicio) |
| `POSTGRES_PORT` | Puerto de Postgres | `5432` |
| `REDIS_URL` | Conexión a Redis | `redis://redis:6379/0` |
| `JWT_SECRET` | Clave con la que se firman los tokens | **Obligatoria** |
| `JWT_EXPIRA_MINUTOS` | Duración de un token | `60` |
| `JWT_ALGORITMO` | Algoritmo de firma del JWT | `HS256` |
| `CORS_ORIGINS` | Orígenes que pueden llamar a la API desde un navegador, separados por coma | `http://localhost:3000` |
| `LOG_LEVEL` | Nivel de log: `DEBUG`, `INFO`, `WARNING` o `ERROR` | `INFO` |

Para generar un `JWT_SECRET` seguro:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> El `.env` real **no está en el repositorio** (está en `.gitignore` y `.dockerignore`) porque
> tiene contraseñas y la clave JWT. Se entrega aparte. En el repo solo está `.env.example`.

## 5. Endpoints

Todas las respuestas tienen el mismo formato: status + valores.

```json
{ "status": 200, "data": { ... } }
{ "status": 200, "data": [ ... ], "paginacion": { "total": 42, "limit": 20, "offset": 0 } }
{ "status": 404, "error": "Producto 7 no existe" }
```

Todos los `GET` de colecciones están **paginados** con `?limit=&offset=`: `limit` vale 20 por
defecto (mínimo 1, máximo 100) y `offset` 0. Un valor fuera de rango responde 422.

### Públicos (no necesitan token)

Lista oficial: `RUTAS_PUBLICAS` en `app/middleware/auth.py`.

| Método | Ruta | Para qué |
|--------|------|----------|
| `POST` | `/auth/login` | Obtener un token |
| `POST` | `/clientes` | Registrarse como cliente |
| `GET`  | `/productos`, `/productos/{id}` | Ver el catálogo |
| `GET`  | `/depositos`, `/depositos/{id}`, `/depositos/{id}/productos` | Ver depósitos y sus productos |
| `GET`  | `/health` | Estado de la API y la base |
| `GET`  | `/docs`, `/openapi.json` | Documentación |

### Privados (necesitan `Authorization: Bearer <token>`)

Sin token o con token inválido/vencido → **401**. Con token pero sin el rol pedido → **403**.

| Recurso | GET (lista paginada / uno) | POST | PUT | PATCH | DELETE |
|---------|:-:|:-:|:-:|:-:|:-:|
| `/auth` | `GET /auth/yo` | — | — | `/auth/password` | — |
| `/clientes` | ✓ (+ `/clientes/{id}/ordenes`) | público | — | ✓ | — |
| `/repartidores` | ✓ | ✓ | — | ✓ | ✓ |
| `/vehiculos` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `/depositos` | público | ✓ | ✓ | ✓ | ✓ |
| `/productos` | público | ✓ | ✓ | ✓ | ✓ |
| `/inventario` | ✓ | ✓ | — | ✓ | ✓ |
| `/ordenes` | ✓ | ✓ 🔒 cliente | — | ver abajo | — |
| `/rutas` | — | — | — | ver abajo | — |
| `/tracking` | — | — | ✓ 🔒 repartidor | — | — |

Acciones sobre órdenes y rutas (todas `PATCH`, porque modifican parte de algo que ya existe):

| Ruta | Qué hace | Rol |
|------|----------|-----|
| `PATCH /ordenes/{id}/asignar` | Asigna repartidor y vehículo → `CONFIRMADA` y publica el cálculo de ruta | cualquier usuario logueado |
| `PATCH /rutas/{id}/iniciar` | El repartidor sale: **todas** las órdenes `CONFIRMADA` de la ruta pasan juntas a `EN_CAMINO` | 🔒 repartidor (solo su ruta) |
| `PATCH /ordenes/{id}/estado` | `EN_CAMINO → ENTREGADA`, de a una orden | 🔒 repartidor (solo órdenes de su ruta) |
| `PATCH /ordenes/{id}/cancelar` | Cancela (solo desde `PENDIENTE` o `CONFIRMADA`) y devuelve el stock | cualquier usuario logueado |

El paso a `EN_CAMINO` es por ruta y no por orden a propósito: si las órdenes salieran de a una, la
ruta seguiría "abierta", una orden nueva podría sumarse y el recálculo pisaría las paradas de un
recorrido que ya arrancó.

Otras reglas de acceso:
- `GET /clientes/{id}/ordenes`: un cliente solo puede ver **su** historial (si no → 403).
- Donde no hay PUT (`repartidores`, `inventario`, `clientes`) es a propósito: o la contraseña
  tiene su propio camino (`PATCH /auth/password`) o hay un solo campo modificable, y PUT y PATCH
  serían lo mismo.

### Login

```http
POST /auth/login
{ "user_name": "ana", "password": "secreta123" }
```

Devuelve:

```json
{ "status": 200, "data": { "access_token": "eyJ...", "token_type": "bearer", "rol": "cliente" } }
```

El token (JWT firmado con `JWT_SECRET`) lleva el id del usuario y su rol (`cliente` o
`repartidor`), y vence a los `JWT_EXPIRA_MINUTOS`. Se manda en cada request privado:
`Authorization: Bearer eyJ...`. El login es un controlador propio (`app/api/auth.py`): **crea**
el token; el middleware solo lo **verifica**.

### WebSocket de tracking

```
ws://localhost:8000/tracking/{id_orden}?token=<token>
```

- El **cliente** se conecta a la orden que quiere seguir. El token va en la URL porque los
  navegadores no permiten mandar headers en un WebSocket; se valida a mano (el middleware solo
  revisa HTTP). Un cliente solo puede mirar **sus** órdenes, y un repartidor solo las de **sus**
  rutas; si no, la conexión se cierra con código `1008`.
- El **repartidor** manda su posición con `PUT /tracking` (`{"latitud": ..., "longitud": ...}`).
  Se guarda en la base y se transmite a quienes están mirando sus órdenes que estén **`EN_CAMINO`**.
  Cada orden es un canal aparte: nadie recibe la ubicación de una orden ajena.

Mensaje que recibe el cliente:

```json
{ "id_repartidor": 3, "latitud": "-34.590000", "longitud": "-58.420000", "ultima_actualizacion": "..." }
```

## 6. Decisiones de diseño

### El mensaje de ruta se publica al asignar repartidor, no al crear la orden
Es un cambio respecto del documento aprobado, que lo ubicaba en `crearOrden()`. Al crear la orden
todavía no se sabe qué repartidor ni qué vehículo la van a llevar, y una ruta es justamente
eso: el recorrido de **un** repartidor con **un** vehículo. Por eso el mensaje sale en
`asignar_repartidor`: ahí se agrupa la orden con las demás `CONFIRMADA` de ese repartidor y
vehículo, y se manda a calcular la ruta completa (depósito + todas las entregas).

### El peso de cada orden se valida contra la capacidad del vehículo
`Orden.calcular_peso()` suma `cantidad × peso` de cada detalle. Al asignar, si supera
`Vehiculo.capacidad_kg`, la asignación se rechaza (400). Es lo que le importa a una plataforma
de logística.

### Se mantienen los precios
`Producto.precio`, `Orden.total` y `calcular_total()` siguen en el modelo, como en el documento
aprobado. El detalle guarda una **foto del precio** (`DetalleOrden.precio_unitario`): si
después el producto cambia de precio, el total de las órdenes ya creadas no cambia.

### Inyección de dependencias
`GestorPedidos` recibe la cola por constructor y solo conoce la interfaz `ColaMensajes`:
`ColaRedis` en la API (`app/api/ordenes.py`) y `ColaFalsa` en los tests, que guarda los mensajes
en una lista sin tocar Redis. El microservicio hace lo mismo: `ProcesadorRutas` recibe un
`RutaOptimizador` (hoy vecino más cercano, mañana se podría cambiar por OR-Tools) y un
repositorio (en los tests, un `Mock`).

### Herencia `Usuario` → `Cliente` / `Repartidor`
Herencia de tablas unidas (*joined table*): una tabla `usuario` con los datos comunes y una tabla
por subclase con los propios, unidas por la misma clave. La columna `tipo` le dice a SQLAlchemy
qué subclase es cada fila; además, se usa como rol en el token.

### Errores
La lógica de negocio no sabe de HTTP: lanza `NoEncontrado` (→ 404) o `ValueError` (→ 400), y
los manejadores de `app/core/errores.py` los traducen al formato de respuesta. Una restricción de
la base (dato duplicado o en uso) → 409; cualquier error inesperado → 500 sin detalles
técnicos (el detalle queda en el log).

## 7. Tests

Con el stack levantado:

| Comando | Qué prueba |
|---------|------------|
| `docker compose exec backend pytest` | Todo el backend: unitarios + integración + e2e |
| `docker compose exec backend pytest tests/unit` | Lógica de los modelos, `GestorPedidos` con `ColaFalsa`, seguridad, respuestas y WebSocket. Sin Postgres ni Redis (SQLite en memoria) |
| `docker compose exec backend pytest tests/integration` | La API con pedidos HTTP reales (`httpx.AsyncClient`) contra Postgres: login, alta de órdenes, stock descontado, historial |
| `docker compose exec backend pytest tests/e2e` | El camino completo con Redis y el microservicio reales: asignar → Redis → `rutas` → `nro_parada` guardado |
| `docker compose exec rutas pytest` | El microservicio: optimizador, procesador con mocks y repositorio |

- El **e2e** necesita todo el stack arriba (`docker compose up -d`). Si el backend no responde,
  el test se **saltea** en vez de fallar.
- La **integración** usa una base aparte, `<POSTGRES_DB>_test`, en el mismo Postgres: la crea
  sola, la vacía después de cada test y **nunca toca los datos de la base real**.

## 8. Estructura de carpetas

```
.
├── app/
│   ├── main.py          # arma la app: CORS, middlewares, manejadores de error y routers
│   ├── db.py            # engine, sesión y create_all
│   ├── api/             # controladores: un router por recurso
│   ├── core/            # config (.env), seguridad (JWT), respuestas, errores, logging, dependencias
│   ├── middleware/      # auth (token) y log de requests
│   ├── models/          # clases SQLAlchemy (las entidades del diagrama) y enums
│   ├── schemas/         # Pydantic: qué entra y qué sale por la API
│   └── services/        # GestorPedidos, cola de mensajes, conexiones WebSocket
├── rutas/               # microservicio de rutas (imagen y código propios)
│   ├── main.py          # loop que escucha la cola de Redis
│   ├── mensajes.py      # MensajeRuta y Coordenada
│   ├── optimizador.py   # RutaOptimizador + vecino más cercano
│   ├── procesador.py    # ProcesadorRutas y RepositorioRutas (SQL directo)
│   └── tests/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
