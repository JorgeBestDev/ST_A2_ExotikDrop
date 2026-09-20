# ExokitDrop

Aplicación web orientada a la gestión y compra de productos de edición limitada, con enfoque en drops, catálogo de productos, carrito de compra, pedidos y pagos. El proyecto está pensado como una arquitectura API-first con backend en Flask y frontend en React, preparándose para crecer en un monorepo o en dos repositorios desacoplados según la estrategia de despliegue.

## 1. Descripción general

ExokitDrop es una propuesta de plataforma de e-commerce especializada en productos premium, rare editions y drops. La aplicación busca cubrir la parte comercial y operativa del negocio, permitiendo:

- gestionar usuarios y administradores
- mostrar categorías y productos
- organizar drops y promociones por fecha
- gestionar carrito de compra
- registrar pedidos y pagos
- preparar la capa visual con React para una experiencia moderna en cliente

La base actual ya incluye la capa de backend REST con Flask, SQLAlchemy y migraciones, así como el esquema inicial de datos para soportar la lógica de negocio principal.

## 2. Proyección del proyecto

### Arquitectura prevista

- Backend: Flask + Flask-SQLAlchemy + Flask-Migrate
- Frontend: React + Vite
- Base de datos: PostgreSQL
- Autenticación y seguridad: Flask + password hashing + variables de entorno
- CORS y consumo API: cliente React consumiendo endpoints REST con fetch/axios

### Modelo de trabajo recomendado

La solución se puede organizar en dos formas:

1. Monorepo
   - todo el proyecto vive en una misma estructura
   - más sencillo para despliegue local y gestión de dependencias
   - útil si se quiere trabajar en un único repositorio con frontend y backend

2. Repositorios separados
   - backend y frontend en carpetas separadas, pero con una misma lógica de negocio
   - más limpio si se quiere independizar despliegues y equipos
   - recomendable para arquitectura más profesional y escalable

En este proyecto se ha priorizado una estructura clara y modular, con la carpeta Backend y la carpeta Frontend separadas, dejando abierta la integración final con React.

## 3. Estructura del proyecto

```text
Backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── categories.py
│   │   ├── drops.py
│   │   ├── products.py
│   │   ├── carts.py
│   │   ├── cart_items.py
│   │   ├── orders.py
│   │   ├── order_items.py
│   │   ├── payments.py
│   │   └── password_reset_tokens.py
│   └── routes/
│       ├── __init__.py
│       ├── user_routes.py
│       ├── product_routes.py
│       ├── categories_routes.py
│       ├── drop_routes.py
│       ├── cart_item.py
│       ├── carts_routes.py
│       ├── order_routes.py
│       ├── order_item_routes.py
│       ├── payment_routes.py
│       └── password_reset_token.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── migrations/

Frontend/
├── package.json
├── vite.config.js
└── src/
```

## 4. Arquitectura de la aplicación

El backend está construido con una arquitectura simple pero ordenada:

- app factory: la aplicación se crea en app/__init__.py mediante create_app()
- configuración centralizada: app/config.py gestiona variables de entorno y valores de configuración
- extensiones compartidas: app/extensions.py centraliza db y migrate
- modelos SQLAlchemy: cada tabla tiene su entidad y relaciones definidas en app/models
- rutas API: cada recurso tiene un blueprint específico en app/routes
- registro de blueprints: app/routes/__init__.py registra todas las rutas principales

Esto permite mantener la app modular, con capacidad de escalar a más recursos, validaciones y servicios.

## 5. Modelo de datos

Los modelos principales son:

### User
- id
- email
- password_hash
- full_name
- is_admin
- created_at
- relaciones: orders, carts, password_reset_tokens

### Category
- id
- name
- description
- productos relacionados

### Drop
- id
- name
- description
- starts_at
- ends_at
- status
- created_at
- productos asociados

### Product
- id
- category_id
- drop_id
- name
- description
- price
- stock
- image_url
- is_active
- created_at
- relaciones: category, drop, cart_items, order_items

### Cart
- id
- user_id
- created_at
- relaciones: user, items

