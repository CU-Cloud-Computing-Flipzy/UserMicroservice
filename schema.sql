CREATE TABLE IF NOT EXISTS users (
  id           CHAR(36)     NOT NULL PRIMARY KEY DEFAULT (UUID()),
  email        VARCHAR(255) NOT NULL UNIQUE,
  username     VARCHAR(30)  NOT NULL UNIQUE,
  full_name    VARCHAR(50),
  avatar_url   TEXT,
  phone        VARCHAR(30),
  is_active    TINYINT(1)   NOT NULL DEFAULT 1,
  is_verified  TINYINT(1)   NOT NULL DEFAULT 0,
  role         ENUM('user','moderator','admin') NOT NULL DEFAULT 'user',
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (phone IS NULL OR CHAR_LENGTH(phone) BETWEEN 6 AND 30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE IF NOT EXISTS addresses (
  id           CHAR(36)     NOT NULL PRIMARY KEY DEFAULT (UUID()),
  user_id      CHAR(36)     NOT NULL,
  recipient    VARCHAR(50)  NOT NULL,
  phone        VARCHAR(30),
  country      VARCHAR(60)  NOT NULL,
  city         VARCHAR(60)  NOT NULL,
  street       VARCHAR(120) NOT NULL,
  postal_code  VARCHAR(20),
  is_default   TINYINT(1)   NOT NULL DEFAULT 0,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CHECK (CHAR_LENGTH(recipient) BETWEEN 1 AND 50),
  CHECK (phone IS NULL OR CHAR_LENGTH(phone) BETWEEN 6 AND 30)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



CREATE INDEX idx_addresses_user_id ON addresses (user_id);
CREATE INDEX idx_addresses_city ON addresses (city);
CREATE INDEX idx_addresses_postal_code ON addresses (postal_code);