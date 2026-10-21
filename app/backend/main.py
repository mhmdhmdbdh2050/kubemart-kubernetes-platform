import os
import time
from decimal import Decimal

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

app = FastAPI(title="KubeMart API", version="1.0.0")


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
                    CREATE TABLE IF NOT EXISTS orders (
                        id BIGSERIAL PRIMARY KEY,
                        customer_name VARCHAR(160) NOT NULL,
                        customer_email VARCHAR(254) NOT NULL,
                        status VARCHAR(30) NOT NULL DEFAULT 'pending',
                        total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
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


class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)


class CreateOrder(BaseModel):
    customer_name: str = Field(min_length=2, max_length=160)
    customer_email: str = Field(min_length=3, max_length=254)
    items: list[OrderItem] = Field(min_length=1, max_length=50)


@app.get("/health")
def health():
    try:
        with connect_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database unavailable")


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
def create_order(order: CreateOrder):
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
                    (customer_name, customer_email, total)
                VALUES (%s, %s, %s)
                RETURNING id, customer_name, customer_email, status,
                          total, created_at
            """, (order.customer_name, order.customer_email, total)).fetchone()

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
