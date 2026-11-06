-- CS-4347 Library Project - Milestone 1
-- Schema for the library database (MySQL 8.x).
-- Backwards compatible with the given schema: every required table and
-- column exists with the same name; extra columns are additive only.

CREATE DATABASE IF NOT EXISTS library
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library;

DROP TABLE IF EXISTS FINES;
DROP TABLE IF EXISTS BOOK_LOANS;
DROP TABLE IF EXISTS BOOK_AUTHORS;
DROP TABLE IF EXISTS AUTHORS;
DROP TABLE IF EXISTS BORROWER;
DROP TABLE IF EXISTS BOOK;

CREATE TABLE BOOK (
    Isbn    CHAR(10)      NOT NULL,          -- 10-char ISBN, may contain 'X' and leading zeros
    Isbn13  CHAR(13)      NULL,              -- added: ISBN-13 from the source file
    Title   VARCHAR(255)  NOT NULL,
    PRIMARY KEY (Isbn),
    UNIQUE KEY uq_book_isbn13 (Isbn13)
);

CREATE TABLE AUTHORS (
    Author_id INT          NOT NULL AUTO_INCREMENT,
    Name      VARCHAR(255) NOT NULL,
    PRIMARY KEY (Author_id)
);

CREATE TABLE BOOK_AUTHORS (
    Author_id INT      NOT NULL,
    Isbn      CHAR(10) NOT NULL,
    PRIMARY KEY (Author_id, Isbn),
    FOREIGN KEY (Author_id) REFERENCES AUTHORS(Author_id),
    FOREIGN KEY (Isbn)      REFERENCES BOOK(Isbn)
);

CREATE TABLE BORROWER (
    Card_id    CHAR(8)      NOT NULL,        -- e.g. ID000001
    Ssn        CHAR(11)     NOT NULL,        -- ###-##-####
    Bname      VARCHAR(100) NOT NULL,        -- full name
    First_name VARCHAR(50)  NULL,            -- added: name components (allowed by the spec)
    Last_name  VARCHAR(50)  NULL,
    Email      VARCHAR(100) NULL,            -- added: present in the source data
    Address    VARCHAR(255) NOT NULL,
    Phone      VARCHAR(20)  NULL,
    PRIMARY KEY (Card_id),
    UNIQUE KEY uq_borrower_ssn (Ssn)
);

-- No data exists yet for the next two tables (per the milestone description).
CREATE TABLE BOOK_LOANS (
    Loan_id  INT      NOT NULL AUTO_INCREMENT,
    Isbn     CHAR(10) NOT NULL,
    Card_id  CHAR(8)  NOT NULL,
    Date_out DATE     NOT NULL,
    Due_date DATE     NOT NULL,
    Date_in  DATE     NULL,
    PRIMARY KEY (Loan_id),
    FOREIGN KEY (Isbn)    REFERENCES BOOK(Isbn),
    FOREIGN KEY (Card_id) REFERENCES BORROWER(Card_id)
);

CREATE TABLE FINES (
    Loan_id  INT           NOT NULL,
    Fine_amt DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    Paid     BOOLEAN       NOT NULL DEFAULT FALSE,
    PRIMARY KEY (Loan_id),
    FOREIGN KEY (Loan_id) REFERENCES BOOK_LOANS(Loan_id)
);
