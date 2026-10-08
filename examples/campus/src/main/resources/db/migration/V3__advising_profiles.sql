CREATE TABLE advising_profiles (
    student_id BIGINT PRIMARY KEY REFERENCES students(id),
    university VARCHAR(100) NOT NULL,
    admission_year INT NOT NULL CHECK (admission_year BETWEEN 1980 AND 2100)
);
