SET FOREIGN_KEY_CHECKS=0;

CREATE DATABASE gym_db;
USE gym_db;

-- Create tables in dependency order
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE
) ENGINE=InnoDB;

CREATE TABLE trainers (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(100) UNIQUE
) ENGINE=InnoDB;

CREATE TABLE membership_plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL,
    duration_months INT NOT NULL,
    price DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    gender VARCHAR(10),
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(100),
    trainer_id INT,
    session_date DATE,
    start_time TIME,
    end_time TIME,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE member_plans (
    member_plan_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    plan_id INT,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date DATE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(plan_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    session_id INT,
    attended BOOLEAN DEFAULT TRUE,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT,
    amount DECIMAL(10,2),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method ENUM('Cash', 'Card', 'UPI', 'Online'),
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS=1;

-- Insert initial data
INSERT INTO users (username, email, password_hash, is_admin) 
VALUES ('admin', 'admin@fithub.com', 'pbkdf2:sha256:600000$dw99OqKPjk1o4Gxt$5eea6e515de97968c75f7253fc832c6a34746d5e97665df60c947d529dc06217', TRUE);

INSERT INTO membership_plans (plan_name, duration_months, price) VALUES
('Basic Monthly', 1, 50.00),
('Standard Quarterly', 3, 135.00),
('Premium Annual', 12, 500.00);

INSERT INTO trainers (name, specialization, email, phone) VALUES
('John Smith', 'Weight Training', 'john@fithub.com', '(555) 123-4567'),
('Sarah Johnson', 'Yoga', 'sarah@fithub.com', '(555) 234-5678');

-- Insert some sample sessions for today
INSERT INTO sessions (session_name, trainer_id, session_date, start_time, end_time) VALUES
('Morning Yoga', 2, CURDATE(), '08:00:00', '09:00:00'),
('Weight Training 101', 1, CURDATE(), '10:00:00', '11:00:00'),
('Evening Yoga', 2, CURDATE(), '17:00:00', '18:00:00');
