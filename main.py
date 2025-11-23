import os
import asyncio
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any

import pymysql
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    BackgroundTasks,
    status,
    Response,
    Request
)
from fastapi.responses import JSONResponse
# --- 导入 CORS 中间件 ---
from fastapi.middleware.cors import CORSMiddleware 
from datetime import datetime

from models.user import UserRead, UserCreate, UserUpdate
from models.address import Address, AddressCreate, AddressUpdate


port = int(os.environ.get("FASTAPIPORT", 8000))

app = FastAPI(
    title="User Service",
    version="0.2.0",
    description="User & Address microservice.",
)

# --- CORS 配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "10.128.0.3"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "user_microservice"), 
        password=os.getenv("MYSQL_PASSWORD", "1234"),
        database=os.getenv("MYSQL_DB", "userservice"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def row_to_user(row: Dict[str, Any]) -> UserRead:
    return UserRead(
        id=UUID(row["id"]),
        email=row["email"],
        username=row["username"],
        full_name=row["full_name"],
        avatar_url=row["avatar_url"],
        phone=row["phone"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_address(row: Dict[str, Any]) -> Address:
    return Address(
        id=UUID(row["id"]),
        user_id=UUID(row["user_id"]),
        country=row["country"],
        city=row["city"],
        street=row["street"],
        postal_code=row["postal_code"],
    )


def fetch_user_by_id(user_id: UUID) -> UserRead:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            return row_to_user(row)
    finally:
        conn.close()


def fetch_address_by_id(address_id: UUID) -> Address:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM addresses WHERE id = %s", (str(address_id),))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Address not found")
            return row_to_address(row)
    finally:
        conn.close()


def make_user_etag(user) -> str:
    ts = int(user.updated_at.timestamp() if isinstance(user.updated_at, datetime)
             else datetime.fromisoformat(str(user.updated_at)).timestamp())
    return f'W/"user-{user.id}-{ts}"'


def user_link_headers(user_id) -> dict[str, str]:
    return {
        "Link": (
            f'</users/{user_id}>; rel="self", '
            f'</users>; rel="collection", '
            f'</addresses?user_id={user_id}>; rel="addresses"'
        )
    }


# ----------------------------------------------------------------------
# Users
# ----------------------------------------------------------------------

@app.get("/users", response_model=List[UserRead], tags=["users"])
def list_users(
    email: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    conn = get_connection()
    try:
        sql = "SELECT * FROM users WHERE 1=1"
        params: list[Any] = []

        if email:
            sql += " AND email = %s"
            params.append(email)
        if username:
            sql += " AND username LIKE %s"
            params.append(f"%{username}%")

        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [row_to_user(r) for r in rows]
    finally:
        conn.close()


@app.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
def create_user(payload: UserCreate, response: Response):
    user_id = uuid4()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. 检查用户是否存在 (Find)
            cur.execute("SELECT * FROM users WHERE email = %s", (payload.email,))
            existing_user = cur.fetchone()

            if existing_user:
                # 存在则返回旧用户信息 (模拟登录)
                response.status_code = status.HTTP_200_OK
                response.headers["Location"] = f"/users/{existing_user['id']}"
                return row_to_user(existing_user)

            # 2. 不存在则创建 (Create)
            cur.execute(
                """
                INSERT INTO users
                    (id, email, username, password, full_name, avatar_url, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(user_id),
                    payload.email,
                    payload.username,
                    payload.password, 
                    payload.full_name,
                    str(payload.avatar_url) if payload.avatar_url else None,
                    payload.phone,
                ),
            )
    except pymysql.err.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

    user = fetch_user_by_id(user_id)
    response.headers["Location"] = f"/users/{user_id}"
    return user


@app.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: UUID, request: Request, response: Response):
    user = fetch_user_by_id(user_id)
    etag = make_user_etag(user)

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, **user_link_headers(user_id)})

    response.headers["ETag"] = etag
    response.headers.update(user_link_headers(user_id))
    return user


@app.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def replace_user(user_id: UUID, payload: UserUpdate, request: Request, response: Response):
    current = fetch_user_by_id(user_id)
    current_etag = make_user_etag(current)

    if_match = request.headers.get("if-match")
    if if_match and if_match != current_etag:
        raise HTTPException(status_code=412, detail="Precondition Failed (ETag mismatch)")

    conn = get_connection()
    try:
        fields = []
        params: list[Any] = []

        if payload.username is not None:
            fields.append("username = %s")
            params.append(payload.username)
        if payload.full_name is not None:
            fields.append("full_name = %s")
            params.append(payload.full_name)
        if payload.avatar_url is not None:
            fields.append("avatar_url = %s")
            params.append(str(payload.avatar_url))
        if payload.phone is not None:
            fields.append("phone = %s")
            params.append(payload.phone)

        if not fields:
            response.headers["ETag"] = current_etag
            response.headers.update(user_link_headers(user_id))
            return current

        sql = "UPDATE users SET " + ", ".join(fields) + " WHERE id = %s"
        params.append(str(user_id))

        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
    finally:
        conn.close()

    updated = fetch_user_by_id(user_id)
    new_etag = make_user_etag(updated)
    response.headers["ETag"] = new_etag
    response.headers.update(user_link_headers(user_id))
    return updated


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
)
def delete_user(user_id: UUID):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s", (str(user_id),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
    finally:
        conn.close()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Addresses
# ----------------------------------------------------------------------

@app.get("/addresses", response_model=List[Address], tags=["addresses"])
def list_addresses(
    user_id: Optional[UUID] = Query(None),
    city: Optional[str] = Query(None),
    postal_code: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    conn = get_connection()
    try:
        sql = "SELECT * FROM addresses WHERE 1=1"
        params: list[Any] = []

        if user_id:
            sql += " AND user_id = %s"
            params.append(str(user_id))
        if city:
            sql += " AND city LIKE %s"
            params.append(f"%{city}%")
        if postal_code:
            sql += " AND postal_code = %s"
            params.append(postal_code)

        sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        return [row_to_address(r) for r in rows]
    finally:
        conn.close()


@app.post(
    "/addresses",
    response_model=Address,
    status_code=status.HTTP_201_CREATED,
    tags=["addresses"],
)
def create_address(payload: AddressCreate, response: Response):
    addr_id = uuid4()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO addresses
                  (id, user_id, country, city, street, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    str(addr_id),
                    str(payload.user_id),
                    payload.country,
                    payload.city,
                    payload.street,
                    payload.postal_code,
                ),
            )
    finally:
        conn.close()

    addr = fetch_address_by_id(addr_id)
    response.headers["Location"] = f"/addresses/{addr_id}"
    return addr


@app.get("/addresses/{address_id}", response_model=Address, tags=["addresses"])
def get_address(address_id: UUID, response: Response):
    addr = fetch_address_by_id(address_id)
    response.headers["Link"] = (
        f'</addresses/{address_id}>; rel="self", '
        f'</addresses>; rel="collection", '
        f'</users/{addr.user_id}>; rel="user"'
    )
    return addr


@app.put("/addresses/{address_id}", response_model=Address, tags=["addresses"])
def replace_address(address_id: UUID, payload: AddressUpdate):
    conn = get_connection()
    try:
        fields = []
        params: list[Any] = []

        if payload.country is not None:
            fields.append("country = %s")
            params.append(payload.country)
        if payload.city is not None:
            fields.append("city = %s")
            params.append(payload.city)
        if payload.street is not None:
            fields.append("street = %s")
            params.append(payload.street)
        if payload.postal_code is not None:
            fields.append("postal_code = %s")
            params.append(payload.postal_code)

        if not fields:
            return fetch_address_by_id(address_id)

        sql = "UPDATE addresses SET " + ", ".join(fields) + " WHERE id = %s"
        params.append(str(address_id))

        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Address not found")
    finally:
        conn.close()

    return fetch_address_by_id(address_id)


@app.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["addresses"],
)
def delete_address(address_id: UUID):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM addresses WHERE id = %s", (str(address_id),))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Address not found")
    finally:
        conn.close()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------

jobs: Dict[str, Dict[str, Any]] = {}


async def run_export_job(job_id: str, user_id: UUID):
    jobs[job_id]["status"] = "running"
    await asyncio.sleep(5)
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["result"] = {"user_export_url": f"/users/{user_id}"}


@app.post(
    "/users/{user_id}/export",
    status_code=status.HTTP_202_ACCEPTED,
    tags=["users"],
)
async def start_export_user(
    user_id: UUID,
    background_tasks: BackgroundTasks,
):
    fetch_user_by_id(user_id)

    job_id = str(uuid4())
    jobs[job_id] = {"status": "pending"}
    background_tasks.add_task(run_export_job, job_id, user_id)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"job_id": job_id, "status": "pending"},
        headers={"Location": f"/jobs/{job_id}"},
    )


@app.get("/jobs/{job_id}", tags=["jobs"])
def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/")
def root():
    return {"message": "Welcome to the User/Address API."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


