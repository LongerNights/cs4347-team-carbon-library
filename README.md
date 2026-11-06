# CS-4347 Library Management System (Team Carbon)

This is a library management system built for CS-4347 Database Systems. Librarians use it to manage books, borrowers, loans and fines. It is backed by a MySQL database.

The project is built in milestones:

| Milestone | Goal | Status |
|---|---|---|
| 1 | Normalize the given data into Third Normal Form (3NF) | Done |

## Milestone 1: Normalizing the data

We were given two raw CSV files: `books.csv` and `borrowers.csv`. Milestone 1 splits them into clean files that match the project's database tables.

### Files

| File | What it is | Rows |
|---|---|---|
| `books.csv` | BOOK table: `Isbn`, `Isbn13`, `Title` | 25,001 |
| `authors.csv` | AUTHORS table: `Author_id`, `Name` | 15,272 |
| `book_authors.csv` | BOOK_AUTHORS table: links each book to its authors | 30,059 |
| `borrowers.csv` | BORROWER table: `Card_id`, `Ssn`, `Bname`, `First_name`, `Last_name`, `Email`, `Address`, `Phone` | 1,000 |
| `normalize.py` | Creates the four CSV files above from the raw data | |
| `verify.py` | Checks the output for mistakes | |
| `schema.sql` | Creates all six MySQL tables, including the empty `BOOK_LOANS` and `FINES` tables | |
| `load_data.sql` | Loads the four CSV files into MySQL | |

### Requirements

- Python 3 (no extra packages needed)
- MySQL 8.x (only needed to load the data into a database)

### How to run

**1. Create the CSV files**

```bash
python normalize.py
```

By default, this reads `books-1.csv` (or `books.csv`) and `borrowers.csv` from the parent folder. To use other locations:

```bash
python normalize.py --books path/to/books.csv --borrowers path/to/borrowers.csv --out output/folder
```

**2. Check the output**

```bash
python verify.py
```

This loads the files into a temporary SQLite database with the keys turned on, then runs checks. Every line should say `PASS`.

**3. Load into MySQL (optional)**

Run these from the folder that has the CSV files:

```bash
mysql -u root -p -e "SET GLOBAL local_infile=1;"
mysql -u root -p < schema.sql
mysql -u root -p --local-infile=1 < load_data.sql
```

This creates a database named `library`. If you already have one with that name, its tables are replaced.

### File format

- Each file has a header row and uses UTF-8.
- All text is in quotes, including ISBNs. This keeps leading zeros and the `X` at the end of some ISBNs. Number ids are not quoted.
- `Isbn` is the 10-character ISBN, as the assignment requires. `Isbn13` is an extra column.

## How the data was cleaned

### Books

- ISBNs are stored as text exactly as given, so leading zeros and a trailing `X` are kept.
- Extra spaces in titles are removed.
- Series or edition notes in parentheses at the end of a title are dropped, following the example in the assignment:
  `The Witchfinder (Amos Walker Series)` → `The Witchfinder`
- A backslash between combined volumes becomes ` / `, and `Flood : X` becomes `Flood: X`.

### Authors

- **Splitting authors:** in the raw file, authors are separated by a comma with no space after it. A comma followed by a space is part of one name (`Ken, Jr. Putnam`). Semicolons also separate authors.
- **Fixing flipped names:** names are put back in normal order. Suffixes like Jr. are kept, while titles and degrees are dropped:

  | Raw | Cleaned |
  |---|---|
  | `Ken, Jr. Putnam` | `Ken Putnam Jr.` |
  | `Harold N., M.D. Levinson` | `Harold N. Levinson` |
  | `Arthur Conan, Sir Doyle` | `Arthur Conan Doyle` |

- **Removing roles:** notes like `(Editor)`, `(Narrator)` and `(Illustrator)` are removed.
- **Matching initials:** `C.S. Lewis`, `C. S Lewis` and `C S Lewis` all become `C. S. Lewis`.
- **Removing junk:** `(none)`, `etc.`, `more`, `Unknown` and `Various` are removed. So are cut-off pieces of 1 to 3 letters at the end of a list that was too long (`...,Patty Mitchell,Na`).
- **Merging duplicates:** two spellings count as the same author if they match when case, accents, spaces and punctuation are ignored. For example, `Emily Bronte` and `Emily Brontë` become one author, and the accented spelling is kept.
- **Author ids:** ids are given out in the order authors first appear, as in the assignment's example.

### One capitalization style

The assignment asks for one capitalization style for all titles and names. We capitalize every word, because most of the raw data already does this (`Decision In Normandy`).

- Text that is all capitals or all lower case is fixed: `JANE AUSTEN` → `Jane Austen`.
- In normal text, acronyms (FBI, USA) and special spellings (MacKade) are kept.
- `Mcdonald` → `McDonald`, `O'rourke` → `O'Rourke`, `Mary-kate` → `Mary-Kate`, and Roman numerals in titles become capitals (II, III).
- The same rules are used for borrower names and addresses.

### Borrowers

- `Bname` is the full name, `First_name Last_name`. The assignment allows keeping the first and last name too.
- `Address` is `street, city, state`. Email is kept as an extra column.

## Why this is 3NF

| Table | Reason |
|---|---|
| BOOK | Every column depends only on `Isbn`. `Isbn13` is also unique, so it does not break 3NF. |
| AUTHORS | `Name` depends only on `Author_id`. The list of authors packed into one field is gone. |
| BOOK_AUTHORS | Only key columns. It connects books and authors, since a book can have many authors and an author can write many books. |
| BORROWER | Every column depends on `Card_id`, and `Ssn` is also unique. `Bname` is the full name, which the assignment allows. |

## Known data problems

These come from the raw data. We kept them and listed them here instead of hiding them.

- ISBN `0195153445` fails the ISBN check-digit test. It looks like a broken copy of `0195153448`, but it is kept because it is a separate entry in the raw file.
- 36 books have no usable author (blank or `(none)` in the raw file), so they are not linked to any author.
- Some longer cut-off names, like `Stepha`, can't be told apart from real one-word names like `Sophocles` or `CLAMP`, so they are kept as given.
- Titles that were all capitals lose their acronyms: `THE FBI` → `The Fbi`.
