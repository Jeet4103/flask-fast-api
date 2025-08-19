CREATE TABLE parents (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number BIGINT,
    email VARCHAR(100),
    relationship ENUM('Father', 'Mother', 'Guardian', 'Other') NOT NULL,
    address TEXT,
    created_at datetime DEFAULT CURRENT_TIMESTAMP
);