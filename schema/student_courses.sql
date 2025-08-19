CREATE TABLE student_courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT,
  course_id INT,
  enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(user_id),
  FOREIGN KEY (course_id) REFERENCES courses(id)
);
