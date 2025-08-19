ALTER TABLE students ADD UNIQUE (user_id);

CREATE TABLE grades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    student_name VARCHAR(50) NOT NULL,
    course_id INT NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    term_id INT,
    term_name VARCHAR(50),
    grade VARCHAR(5),
    marks_obtained DECIMAL(5,2),
    total_marks DECIMAL(5,2),
    gpa DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_grades_student FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_grades_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    CONSTRAINT fk_grades_term FOREIGN KEY (term_id) REFERENCES academic_terms(id) ON DELETE SET NULL
);
