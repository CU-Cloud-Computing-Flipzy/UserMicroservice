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
)
from fastapi.responses import JSONResponse

from models.user import UserRead, UserCreate, UserUpdate
from models.address import Address, AddressCreate, AddressUpdate


# App config
port = int(os.environ.get("FASTAPIPORT", 8000))

app = FastAPI(
    title="User Service",
    version="0.2.0",
    description="User & Address microservice for Flipzy (Sprint 2).",
)


# DB helpers (mysql via pymysql)

def get_connection():
    """
    Create a new MySQL connection using environment variables.
    """
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DB", "user_service"),
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
        is_active=bool(row["is_active"]),
        is_verified=bool(row["is_verified"]),
        role=row["role"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_address(row: Dict[str, Any]) -> Address:
    return Address(
        id=UUID(row["id"]),
        user_id=UUID(row["user_id"]),
        recipient=row["recipient"],
        phone=row["phone"],
        country=row["country"],
        city=row["city"],
        street=row["street"],
        postal_code=row["postal_code"],
        is_default=bool(row["is_default"]),
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


# ----------------------------------------------------------------------
# Users collection & resources
# ----------------------------------------------------------------------


@app.get("/users", response_model=List[UserRead], tags=["users"])
def list_users(
    email: Optional[str] = Query(None, description="Filter by exact email"),
    username: Optional[str] = Query(
        None, description="Filter by username (substring match)"
    ),
    role: Optional[str] = Query(
        None,
        description="Filter by role",
        regex="^(user|moderator|admin)$",
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter by active/inactive status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset for paging"),
):
    """
    Collection resource with query parameters :
    - email / username / role / is_active filters
    - limit / offset for basic pagination
    """
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
        if role:
            sql += " AND role = %s"
            params.append(role)
        if is_active is not None:
            sql += " AND is_active = %s"
            params.append(1 if is_active else 0)

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
    """
    Create user with 201 Created + Location header.
    """
    user_id = uuid4()
    conn = get_connection()
    try:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users
                        (id, email, username, full_name, avatar_url, phone)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(user_id),
                        payload.email,
                        payload.username,
                        payload.full_name,
                        str(payload.avatar_url) if payload.avatar_url else None,
                        payload.phone,
                    ),
                )
        except pymysql.err.IntegrityError:
            # unique(email) or unique(username) violation
            raise HTTPException(
                status_code=400,
                detail="Email or username already exists",
            )

    finally:
        conn.close()

    # Fetch full row (including defaults like is_active, created_at...)
    user = fetch_user_by_id(user_id)

    # REST best practice: Location header points to the new resource
    response.headers["Location"] = f"/users/{user_id}"
    return user


@app.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: UUID):
    return fetch_user_by_id(user_id)


@app.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def replace_user(user_id: UUID, payload: UserUpdate):
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
            # Nothing to update, just return current value
            return fetch_user_by_id(user_id)

        sql = "UPDATE users SET " + ", ".join(fields) + " WHERE id = %s"
        params.append(str(user_id))

        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

    finally:
        conn.close()

    return fetch_user_by_id(user_id)


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
    # 204 No Content: no response body
    return Response(status_code=status.HTTP_204_NO_CONTENT)



# Addresses collection & resources

@app.get("/addresses", response_model=List[Address], tags=["addresses"])
def list_addresses(
    user_id: Optional[UUID] = Query(None, description="Filter by user_id"),
    city: Optional[str] = Query(None, description="Filter by city"),
    postal_code: Optional[str] = Query(None, description="Filter by postal code"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset for paging"),
):
    """
    Collection resource with query parameters for addresses.
    """
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
    """
    Create address with 201 Created + Location header.
    """
    addr_id = uuid4()

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO addresses
                  (id, user_id, recipient, phone, country, city, street, postal_code, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(addr_id),
                    str(payload.user_id),
                    payload.recipient,
                    payload.phone,
                    payload.country,
                    payload.city,
                    payload.street,
                    payload.postal_code,
                    1 if payload.is_default else 0,
                ),
            )
    finally:
        conn.close()

    addr = fetch_address_by_id(addr_id)
    response.headers["Location"] = f"/addresses/{addr_id}"
    return addr


@app.get("/addresses/{address_id}", response_model=Address, tags=["addresses"])
def get_address(address_id: UUID):
    return fetch_address_by_id(address_id)


@app.put("/addresses/{address_id}", response_model=Address, tags=["addresses"])
def replace_address(address_id: UUID, payload: AddressUpdate):
    conn = get_connection()
    try:
        fields = []
        params: list[Any] = []

        if payload.recipient is not None:
            fields.append("recipient = %s")
            params.append(payload.recipient)
        if payload.phone is not None:
            fields.append("phone = %s")
            params.append(payload.phone)
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
        if payload.is_default is not None:
            fields.append("is_default = %s")
            params.append(1 if payload.is_default else 0)

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



# Async job example: 202 Accepted + polling

jobs: Dict[str, Dict[str, Any]] = {}


async def run_export_job(job_id: str, user_id: UUID):
    """
    Dummy async task: simulate exporting user data.
    """
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
    """
    Sprint 2 requirement: 202 Accepted + async processing + polling.

    - call POST /users/{user_id}/export
    - return 202 + job_id，Location: /jobs/{job_id}
    - query GET /jobs/{job_id}
    """
    # check if user exists
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
    return {"message": "Welcome to the User/Address API. See /docs for OpenAPI UI."}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)



