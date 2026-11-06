-- CS-4347 Library Project - Milestone 1
-- Loads the normalized CSV files into the schema created by schema.sql.
-- Run from the folder that contains the CSV files:
--     mysql --local-infile=1 -u <user> -p < schema.sql
--     mysql --local-infile=1 -u <user> -p < load_data.sql
-- (The server also needs:  SET GLOBAL local_infile = 1;)

USE library;

LOAD DATA LOCAL INFILE 'books.csv' INTO TABLE BOOK
  CHARACTER SET utf8mb4
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (Isbn, Isbn13, Title);

LOAD DATA LOCAL INFILE 'authors.csv' INTO TABLE AUTHORS
  CHARACTER SET utf8mb4
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (Author_id, Name);

LOAD DATA LOCAL INFILE 'book_authors.csv' INTO TABLE BOOK_AUTHORS
  CHARACTER SET utf8mb4
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (Author_id, Isbn);

LOAD DATA LOCAL INFILE 'borrowers.csv' INTO TABLE BORROWER
  CHARACTER SET utf8mb4
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
  LINES TERMINATED BY '\n'
  IGNORE 1 LINES
  (Card_id, Ssn, Bname, First_name, Last_name, Email, Address, Phone);

SELECT 'BOOK' AS tbl, COUNT(*) FROM BOOK
UNION ALL SELECT 'AUTHORS', COUNT(*) FROM AUTHORS
UNION ALL SELECT 'BOOK_AUTHORS', COUNT(*) FROM BOOK_AUTHORS
UNION ALL SELECT 'BORROWER', COUNT(*) FROM BORROWER;
