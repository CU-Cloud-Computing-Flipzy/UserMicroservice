CREATE TABLE IF NOT EXISTS users (
  id           CHAR(36)     NOT NULL PRIMARY KEY DEFAULT (UUID()),
  email        VARCHAR(255) NOT NULL UNIQUE,
  username     VARCHAR(30)  NOT NULL UNIQUE,
  full_name    VARCHAR(50),
  avatar_url   TEXT,
  phone        VARCHAR(30),

  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CHECK (phone IS NULL OR CHAR_LENGTH(phone) BETWEEN 6 AND 30)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS addresses (
  id           CHAR(36)     NOT NULL PRIMARY KEY DEFAULT (UUID()),
  user_id      CHAR(36)     NOT NULL,

  country      VARCHAR(60)  NOT NULL,
  city         VARCHAR(60)  NOT NULL,
  street       VARCHAR(120) NOT NULL,
  postal_code  VARCHAR(20),

  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_addresses_user_id 
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,

  CHECK (postal_code IS NULL OR CHAR_LENGTH(postal_code) BETWEEN 3 AND 20)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_0900_ai_ci;

CREATE INDEX idx_addresses_user_id ON addresses (user_id);
CREATE INDEX idx_addresses_city ON addresses (city);
CREATE INDEX idx_addresses_postal_code ON addresses (postal_code);
