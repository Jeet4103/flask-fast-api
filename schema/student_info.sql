CREATE TABLE student_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    phone_number BIGINT,
    mothers_name VARCHAR(100),
    fathers_name VARCHAR(100),
    date_of_birth DATE,
    branch VARCHAR(50),
    address VARCHAR(100),
    FOREIGN KEY(student_id) REFERENCES students(user_id) ON DELETE CASCADE
);