### CartItem
- id
- cart_id
- product_id
- quantity
- added_at
- relación con cart y product

### Order
- id
- user_id
- total
- status
- created_at
- relaciones: user, items, payment

### OrderItem
- id
- order_id
- product_id
- quantity
- unit_price
- total_price
- relación con order y product

### Payment
- id
- order_id
- method
- amount
- status
- created_at
- relación con order

### PasswordResetToken
- id
- user_id
- token
- created_at
- relación con user

## 5.1. Estructura de la base de datos

La base de datos de ExitDrop está diseñada para cubrir el ciclo completo de un
e-commerce de productos limitados: usuarios, catálogo, drops, carritos,
pedidos y pagos. Cada modelo de SQLAlchemy representa una tabla y las claves
foráneas mantienen la relación entre los módulos.

### Diagrama entidad-relación

El siguiente diagrama resume las tablas, sus campos principales y las
relaciones del esquema:

![Diagrama de la base de datos de ExitDrop](./docs/database-schema.jfif)

### Entidades y responsabilidades

| Tabla | Responsabilidad | Relaciones principales |
| --- | --- | --- |
| `users` | Registra clientes y administradores. | Un usuario puede tener muchos `carts`, `orders` y `password_reset_tokens`. |
| `categories` | Clasifica los productos del catálogo. | Una categoría contiene muchos `products`. |
| `drops` | Agrupa lanzamientos con fechas y estado. | Un drop puede publicar muchos `products`. |
| `products` | Contiene el inventario que se muestra en la tienda. | Pertenece a una categoría y opcionalmente a un drop; se relaciona con carritos y pedidos. |
| `carts` | Representa el carrito de un usuario. | Pertenece a un usuario y contiene muchos `cart_items`. |
| `cart_items` | Guarda los productos y cantidades elegidos en un carrito. | Une `carts` con `products`; la combinación `cart_id` + `product_id` es única. |
| `orders` | Guarda la compra confirmada y su estado. | Pertenece a un usuario y contiene muchos `order_items`; puede tener un pago. |
| `order_items` | Conserva el detalle de una compra. | Une `orders` con `products` y guarda el precio aplicado al momento de comprar. |
| `payments` | Registra el método, importe y estado del pago. | Se relaciona con una orden. |
| `password_reset_tokens` | Permite gestionar recuperación de contraseñas. | Cada token pertenece a un usuario. |

### Claves y relaciones

- Las columnas `id` son las claves primarias de cada tabla.
- `products.category_id` referencia a `categories.id`.
- `products.drop_id` referencia a `drops.id` y es opcional porque un producto
  puede existir fuera de un lanzamiento.
- `carts.user_id` y `orders.user_id` referencia a `users.id`.
- `cart_items.cart_id` y `cart_items.product_id` conectan un carrito con sus
  productos. La restricción `uq_cart_product` evita repetir el mismo producto
  dentro del carrito.
- `order_items.order_id` y `order_items.product_id` conectan una orden con
  sus productos. La restricción `uq_order_product` evita duplicar un producto
  dentro de la misma orden.
- `payments.order_id` conecta el pago con la orden correspondiente.
- `password_reset_tokens.user_id` conecta cada token con su usuario.

### Flujo de datos de una compra

1. El usuario consulta `categories` y `products` desde el catálogo.
2. El frontend crea o recupera un registro en `carts`.
3. Cada selección se guarda en `cart_items` con su cantidad.
4. Al confirmar la compra, se crea una fila en `orders`.
5. Los elementos del carrito pasan a `order_items`, conservando `unit_price` y
   `total_price` para mantener el historial aunque cambie el precio del
   producto.
6. El resultado del cobro se registra en `payments` y actualiza el estado de
   la orden.

### Entornos y migraciones

- **Desarrollo local:** si `DATABASE_URL` no está definida, Flask utiliza
  `instance/exitdrop-dev.sqlite3`.
- **Neon/PostgreSQL:** cuando `DATABASE_URL` contiene una URL de PostgreSQL,
  `app/config.py` normaliza el driver a `postgresql+psycopg2`.
