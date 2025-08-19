CREATE TABLE academic_terms (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,           
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);