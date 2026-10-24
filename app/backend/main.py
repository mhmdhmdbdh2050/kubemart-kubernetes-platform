import hashlib
import os
import secrets
import time
from decimal import Decimal

import psycopg
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from psycopg.rows import dict_row
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

app = FastAPI(title="KubeMart API", version="1.1.0")
password_hash = PasswordHash.recommended()
SESSION_COOKIE = "kubemart_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() not in {
    "0", "false", "no"
}


def connect_db():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


def initialize_database():
    # Retry startup while PostgreSQL becomes available.
    for attempt in range(30):
        try:
            with connect_db() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(160) NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
                        image_url TEXT NOT NULL DEFAULT '',
                        stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGSERIAL PRIMARY KEY,
                        customer_name VARCHAR(160) NOT NULL,
                        email VARCHAR(254) NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        token_hash CHAR(64) PRIMARY KEY,
                        user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        expires_at TIMESTAMPTZ NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS sessions_expires_at_idx
                    ON sessions(expires_at)
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id BIGSERIAL PRIMARY KEY,
                        customer_name VARCHAR(160) NOT NULL,
                        customer_email VARCHAR(254) NOT NULL,
                        status VARCHAR(30) NOT NULL DEFAULT 'pending',
                        total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                # Existing lab databases retain their old orders; new orders
                # are linked to the authenticated customer.
                conn.execute("""
                    ALTER TABLE orders
                    ADD COLUMN IF NOT EXISTS user_id BIGINT
                    REFERENCES users(id) ON DELETE SET NULL
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS order_items (
                        id BIGSERIAL PRIMARY KEY,
                        order_id BIGINT NOT NULL
                            REFERENCES orders(id) ON DELETE RESTRICT,
                        product_id INTEGER NOT NULL
                            REFERENCES products(id) ON DELETE RESTRICT,
                        product_name VARCHAR(160) NOT NULL,
                        unit_price NUMERIC(10, 2) NOT NULL,
                        quantity INTEGER NOT NULL CHECK (quantity > 0)
                    )
                """)

                # Multiple API replicas can start at once. Serialize initial
                # catalog seeding so they cannot insert duplicate products.
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (73190421,))
                count = conn.execute(
                    "SELECT COUNT(*) AS count FROM products"
                ).fetchone()["count"]

                if count == 0:
                    conn.cursor().executemany("""
                        INSERT INTO products
                            (name, description, price, image_url, stock)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [
                        (
                            "Wireless Headphones",
                            "Comfortable wireless headphones for everyday use.",
                            Decimal("1299.00"),
                            "https://placehold.co/600x400?text=Headphones",
                            20,
                        ),
                        (
                            "Smart Watch",
                            "A practical smartwatch for daily activities.",
                            Decimal("1899.00"),
                            "https://placehold.co/600x400?text=Smart+Watch",
                            15,
                        ),
                        (
                            "Laptop Backpack",
                            "A durable backpack for work and study.",
                            Decimal("799.00"),
                            "https://placehold.co/600x400?text=Backpack",
                            25,
                        ),
                        (
                            "USB-C Hub",
                            "A compact hub for connecting your devices.",
                            Decimal("549.00"),
                            "https://placehold.co/600x400?text=USB-C+Hub",
                            30,
                        ),
                    ])
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(2)


@app.on_event("startup")
def startup():
    initialize_database()


class AccountInput(BaseModel):
    customer_name: str = Field(min_length=2, max_length=160)
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=12, max_length=128)


class LoginInput(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)


class CreateOrder(BaseModel):
    items: list[OrderItem] = Field(min_length=1, max_length=50)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_session_cookie(response: Response, token: str):
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="strict",
        path="/",
    )


def create_session(conn, user_id: int, response: Response):
    token = secrets.token_urlsafe(32)
    conn.execute("DELETE FROM sessions WHERE expires_at <= NOW()")
    conn.execute("""
        INSERT INTO sessions (token_hash, user_id, expires_at)
        VALUES (%s, %s, NOW() + (%s * INTERVAL '1 second'))
    """, (token_digest(token), user_id, SESSION_TTL_SECONDS))
    set_session_cookie(response, token)


def get_current_user(
    kubemart_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    if not kubemart_session:
        raise HTTPException(status_code=401, detail="Sign in to continue")

    try:
        with connect_db() as conn:
            user = conn.execute("""
                SELECT u.id, u.customer_name, u.email
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s AND s.expires_at > NOW()
            """, (token_digest(kubemart_session),)).fetchone()
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to continue")
    return user


def require_same_origin(request: Request):
    # SameSite cookies provide the primary CSRF defense. Reject a supplied
    # cross-origin Origin as defense in depth, accounting for TLS termination
    # at the ingress proxy by comparing hostnames rather than schemes.
    origin = request.headers.get("origin")
    if origin:
        from urllib.parse import urlsplit

        try:
            origin_host = urlsplit(origin).netloc.casefold()
        except ValueError:
            raise HTTPException(status_code=403, detail="Cross-origin request rejected")
        request_host = request.headers.get("host", "").casefold()
        if not origin_host or origin_host != request_host:
            raise HTTPException(status_code=403, detail="Cross-origin request rejected")


@app.get("/live")
def live():
    return {"status": "ok"}


@app.get("/health")
def health():
    try:
        with connect_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.post("/api/auth/register", status_code=201)
def register(account: AccountInput, request: Request, response: Response):
    require_same_origin(request)
    name = account.customer_name.strip()
    if len(name) < 2:
        raise HTTPException(status_code=422, detail="Name must contain at least 2 characters")
    email = str(account.email).strip().casefold()

    try:
        with connect_db() as conn:
            user = conn.execute("""
                INSERT INTO users (customer_name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, customer_name, email
            """, (name, email, password_hash.hash(account.password))).fetchone()
            create_session(conn, user["id"], response)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database operation failed")

    return user


@app.post("/api/auth/login")
def login(credentials: LoginInput, request: Request, response: Response):
    require_same_origin(request)
    email = str(credentials.email).strip().casefold()
    try:
        with connect_db() as conn:
            user = conn.execute("""
                SELECT id, customer_name, email, password_hash
                FROM users WHERE email = %s
            """, (email,)).fetchone()
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

    if user is None or not password_hash.verify(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    try:
        with connect_db() as conn:
            create_session(conn, user["id"], response)
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    return {"id": user["id"], "customer_name": user["customer_name"], "email": user["email"]}


@app.post("/api/auth/logout")
def logout(
    request: Request,
    response: Response,
    kubemart_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    require_same_origin(request)
    if kubemart_session:
        try:
            with connect_db() as conn:
                conn.execute("DELETE FROM sessions WHERE token_hash = %s", (token_digest(kubemart_session),))
        except psycopg.Error:
            raise HTTPException(status_code=503, detail="Authentication service unavailable")
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )
    return {"status": "signed_out"}


@app.get("/api/auth/me")
def current_account(user=Depends(get_current_user)):
    return user


@app.get("/api/products")
def list_products():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT id, name, description, price, image_url, stock
            FROM products
            ORDER BY id
        """).fetchall()
    return rows


@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    with connect_db() as conn:
        product = conn.execute("""
            SELECT id, name, description, price, image_url, stock
            FROM products WHERE id = %s
        """, (product_id,)).fetchone()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.post("/api/orders", status_code=201)
def create_order(
    order: CreateOrder,
    request: Request,
    user=Depends(get_current_user),
):
    require_same_origin(request)
    try:
        with connect_db() as conn:
            # Lock product rows to avoid overselling concurrent orders.
            product_ids = sorted({item.product_id for item in order.items})
            products = conn.execute("""
                SELECT id, name, price, stock
                FROM products
                WHERE id = ANY(%s)
                ORDER BY id
                FOR UPDATE
            """, (product_ids,)).fetchall()

            product_map = {p["id"]: p for p in products}
            quantities = {}
            for item in order.items:
                quantities[item.product_id] = (
                    quantities.get(item.product_id, 0) + item.quantity
                )

            if len(product_map) != len(product_ids):
                raise HTTPException(status_code=400, detail="Unknown product")

            total = Decimal("0.00")
            for product_id, quantity in quantities.items():
                product = product_map[product_id]
                if product["stock"] < quantity:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Insufficient stock for {product['name']}",
                    )
                total += product["price"] * quantity

            created = conn.execute("""
                INSERT INTO orders
                    (user_id, customer_name, customer_email, total)
                VALUES (%s, %s, %s, %s)
                RETURNING id, customer_name, customer_email, status,
                          total, created_at
            """, (user["id"], user["customer_name"], user["email"], total)).fetchone()

            for product_id, quantity in quantities.items():
                product = product_map[product_id]
                conn.execute("""
                    INSERT INTO order_items
                        (order_id, product_id, product_name, unit_price, quantity)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    created["id"], product_id, product["name"],
                    product["price"], quantity,
                ))
                conn.execute("""
                    UPDATE products SET stock = stock - %s WHERE id = %s
                """, (quantity, product_id))

        return {
            "id": created["id"],
            "customer_name": created["customer_name"],
            "customer_email": created["customer_email"],
            "status": created["status"],
            "total": created["total"],
            "created_at": created["created_at"],
        }
    except HTTPException:
        raise
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database operation failed")
