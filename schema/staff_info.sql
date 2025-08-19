CREATE TABLE staff_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    staff_id INT NOT NULL,
    phone_number BIGINT,
    date_of_birth DATE,
    branch VARCHAR(50),
    address VARCHAR(100),
    designation VARCHAR(50),
    FOREIGN KEY (staff_id) REFERENCES staff(user_id) ON DELETE CASCADE
);
