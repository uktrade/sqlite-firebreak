import collections
import itertools
import sqlite3
import tempfile
import unittest

from stream_sqlite import stream_sqlite

column_constructor = collections.namedtuple('Column', ('cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'))


class TestStreamSqlite(unittest.TestCase):

    def test_empty_database(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size, chunk_size=chunk_size):
                all_chunks = tables_list(stream_sqlite(db(['VACUUM;'], page_size, chunk_size), buffer_size=0))
                self.assertEqual([], all_chunks)

    def test_small_table(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = [
                    "CREATE TABLE \"my_table_'1\" (my_text_col_a text, my_text_col_b text);",
                    "CREATE TABLE \"my_table_'2\" (my_text_col_a text, my_text_col_b text);",
                    "INSERT INTO \"my_table_'1\" VALUES ('some-text-a', 'some-text-b')",
                ]
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=0))
                self.assertEqual([(
                    "my_table_'1",
                    (
                        column_constructor(cid=0, name='my_text_col_a', type='text', notnull=0, dflt_value=None, pk=0),
                        column_constructor(cid=1, name='my_text_col_b', type='text', notnull=0, dflt_value=None, pk=0),
                    ),
                    [('some-text-a', 'some-text-b')],
                )], all_chunks)

    def test_overflow(self):
        for page_size, chunk_size in itertools.product(
            [512],
            [131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                for i  in range(1, 10001):
                    sqls = [
                        "CREATE TABLE my_table_1 (my_text_col_a text);",
                        "INSERT INTO my_table_1 VALUES ('" + ('-' * i) + "')"
                    ]
                    all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=20971520))
                    self.assertEqual([(
                        "my_table_1",
                        (
                            column_constructor(cid=0, name='my_text_col_a', type='text', notnull=0, dflt_value=None, pk=0),
                        ),
                        [
                            ('-' * i,)
                        ],
                    )], all_chunks)

    def test_integers(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = [
                    "CREATE TABLE my_table_1 (my_text_col_a integer);",
                    "INSERT INTO my_table_1 VALUES (0),(1),(2),(65536),(16777216),(4294967296),(1099511627776),(281474976710656),(72057594037927936)",
                    "INSERT INTO my_table_1 VALUES (0),(-1),(-2),(-65536),(-16777216),(-4294967296),(-1099511627776),(-281474976710656),(-72057594037927936)",
                ]
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=0))
                self.assertEqual([(
                    'my_table_1',
                    (
                        column_constructor(cid=0, name='my_text_col_a', type='integer', notnull=0, dflt_value=None, pk=0),
                    ),
                    [
                        (0,),
                        (1,),
                        (2,),
                        (65536,),
                        (16777216,),
                        (4294967296,),
                        (1099511627776,),
                        (281474976710656,),
                        (72057594037927936,),
                        (0,),
                        (-1,),
                        (-2,),
                        (-65536,),
                        (-16777216,),
                        (-4294967296,),
                        (-1099511627776,),
                        (-281474976710656,),
                        (-72057594037927936,)]
                )], all_chunks)

    def test_floats(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = [
                    "CREATE TABLE my_table_1 (my_col_a real);",
                    "INSERT INTO my_table_1 VALUES (0.5123), (-0.1)",
                ]
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=0))
                self.assertEqual([(
                    'my_table_1',
                    (
                        column_constructor(cid=0, name='my_col_a', type='real', notnull=0, dflt_value=None, pk=0),
                    ),
                    [
                        (0.5123,),
                        (-0.1,),
                    ]
                )], all_chunks)

    def test_many_small_tables(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = flatten((
                    [
                        "CREATE TABLE my_table_{} (my_text_col_a text, my_text_col_b text);".format(i),
                        "INSERT INTO my_table_{} VALUES ('some-text-a', 'some-text-b');".format(i),
                    ]
                    for i in range(1, 101)
                ))
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=1000000))
                self.assertEqual([(
                    'my_table_{}'.format(i),
                    (
                        column_constructor(cid=0, name='my_text_col_a', type='text', notnull=0, dflt_value=None, pk=0),
                        column_constructor(cid=1, name='my_text_col_b', type='text', notnull=0, dflt_value=None, pk=0),
                    ),
                    [('some-text-a', 'some-text-b')],
                ) for i in range(1, 101)], all_chunks)

    def test_large_table(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = [
                    "CREATE TABLE my_table_1 (my_text_col_a text, my_text_col_b text);",
                ] + [
                    "INSERT INTO my_table_1 VALUES ('some-text-a', 'some-text-b')",
                ] * 1000
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=0))

                self.assertEqual(
                    [('some-text-a', 'some-text-b')] * 1000,
                    all_chunks[0][2],
                )

    def test_index(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192, 16384, 32768, 65536],
            [1, 2, 3, 5, 7, 32, 131072],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = (
                    ["CREATE TABLE my_table_1 (my_col_a integer);"] +
                    [
                        "INSERT INTO my_table_1 VALUES ({});".format(i)
                        for i in range(0, 1024)
                    ] +
                    ["CREATE INDEX my_index ON my_table_1(my_col_a);"]
                )
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=0))
                self.assertEqual([(
                    "my_table_1",
                    (
                        column_constructor(cid=0, name='my_col_a', type='integer', notnull=0, dflt_value=None, pk=0),
                    ),
                    [(i,) for i in range(0, 1024)],
                )], all_chunks)

    def test_with_pointermap_pages(self):
        for page_size, chunk_size in itertools.product(
            [512, 1024, 4096, 8192],
            [512],
        ):
            with self.subTest(page_size=page_size, chunk_size=chunk_size):
                sqls = (
                    ["PRAGMA auto_vacuum = FULL;"] +
                    ["CREATE TABLE my_table_1 (my_col_a integer);"] +
                    [
                        "INSERT INTO my_table_1 VALUES ({});".format(i)
                        for i in range(0, 20000)
                    ]
                )
                all_chunks = tables_list(stream_sqlite(db(sqls, page_size, chunk_size), buffer_size=20971520))
                self.assertEqual([(
                    "my_table_1",
                    (
                        column_constructor(cid=0, name='my_col_a', type='integer', notnull=0, dflt_value=None, pk=0),
                    ),
                    [(i,) for i in range(0, 20000)],
                )], all_chunks)

    def test_freelist(self):
        sqls = [
            "CREATE TABLE my_table_1 (my_text_col_a text, my_text_col_b text);",
        ] + [
            "INSERT INTO my_table_1 VALUES " + ','.join(["('some-text-a', 'some-text-b')"] * 500),
        ] * 1000 + [
            "DELETE FROM my_table_1",
        ]
        all_chunks = tables_list(stream_sqlite(db(sqls, page_size=1024, chunk_size=131072), buffer_size=20971520))
        self.assertEqual([], all_chunks)

        with self.assertRaises(ValueError):
            all_chunks = tables_list(stream_sqlite(db(sqls, page_size=1024, chunk_size=131072), buffer_size=1048576))

    def test_truncated(self):
        with self.assertRaises(ValueError):
            next(stream_sqlite([b'too-short'], buffer_size=20971520))

    def test_bad_header(self):
        with self.assertRaises(ValueError):
            next(stream_sqlite([b'0123456789'] * 10, buffer_size=20971520))

    def test_bad_encoding(self):
        sqls = [
            "CREATE TABLE my_table_1 (my_text_col_a text, my_text_col_b text);",
        ] + [
            "INSERT INTO my_table_1 VALUES ('some-text-a', 'some-text-b')",
        ]
        db_bytes = bytearray(b''.join(db(sqls, page_size=1024, chunk_size=131072)))
        db_bytes[56] = 99
        with self.assertRaises(ValueError):
            next(tables_list(stream_sqlite([db_bytes], buffer_size=20971520)))

    def test_bad_usable_space(self):
        sqls = [
            "CREATE TABLE my_table_1 (my_text_col_a text, my_text_col_b text);",
        ] + [
            "INSERT INTO my_table_1 VALUES ('some-text-a', 'some-text-b')",
        ]
        db_bytes = bytearray(b''.join(db(sqls, page_size=1024, chunk_size=131072)))
        db_bytes[20] = 1
        with self.assertRaises(ValueError):
            next(stream_sqlite([db_bytes], buffer_size=20971520))

    def test_unused_page(self):
        sqls = [
            "CREATE TABLE my_table_1 (my_text_col_a text, my_text_col_b text);",
        ] + [
            "INSERT INTO my_table_1 VALUES " + ','.join(["('some-text-a', 'some-text-b')"] * 500),
        ] * 1000 + [
            "DELETE FROM my_table_1",
        ]
        db_bytes = bytearray(b''.join(db(sqls, page_size=1024, chunk_size=131072)))
        db_bytes[32:36] = b'\x99\x00\x00\x00'
        with self.assertRaises(ValueError):
            next(tables_list(stream_sqlite([db_bytes], buffer_size=20971520)))

def db(sqls, page_size, chunk_size):
    with tempfile.NamedTemporaryFile() as fp:
        with sqlite3.connect(fp.name, isolation_level=None) as con:
            cur = con.cursor()
            cur.execute('PRAGMA page_size = {};'.format(page_size))
            for sql in sqls:
                cur.execute(sql)

        with open(fp.name, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

def tables_list(table_iter):
    return [
        (table_name, table_info, list(table_rows))
        for table_name, table_info, table_rows in table_iter
    ]


def flatten(l):
    return [
        item
        for sublist in l
        for item in sublist
    ]
