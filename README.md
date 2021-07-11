# stream-sqlite [![CircleCI](https://circleci.com/gh/uktrade/stream-sqlite.svg?style=shield)](https://circleci.com/gh/uktrade/stream-sqlite) [![Test Coverage](https://api.codeclimate.com/v1/badges/b665c7634e8194fe6878/test_coverage)](https://codeclimate.com/github/uktrade/stream-sqlite/test_coverage)

It can read a table from sqlite page(s)
Hardcoded database path for convenience

Missing:
Parsing sql in sqlite_master to identify the table name and the starting page
no checks for consistency between record size and space allocated to the record
record overflow
handling of NO ROWID tables. For the moment, I always output the row index at the beginning of the record
TESTS


Inefficient:
use recursion to read a page
several useless seek and read in the routines



Wrong:
reading of varint using more than 2 bytes (?)
use hardcoded page size