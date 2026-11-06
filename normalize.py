#!/usr/bin/env python3
"""
CS-4347 Library Project - Milestone 1
Normalizes the raw books/borrowers CSV files into 3NF files that match the
project schema:

    BOOK(Isbn, Title)                             -> books.csv
    AUTHORS(Author_id, Name)                      -> authors.csv
    BOOK_AUTHORS(Author_id, Isbn)                 -> book_authors.csv
    BORROWER(Card_id, Ssn, Bname, Address, Phone) -> borrowers.csv
"""

import argparse
import csv
import os
import re
import sys
import unicodedata
from collections import OrderedDict

# text helpers

ROMAN = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "xi", "xii", "xiii",
         "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"}

# Trim and collapse any run of whitespace to a single space.
def collapse_ws(s):
    return re.sub(r"\s+", " ", s).strip()

# Upper-case the first alphabetic character of s (if it is the first char).
def _cap_first_alpha(s):
    return s[:1].upper() + s[1:] if s[:1].isalpha() else s

"""
    Convert one word to the project's case convention ("Capitalized Words"):
      - first letter upper, the rest lower
      - a letter following '-', '.', '/', '(', '"' is also capitalized
        (Mary-Kate, J.R.R., Either/Or)
      - O'/D'/L' prefixes:  O'Rourke, D'Este, L'Amour
      - Mc prefix:          McDonald
      - Roman numerals (titles only): II, III, IV ...
"""
def recase_word(word, roman=False):
    if roman and word.lower().strip(".,:;!?") in ROMAN:
        return word.upper()
    w = word.lower()
    w = re.sub(r"(^|[-./(\"])([^\W\d_])", lambda m: m.group(1) + m.group(2).upper(), w)
    w = re.sub(r"^([OoDdLl])'([^\W\d_])(?=[^\W\d_])",
               lambda m: m.group(1).upper() + "'" + m.group(2).upper(), w)
    w = fix_mc(w)
    return w

# Mcdonald -> McDonald (only when 'Mc' starts the word and >= 2 letters follow).
def fix_mc(word):
    return re.sub(r"^Mc([a-z])(?=[a-z])", lambda m: "Mc" + m.group(1).upper(), word)

"""
    Apply one consistent capitalization convention to a title or a name.

    The source data is overwhelmingly written in "Capitalized Words" style
    (e.g. "Decision In Normandy"), so that is the convention we enforce.
      - If the whole string is ALL CAPS or all lower case it carries no
        useful case information, so every word is re-cased.
      - Otherwise only words that are entirely lower case are re-cased;
        ALL-CAPS words (acronyms such as FBI, USA, DK) and deliberately
        mixed-case words (MacKade, DeKay) are preserved, except that
        "Mcxxx" is fixed to "McXxx" and lower-case hyphen parts are
        capitalized (Mary-kate -> Mary-Kate).
"""
def normalize_case(text, roman=False):
    letters = [c for c in text if c.isalpha()]
    force = bool(letters) and (all(c.isupper() for c in letters) or
                               all(c.islower() for c in letters))
    out = []
    for word in text.split(" "):
        if not word:
            continue
        if force or word == word.lower():
            out.append(recase_word(word, roman))
        elif word == word.upper():
            out.append(word)
        else:
            w = "-".join(_cap_first_alpha(p) if p == p.lower() else p
                         for p in word.split("-"))
            out.append(fix_mc(_cap_first_alpha(w)))
    return " ".join(out)


# titles

TRAILING_PAREN = re.compile(r"\s*\([^()]*\)\s*$")

"""
    - collapse whitespace
    - '\\' is used in the source to join omnibus volumes -> ' / '
    - 'Flood : Mississippi' -> 'Flood: Mississippi'
    - drop trailing parenthetical series/edition notes, exactly as in the
      example: "The Witchfinder (Amos Walker Series)" -> "The Witchfinder"
    - enforce the common case convention
"""
def clean_title(raw):
    t = collapse_ws(raw.replace("\\", " / "))
    t = re.sub(r"\s+:", ":", t)
    stripped = t
    while TRAILING_PAREN.search(stripped):
        candidate = TRAILING_PAREN.sub("", stripped)
        if not candidate:
            break
        stripped = candidate
    t = stripped.rstrip(" :;,-")
    return normalize_case(t, roman=True)


