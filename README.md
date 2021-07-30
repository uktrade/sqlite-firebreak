# stream-sqlite [![CircleCI](https://circleci.com/gh/uktrade/stream-sqlite.svg?style=shield)](https://circleci.com/gh/uktrade/stream-sqlite) [![Test Coverage](https://api.codeclimate.com/v1/badges/b665c7634e8194fe6878/test_coverage)](https://codeclimate.com/github/uktrade/stream-sqlite/test_coverage)

Python function to extract all the rows from a SQLite database file concurrently with iterating over its bytes. Typically used to extract rows while downloading, without loading the entire file to memory or disk.


## Installation

```bash
pip install stream-sqlite
```


## Usage

```python
from stream_sqlite import stream_sqlite
import httpx

def sqlite_bytes():
    # Iterable that yields the bytes of a sqlite file
    with httpx.stream('GET', 'https://www.example.com/my.sqlite') as r:
        yield from r.iter_bytes(chunk_size=65536)

# A table is not guaranteed to be contiguous in a sqlite file, so can appear
# multiple times while iterating. However, if there is a single table in the
# file, there will be exactly one iteration of the outer loop
for table_name, table_info, rows in stream_sqlite(sqlite_bytes()):
    # Output of PRAGMA table_info
    print(table_info)

    for row in rows:
        print(row)
```


## Limitations and recommendations

The [SQLite file format](https://www.sqlite.org/fileformat.html) is not designed to be streamed: the data is arranged in _pages_ of a fixed number of bytes, and the information to identify a page may come _after_ the page in the stream. Therefore, pages are buffered in memory by the `stream_sqlite` function until they can be identified.

However, if you have control over the SQLite file, `VACUUM;` should be run on it before streaming. In addition to minimising the size of the file, `VACUUM;` arranges the pages in a way that often reduces the buffering required when streaming. This is especially true if it was the target of intermingled `INSERT`s and/or `DELETE`s over multiple tables.

Also, indexes are not used for extracting the rows while streaming. If streaming is the only use case of the SQLite file, and you have control over it, indexes should be removed, and `VACUUM;` then run.
