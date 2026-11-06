#!/usr/bin/env python3
"""
Verifies the normalized output by loading it into an SQLite
database that enforces the project's primary keys, foreign keys and
uniqueness constraints, then running integrity checks against the raw input.
"""
import csv
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
RAW_BOOKS = next(p for p in (os.path.join(PARENT, "books.csv"),
                             os.path.join(PARENT, "books-1.csv")) if os.path.exists(p))

DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE BOOK (Isbn TEXT PRIMARY KEY CHECK (length(Isbn) = 10),
                   Isbn13 TEXT UNIQUE, Title TEXT NOT NULL);
CREATE TABLE AUTHORS (Author_id INTEGER PRIMARY KEY, Name TEXT NOT NULL);
CREATE TABLE BOOK_AUTHORS (Author_id INTEGER NOT NULL REFERENCES AUTHORS(Author_id),
                           Isbn TEXT NOT NULL REFERENCES BOOK(Isbn),
                           PRIMARY KEY (Author_id, Isbn));
CREATE TABLE BORROWER (Card_id TEXT PRIMARY KEY, Ssn TEXT NOT NULL UNIQUE,
                       Bname TEXT NOT NULL, First_name TEXT, Last_name TEXT,
                       Email TEXT, Address TEXT NOT NULL, Phone TEXT);
"""


def load(con, table, path):
    with open(os.path.join(HERE, path), encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))[1:]
    marks = ",".join("?" * len(rows[0]))
    con.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)
    return len(rows)


def main():
    con = sqlite3.connect(":memory:")
    con.executescript(DDL)
    for t, p in [("BOOK", "books.csv"), ("AUTHORS", "authors.csv"),
                 ("BOOK_AUTHORS", "book_authors.csv"), ("BORROWER", "borrowers.csv")]:
        print(f"loaded {load(con, t, p):6d} rows into {t}  (PK/FK/UNIQUE enforced)")

    with open(RAW_BOOKS, encoding="utf-8-sig", newline="") as f:
        raw = list(csv.DictReader(f))
    raw_isbns = {r["ISBN10"] for r in raw}
    db_isbns = {r[0] for r in con.execute("SELECT Isbn FROM BOOK")}

    checks = {
        "every source ISBN present (leading zeros / X kept)": raw_isbns == db_isbns,
        "no orphan BOOK_AUTHORS rows":
            con.execute("PRAGMA foreign_key_check").fetchall() == [],
        "no author without a book":
            con.execute("SELECT COUNT(*) FROM AUTHORS WHERE Author_id NOT IN "
                        "(SELECT Author_id FROM BOOK_AUTHORS)").fetchone()[0] == 0,
        "author names unique":
            con.execute("SELECT COUNT(*) - COUNT(DISTINCT Name) FROM AUTHORS").fetchone()[0] == 0,
        "no leading/trailing/double spaces in names or titles":
            con.execute("SELECT COUNT(*) FROM (SELECT Name s FROM AUTHORS UNION ALL "
                        "SELECT Title FROM BOOK UNION ALL SELECT Bname FROM BORROWER) "
                        "WHERE s <> trim(s) OR s LIKE '%  %'").fetchone()[0] == 0,
        "Bname = First_name || ' ' || Last_name":
            con.execute("SELECT COUNT(*) FROM BORROWER WHERE Bname <> First_name || ' ' || "
                        "Last_name").fetchone()[0] == 0,
    }
    # example mapping
    ex = con.execute("""SELECT b.Title, group_concat(a.Name, '|') FROM BOOK b
                        JOIN BOOK_AUTHORS ba USING (Isbn) JOIN AUTHORS a USING (Author_id)
                        WHERE b.Isbn = '1567407781' GROUP BY b.Isbn""").fetchone()
    checks["PDF example: 1567407781 -> The Witchfinder / Estleman, Kenneth"] = (
        ex == ("The Witchfinder", "Loren D. Estleman|John Kenneth"))

    ok = True
    for name, passed in checks.items():
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok &= passed
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