# author names

# Generational suffixes are part of a person's name and are kept (at the end).
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}
# Credentials / honorifics / filler words are not part of the name -> removed
# when they appear as comma-separated name modifiers ("Ken, Jr. Putnam").
DROP_WORDS = {"ph.d.", "ph.d", "phd", "m.d.", "md", "m.d", "r.d.", "d.d.",
              "s.j.", "dr.", "dr", "rev.", "rev", "sir", "saint", "earl",
              "baroness", "etal.", "etal", "et", "al.", "etc.", "etc", "and"}
# Tokens that are not authors at all (artifacts of the source export).
JUNK_TOKENS = {"", "etc", "etc.", "more", "none", "et al", "et al.", "various",
               "unknown", "unspecified", "n/a"}
# Abbreviations that legitimately end in a period.
ABBREVIATIONS = {"jr.", "sr.", "dr.", "mr.", "mrs.", "ms.", "st.", "ste.",
                 "mt.", "ft.", "rev.", "prof.", "hon.", "gen.", "col.",
                 "capt.", "lt.", "sgt.", "fr.", "bros.", "co.", "inc.",
                 "ltd.", "wm.", "chas.", "geo.", "jos.", "jas.", "ed.",
                 "eds.", "ph.d.", "corp.", "assn.", "dept.", "univ."}

"""
    In the source, authors are separated by a comma WITHOUT a following
    space ("Mark P. O. Morford,Robert J. Lenardon").  A comma FOLLOWED by a
    space is part of a single name ("Ken, Jr. Putnam").  Semicolons are
    also used as separators in a handful of records.
"""
def split_authors(field):
    chunks = re.split(r",(?! )", field)
    # The source export truncated long author lists at a fixed width, which
    # leaves a cut-off last author ('...,Patty Mitchell,Na').  A trailing
    # single word of 1-3 letters in a multi-author field is such a fragment.
    if len(chunks) >= 2 and re.fullmatch(r"[^\W\d_]{1,3}", chunks[-1].strip()):
        chunks = chunks[:-1]
    parts = []
    for chunk in chunks:
        parts.extend(chunk.split(";"))
    return parts

# Remove role notes such as '(Editor)', '(Narrator)', '(Anson)' and truncated ones such as '(Co' at the end of a string.
def strip_parentheticals(s):
    s = re.sub(r"\([^()]*\)", " ", s)
    s = re.sub(r"\([^()]*$", " ", s)
    return s.replace(")", " ")

"""
    Handle names that contain ', ' (an inverted/qualified form), e.g.
        'Ken, Jr. Putnam'           -> 'Ken Putnam Jr.'
        'Jr., Richard Henry Dana'   -> 'Richard Henry Dana Jr.'
        'Harold N., M.D. Levinson'  -> 'Harold N. Levinson'
        'Arthur Conan, Sir Doyle'   -> 'Arthur Conan Doyle'
        'Margaret, Levine Young'    -> 'Margaret Levine Young'
"""
def reorder_comma_name(name):
    if ", " not in name:
        return name
    words, suffixes = [], []
    for seg in name.split(", "):
        for w in seg.split(" "):
            lw = w.lower()
            if lw in SUFFIXES:
                s = w.capitalize() if lw.startswith(("jr", "sr")) else w.upper()
                if lw in ("jr", "sr"):
                    s += "."
                if s not in suffixes:
                    suffixes.append(s)
            elif lw in DROP_WORDS or not w:
                continue
            else:
                words.append(w)
    return " ".join(words + suffixes)