- **Migraciones:** Flask-Migrate/Alembic versiona los cambios de esquema en
  `migrations/versions`. La revisión debe ejecutarse con:

  ```bash
  flask --app app.py db upgrade
  ```

- Antes de desplegar una nueva revisión conviene comprobar el estado con:

  ```bash
  flask --app app.py db current
  flask --app app.py db check
  ```

La imagen del diagrama se conserva en
[`docs/database-schema.jfif`](./docs/database-schema.jfif), de modo que la
documentación funciona tanto en GitHub como en una copia local del proyecto.

## 6. Endpoints de la API

La API se expone bajo prefijo /api.

### Usuarios

- GET /api/users
- GET /api/users/<user_id>
- POST /api/users
- PUT /api/users/<user_id>
- DELETE /api/users/<user_id>

### Productos

- GET /api/products
- GET /api/products/<product_id>

### Categorías

- GET /api/categories
- GET /api/categories/<category_id>

### Drops

- GET /api/drops
- GET /api/drops/<drop_id>

### Carts

- GET /api/carts
- GET /api/carts/<cart_id>

### Cart items

- GET /api/cart-items
- GET /api/cart-items/<cart_item_id>

### Orders

- GET /api/orders
- GET /api/orders/<order_id>

### Order items

- GET /api/order-items
- GET /api/order-items/<order_item_id>

### Payments

- GET /api/payments
- GET /api/payments/<payment_id>

### Password reset tokens

- GET /api/password-reset-tokens
- GET /api/password-reset-tokens/<token_id>

## 7. Patrones de respuesta

Los endpoints siguen un formato común y consistente:

```json
{
  "success": true,
  "data": [...],
  "count": 1
}
```

En caso de error:

```json
{
  "success": false,
  "message": "Mensaje descriptivo"
}
```

Esto facilita la integración con React y la renderización de errores desde el cliente.

## 8. Tecnologías usadas

### Backend
- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-CORS
- Python-dotenv
- PostgreSQL + psycopg2-binary
- Werkzeug para hashing de contraseñas

### Frontend (planificado)
- React
- Vite
- JavaScript/JSX (estructura inicial pensada para React)
- consumo de endpoints REST mediante fetch o axios

## 9. Variables de entorno

El proyecto usa un archivo .env para configurar la aplicación. La base de datos se gestiona con DATABASE_URL y se normaliza en app/config.py para asegurar compatibilidad con PostgreSQL y psycopg2.

Ejemplo:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/exokitdrop
SECRET_KEY=tu_clave_secreta
CORS_ORIGINS=http://localhost:5173
DEBUG=True
```

## 10. Cómo ejecutar el backend

Desde la carpeta Backend:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

También se puede arrancar con Flask:

```bash
flask --app app run
```

## 11. Estado actual del proyecto

El backend se encuentra en una fase funcional y modular, con:

- app factory estructurada
- modelos principales creados
- blueprints registrados
- endpoints GET funcionando para recursos principales
- CRUD de usuarios implementado
- preparación para integración con frontend React

## 12. Roadmap futuro

### Fase 1: backend estable
- terminar CRUD completo de productos, carritos, pedidos y pagos
- revisar validaciones y mensajes de error
- asegurar buenas prácticas de serialización y middleware

### Fase 2: integración con React
- crear dashboard administrativo
- construir catálogo público
- pantalla de detalle de producto
- carrito y checkout
- login y registro de usuarios

### Fase 3: despliegue y producción
- configurar PostgreSQL en entorno real
- preparar variables de entorno para producción
- revisar seguridad, CORS y manejo de errores
- desplegar frontend y backend por separado o en monorepo

## 13. Conclusión

ExokitDrop es una base sólida para una aplicación de ecommerce con enfoque en drops y productos de edición limitada. La arquitectura actual ya permite trabajar con una API REST bien organizada y preparada para conectarse a un frontend con React, manteniendo un modelo de datos claro, limpio y extensible.

El proyecto está preparado para continuar evolucionando hacia una solución completa de compra online, con foco tanto en la experiencia de usuario como en la administración y gestión interna del negocio.
