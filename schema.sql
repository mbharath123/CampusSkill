-- =============================================================
--  CampusSkill – Database Schema
--  Run this file against MySQL to set up the database.
-- =============================================================

CREATE DATABASE IF NOT EXISTS campusskill
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE campusskill;

-- -----------------------------------------------------------
-- Table: students
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(120)  NOT NULL,
    email        VARCHAR(255)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,          -- bcrypt hash
    department   VARCHAR(120)  NOT NULL,
    academic_year ENUM('1st Year','2nd Year','3rd Year','4th Year','Alumni') NOT NULL,
    bio          TEXT,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- Table: skills
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS skills (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    student_id       INT         NOT NULL,
    skill_name       VARCHAR(120) NOT NULL,
    category         ENUM('Programming','Database','Web Development','AI/ML','Design','Communication','Other') NOT NULL,
    proficiency_level ENUM('Beginner','Intermediate','Advanced') NOT NULL,
    description      TEXT,
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_skill_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT uq_student_skill UNIQUE (student_id, skill_name)
);

-- -----------------------------------------------------------
-- Table: learning_requests
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_requests (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    learner_id       INT         NOT NULL,
    provider_id      INT         NOT NULL,
    skill_id         INT         NOT NULL,
    message          TEXT,
    preferred_time   VARCHAR(255),
    status           ENUM('Pending','Accepted','Rejected','Cancelled','Completed') NOT NULL DEFAULT 'Pending',
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_req_learner  FOREIGN KEY (learner_id)  REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_req_provider FOREIGN KEY (provider_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_req_skill    FOREIGN KEY (skill_id)    REFERENCES skills(id)   ON DELETE CASCADE
);

-- -----------------------------------------------------------
-- Table: sessions
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    request_id       INT         NOT NULL UNIQUE,
    learner_id       INT         NOT NULL,
    provider_id      INT         NOT NULL,
    session_date     DATE        NOT NULL,
    start_time       TIME        NOT NULL,
    duration_minutes INT         NOT NULL DEFAULT 60,
    meeting_details  TEXT,
    status           ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_request  FOREIGN KEY (request_id)  REFERENCES learning_requests(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_learner  FOREIGN KEY (learner_id)  REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_provider FOREIGN KEY (provider_id) REFERENCES students(id) ON DELETE CASCADE
);

-- -----------------------------------------------------------
-- Table: feedback
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    session_id  INT  NOT NULL UNIQUE,          -- one review per session
    learner_id  INT  NOT NULL,
    provider_id INT  NOT NULL,
    rating      TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fb_session  FOREIGN KEY (session_id)  REFERENCES sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_fb_learner  FOREIGN KEY (learner_id)  REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_fb_provider FOREIGN KEY (provider_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================================
--  Sample Demo Data  (clearly separated from real user data)
-- =============================================================

-- Demo students (passwords are bcrypt of "Demo@1234")
INSERT INTO students (full_name, email, password, department, academic_year, bio) VALUES
('Alice Johnson',  'alice@demo.campusskill',
 '$2b$12$I6A8WBqMkPJfOFEGBTg7s.sY2aEHGMINyuGKoG7M8uyWqXmabGK7W',
 'Computer Science', '3rd Year',
 'Passionate about programming and AI. Love helping peers debug code.'),
('Bob Martinez',   'bob@demo.campusskill',
 '$2b$12$I6A8WBqMkPJfOFEGBTg7s.sY2aEHGMINyuGKoG7M8uyWqXmabGK7W',
 'Information Technology', '2nd Year',
 'Web dev enthusiast. Exploring full-stack development.'),
('Carol Lee',      'carol@demo.campusskill',
 '$2b$12$I6A8WBqMkPJfOFEGBTg7s.sY2aEHGMINyuGKoG7M8uyWqXmabGK7W',
 'Data Science', '4th Year',
 'Machine learning researcher and data analytics lover.');

-- Demo skills
INSERT INTO skills (student_id, skill_name, category, proficiency_level, description) VALUES
(1, 'Python Programming', 'Programming',      'Advanced',      'OOP, Flask, data structures'),
(1, 'Machine Learning',   'AI/ML',            'Intermediate',  'scikit-learn, regression, classification'),
(2, 'React.js',           'Web Development',  'Intermediate',  'Hooks, state management, routing'),
(2, 'MySQL',              'Database',         'Advanced',      'Query optimisation, ER design'),
(3, 'Data Visualisation', 'AI/ML',            'Advanced',      'Matplotlib, Seaborn, Tableau basics'),
(3, 'UI/UX Design',       'Design',           'Intermediate',  'Figma, wireframing, prototyping');

-- Demo learning requests
INSERT INTO learning_requests (learner_id, provider_id, skill_id, message, preferred_time, status) VALUES
(2, 1, 1, 'I want to improve my Python skills for backend development.', 'Weekdays after 4 PM', 'Accepted'),
(3, 2, 3, 'Looking to learn React for my final-year project.',           'Saturday mornings',   'Pending');

-- Demo session (from accepted request)
INSERT INTO sessions (request_id, learner_id, provider_id, session_date, start_time, duration_minutes, meeting_details, status) VALUES
(1, 2, 1, '2026-10-25', '16:00:00', 90, 'Google Meet link: meet.google.com/demo-abc-xyz', 'Scheduled');