# 'Emmuska Orczy Orczy' -> 'Emmuska Orczy'; 'W.G. W.G. Moore' -> 'W.G. Moore'.
def dedupe_adjacent(name):
    out = []
    for w in name.split(" "):
        is_initial = re.fullmatch(r"[^\W\d_]\.?", w) is not None   # 'J. J. Abrams' is fine
        if not out or is_initial or out[-1].lower() != w.lower():
            out.append(w)
    return " ".join(out)

"""
    Give every initial the form 'X.' followed by a space so that
    'C.S. Lewis', 'C. S Lewis', 'C S Lewis' all become 'C. S. Lewis'.
"""
def normalize_initials(name):
    # 'C.S.' / 'W.W.Comfort' -> 'C. S.' / 'W. W. Comfort'
    name = re.sub(r"\b([^\W\d_])\.(?=[^\W\d_])", r"\1. ", name)
    words = name.split(" ")
    out = []
    for i, w in enumerate(words):
        last = i == len(words) - 1
        if len(w) == 1 and w.isalpha() and w.isupper() and not last:
            w += "."                                   # 'Patricia D Cornwell'
        elif (w.endswith(".") and w[:-1].isalpha() and len(w) > 3
              and w.lower() not in ABBREVIATIONS):
            w = w[:-1]                                 # 'Maeve. Binchy'
        out.append(w)
    return " ".join(out)


CREDENTIAL_TAIL = re.compile(
    r"(,?\s+(Ph\.?\s?D\.?|M\.\s?D\.|R\.\s?N\.|R\.\s?D\.|D\.\s?D\.|M\.\s?S\.|Psy\.\s?D\.))+$",
    re.I)

# Return the normalized author name, or None if the token is not a name.
def clean_author(raw):
    s = collapse_ws(strip_parentheticals(raw).replace("`", "'"))
    if s.lower() in JUNK_TOKENS:
        return None
    s = reorder_comma_name(s)
    s = CREDENTIAL_TAIL.sub("", s)          # 'Warren Farrell Ph.D.' -> 'Warren Farrell'
    s = collapse_ws(s).strip(" ,;-&")
    if not s or s.lower() in JUNK_TOKENS:
        return None
    s = normalize_case(s)
    s = normalize_initials(s)
    s = dedupe_adjacent(s)
    return s or None

"""
    Identity key used to decide whether two spellings are the same author.
    Ignores case, accents, spaces and punctuation, so 'Emily Bronte' and
    'Emily Brontë', 'C.S. Lewis' and 'C. S. Lewis', 'John LeCarre' and
    'John Le Carré', 'Jean Paul Tibbles' and 'Jean-Paul Tibbles' collapse
    to one AUTHORS row.
"""
def author_key(name):
    folded = unicodedata.normalize("NFKD", name.casefold())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return "".join(c for c in folded if c.isalnum())

# Number of non-ASCII characters; used to prefer 'Brontë' over 'Bronte'.
def accent_score(name):
    return sum(1 for c in name if ord(c) > 127)

"""
    Within ONE book, drop a name whose words all appear (in order) inside a
    longer co-author name - these are artifacts of broken source records,
    e.g. 'Saul; Saul Bellow Bellow' -> ['Saul', 'Saul Bellow'] -> ['Saul Bellow'].
"""
def remove_fragments(names):
    def is_subseq(short, long_):
        it = iter(long_)
        return all(w in it for w in short)

    keep = []
    for n in names:
        nw = n.lower().split()
        if any(o != n and len(o.split()) > len(nw) and is_subseq(nw, o.lower().split())
               for o in names):
            continue
        keep.append(n)
    return keep


# ISBN helpers (used only for validation / reporting)

def isbn10_valid(isbn):
    if not re.fullmatch(r"\d{9}[\dXx]", isbn):
        return False
    total = sum((10 - i) * (10 if c in "Xx" else int(c)) for i, c in enumerate(isbn))
    return total % 11 == 0


# Main processing

"""
   Read a CSV that may be comma- or tab-delimited (the PDF says the
   original books.csv is tab-separated; the copy provided is comma-separated).
"""
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        delim = "\t" if sample.split("\n", 1)[0].count("\t") > 0 else ","
        return list(csv.DictReader(f, delimiter=delim))


