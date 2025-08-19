create table users(
    id int auto_increment primary key,
    first_name varchar(50) not null,
    middle_name varchar(50) not null,
    last_name varchar(50) not null,
    username varchar(50) not null,
    password varchar(50) not null,
    email varchar(50) not null,
    role ENUM('student', 'staff') NOT NULL,
    created_at datetime default current_timestamp,
    is_active boolean default true
    );