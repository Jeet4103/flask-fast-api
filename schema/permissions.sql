CREATE TABLE permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    delete_students BOOLEAN DEFAULT FALSE,
    soft_delete BOOLEAN DEFAULT FALSE,
    update_student BOOLEAN DEFAULT FALSE,
    advanced_search BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