def process_books(rows):
    books = []                         # (isbn10, isbn13, title)
    authors = OrderedDict()            # key -> (author_id, display name)
    book_authors = []                  # (author_id, isbn10)
    seen_isbn = set()
    stats = {"rows": len(rows), "invalid_isbn10": [], "no_author": 0,
             "dup_isbn": 0}

    for r in rows:
        isbn10 = r["ISBN10"].strip().upper().zfill(10)   # keep leading zeros
        isbn13 = r["ISBN13"].strip()
        if isbn10 in seen_isbn:
            stats["dup_isbn"] += 1
            continue
        seen_isbn.add(isbn10)
        if not isbn10_valid(isbn10):
            stats["invalid_isbn10"].append(isbn10)

        books.append((isbn10, isbn13, clean_title(r["Title"])))

        names = []
        for tok in split_authors(r.get("Author") or ""):
            n = clean_author(tok)
            if n and author_key(n) not in {author_key(x) for x in names}:
                names.append(n)
        names = remove_fragments(names)
        if not names:
            stats["no_author"] += 1

        for n in names:
            k = author_key(n)
            if k not in authors:
                authors[k] = (len(authors) + 1, n)
            elif accent_score(n) > accent_score(authors[k][1]):
                authors[k] = (authors[k][0], n)        # keep the accented spelling
            book_authors.append((authors[k][0], isbn10))

    return books, list(authors.values()), book_authors, stats


def process_borrowers(rows):
    out = []
    id_col = next(c for c in rows[0].keys() if c.lower().startswith("id"))
    for r in rows:
        first = normalize_case(collapse_ws(r["first_name"]))
        last = normalize_case(collapse_ws(r["last_name"]))
        street = normalize_case(collapse_ws(r["address"]))
        city = normalize_case(collapse_ws(r["city"]))
        state = collapse_ws(r["state"]).upper()
        out.append((
            collapse_ws(r[id_col]).upper(),          # card_id
            collapse_ws(r["ssn"]),                   # ssn
            f"{first} {last}",                       # bname (full name)
            first,
            last,
            collapse_ws(r["email"]).lower(),
            f"{street}, {city}, {state}",            # address
            collapse_ws(r["phone"]),
        ))
    return out


def write_csv(path, header, rows):
    # QUOTE_NONNUMERIC: every string (ISBNs, names, titles) is quoted, numeric
    # ids are not -> leading zeros in ISBNs can never be lost by a loader.
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(here)
    default_books = next((p for p in (os.path.join(parent, "books.csv"),
                                      os.path.join(parent, "books-1.csv"))
                          if os.path.exists(p)), os.path.join(parent, "books.csv"))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--books", default=default_books)
    ap.add_argument("--borrowers", default=os.path.join(parent, "borrowers.csv"))
    ap.add_argument("--out", default=here)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    books, authors, book_authors, st = process_books(read_csv(args.books))
    borrowers = process_borrowers(read_csv(args.borrowers))

    write_csv(os.path.join(args.out, "books.csv"), ["isbn", "isbn13", "title"], books)
    write_csv(os.path.join(args.out, "authors.csv"), ["author_id", "name"], authors)
    write_csv(os.path.join(args.out, "book_authors.csv"), ["author_id", "isbn"], book_authors)
    write_csv(os.path.join(args.out, "borrowers.csv"),
              ["card_id", "ssn", "bname", "first_name", "last_name", "email",
               "address", "phone"], borrowers)

    print(f"source book rows      : {st['rows']}")
    print(f"books written         : {len(books)}")
    print(f"authors written       : {len(authors)}")
    print(f"book_authors written  : {len(book_authors)}")
    print(f"borrowers written     : {len(borrowers)}")
    print(f"books with no author  : {st['no_author']}")
    print(f"duplicate ISBNs skipped: {st['dup_isbn']}")
    print(f"ISBN10 failing checksum (kept): {st['invalid_isbn10']}")


if __name__ == "__main__":
    sys.exit(main())
