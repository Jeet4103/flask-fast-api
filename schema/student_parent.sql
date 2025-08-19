CREATE TABLE student_parents (
    student_id INTEGER NOT NULL,
    parent_id INTEGER NOT NULL,
    student_name VARCHAR(50) NOT NULL,
    parent_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (student_id, parent_id),
    FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES parents(id) ON DELETE CASCADE
);