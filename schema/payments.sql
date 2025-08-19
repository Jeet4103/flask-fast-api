CREATE TABLE payments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_fee_id INT NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    payment_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    payment_method ENUM('cash','card','bank','upi','online') NOT NULL,
    receipt_number CHAR(36) NOT NULL DEFAULT (UUID()),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_fee_id) REFERENCES student_fees(id) ON DELETE CASCADE
);