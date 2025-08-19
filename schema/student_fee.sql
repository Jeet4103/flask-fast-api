CREATE TABLE student_fees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    fee_category_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    due_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending','partial','paid') DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    FOREIGN KEY (fee_category_id) REFERENCES fee_categories(id) ON DELETE CASCADE
);
