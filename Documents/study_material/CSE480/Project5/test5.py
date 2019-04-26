import unittest
from pprint import pprint
from project import connect  # , reset_state


class TestsProject5(unittest.TestCase):
    # NOTE: This function is called after each test is ran (often referred to
    # as the cleanup function). You may need to make a function that resets
    # the state of your program (i.e remove all databases and clear all locks)
    # in order to run the tests one after the other, otherwise your program
    # may throw errors (i.e trying to create a table that shouldn't exist but
    # does due to a previous test).
    def tearDown(self):
        # reset_state()
        pass

    def check(self, conn, sql_statement, expected):
        print("SQL: " + sql_statement)
        result = conn.execute(sql_statement)
        result_list = list(result)

        print("expected:")
        pprint(expected)
        print("student: ")
        pprint(result_list)
        assert expected == result_list

    def test_regression(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, course INTEGER);")
        conn.execute("CREATE TABLE profs (name TEXT, course INTEGER);")

        conn.execute("""INSERT INTO students VALUES ('Zizhen', 4.0, 450),
        ('Cam', 3.5, 480),
        ('Cam', 3.0, 450),
        ('Jie', 0.0, 231),
        ('Jie', 2.0, 331),
        ('Anne', 3.0, 231),
        ('Josh', 1.0, 231),
        ('Josh', 0.0, 480),
        ('Josh', 0.0, 331);""")

        conn.execute("""INSERT INTO profs VALUES ('Josh', 480),
        ('Josh', 450),
        ('Rich', 231),
        ('Sebnem', 331);""")

        self.check(
            conn,
            """SELECT profs.name, students.grade, students.name
            FROM students LEFT OUTER JOIN profs ON students.course = profs.course
            WHERE students.grade > 0.0 ORDER BY students.name, profs.name, students.grade;""",
            [('Rich', 3.0, 'Anne'),
             ('Josh', 3.0, 'Cam'),
             ('Josh', 3.5, 'Cam'),
             ('Sebnem', 2.0, 'Jie'),
             ('Rich', 1.0, 'Josh'),
             ('Josh', 4.0, 'Zizhen')])

    def test_desc_basic(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, course INTEGER);")
        conn.execute("CREATE TABLE profs (name TEXT, course INTEGER);")

        conn.execute("""INSERT INTO students VALUES ('Zizhen', 4.0, 450),
        ('Cam', 3.5, 480),
        ('Cam', 3.0, 450),
        ('Jie', 0.0, 231),
        ('Jie', 2.0, 331),
        ('Dennis', 2.0, 331),
        ('Dennis', 2.0, 231),
        ('Anne', 3.0, 231),
        ('Josh', 1.0, 231),
        ('Josh', 0.0, 480),
        ('Josh', 0.0, 331);""")

        conn.execute("""INSERT INTO profs VALUES ('Josh', 480),
        ('Josh', 450),
        ('Rich', 231),
        ('Sebnem', 331);""")

        self.check(
            conn,
            """SELECT students.name
            FROM students ORDER BY students.name DESC;""",
            [('Zizhen',),
             ('Josh',),
             ('Josh',),
             ('Josh',),
             ('Jie',),
             ('Jie',),
             ('Dennis',),
             ('Dennis',),
             ('Cam',),
             ('Cam',),
             ('Anne',)])

    def test_desc_advanced(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, course INTEGER);")
        conn.execute("CREATE TABLE profs (name TEXT, course INTEGER);")

        conn.execute("""INSERT INTO students VALUES ('Zizhen', 4.0, 450),
        ('Cam', 3.5, 480),
        ('Cam', 3.0, 450),
        ('Jie', 0.0, 231),
        ('Jie', 2.0, 331),
        ('Dennis', 2.0, 331),
        ('Dennis', 2.0, 231),
        ('Anne', 3.0, 231),
        ('Josh', 1.0, 231),
        ('Josh', 0.0, 480),
        ('Josh', 0.0, 331);""")

        conn.execute("""INSERT INTO profs VALUES ('Josh', 480),
        ('Josh', 450),
        ('Rich', 231),
        ('Sebnem', 331);""")

        self.check(
            conn,
            """SELECT profs.name, students.grade, students.name
            FROM students LEFT OUTER JOIN profs ON students.course = profs.course
            WHERE students.grade > 0.0 ORDER BY students.grade, students.name DESC, profs.name DESC;""",
            [('Rich', 1.0, 'Josh'),
             ('Sebnem', 2.0, 'Jie'),
             ('Sebnem', 2.0, 'Dennis'),
             ('Rich', 2.0, 'Dennis'),
             ('Josh', 3.0, 'Cam'),
             ('Rich', 3.0, 'Anne'),
             ('Josh', 3.5, 'Cam'),
             ('Josh', 4.0, 'Zizhen')])

    def test_desc_hidden_help(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, course INTEGER);")
        conn.execute("CREATE TABLE profs (name TEXT, course INTEGER);")

        conn.execute("""INSERT INTO students VALUES ('Zizhen', 4.0, 450),
        ('Cam', 3.5, 480),
        ('Cam', 3.0, 450),
        ('Jie', 0.0, 231),
        ('Jie', 2.0, 331),
        ('Dennis', 2.0, 331),
        ('Zach', 1.0, 480),
        ('Dennis', 2.0, 231),
        ('Anne', 3.0, 231),
        ('Josh', 1.0, 231),
        ('Josh', 0.0, 480),
        ('Josh', 0.5, 491),
        ('Josh', 0.0, 331);""")

        conn.execute("""INSERT INTO profs VALUES ('Josh', 480),
        ('Josh', 450),
        ('Charles', 491),
        ('Rich', 231),
        ('Sebnem', 331);""")

        self.check(
            conn,
            """SELECT profs.name, students.grade, students.name
            FROM students LEFT OUTER JOIN profs ON students.course = profs.course
            WHERE students.grade < 4.0 ORDER BY students.grade DESC, students.name, profs.name DESC;""",
            [('Josh', 3.5, 'Cam'),
             ('Rich', 3.0, 'Anne'),
             ('Josh', 3.0, 'Cam'),
             ('Sebnem', 2.0, 'Dennis'),
             ('Rich', 2.0, 'Dennis'),
             ('Sebnem', 2.0, 'Jie'),
             ('Rich', 1.0, 'Josh'),
             ('Josh', 1.0, 'Zach'),
             ('Charles', 0.5, 'Josh'),
             ('Rich', 0.0, 'Jie'),
             ('Sebnem', 0.0, 'Josh'),
             ('Josh', 0.0, 'Josh')])

    def test_default_values(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL DEFAULT 0.0, id TEXT);")

        conn.execute("INSERT INTO students VALUES ('Zizhen', 4.0, 'Hi');")
        conn.execute(
            "INSERT INTO students (name, id) VALUES ('Cam', 'Hello');")
        conn.execute(
            "INSERT INTO students (id, name) VALUES ('Instructor', 'Josh');")
        conn.execute(
            "INSERT INTO students (id, name, grade) VALUES ('TA', 'Dennis', 3.0);")
        conn.execute(
            "INSERT INTO students (id, name) VALUES ('regular', 'Emily'), ('regular', 'Alex');")

        self.check(
            conn,
            """SELECT name, id, grade  FROM students ORDER BY students.name;""",
            [('Alex', 'regular', 0.0),
             ('Cam', 'Hello', 0.0),
             ('Dennis', 'TA', 3.0),
             ('Emily', 'regular', 0.0),
             ('Josh', 'Instructor', 0.0),
             ('Zizhen', 'Hi', 4.0)])

    def test_default_values_all(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT DEFAULT '', health INTEGER DEFAULT 100, grade REAL DEFAULT 0.0, id TEXT DEFAULT 'NONE PROVIDED');")

        conn.execute("INSERT INTO students VALUES ('Zizhen', 45, 4.0, 'Hi');")
        conn.execute("INSERT INTO students DEFAULT VALUES;")
        conn.execute(
            "INSERT INTO students (name, id) VALUES ('Cam', 'Hello');")
        conn.execute(
            "INSERT INTO students (id, name) VALUES ('Instructor', 'Josh');")
        conn.execute("INSERT INTO students DEFAULT VALUES;")

        conn.execute(
            "INSERT INTO students (id, name, grade) VALUES ('TA', 'Dennis', 3.0);")
        conn.execute(
            "INSERT INTO students (id, name) VALUES ('regular', 'Emily'), ('regular', 'Alex');")

        self.check(
            conn,
            """SELECT name, id, grade, health  FROM students ORDER BY students.name;""",
            [('', 'NONE PROVIDED', 0.0, 100),
             ('', 'NONE PROVIDED', 0.0, 100),
             ('Alex', 'regular', 0.0, 100),
             ('Cam', 'Hello', 0.0, 100),
             ('Dennis', 'TA', 3.0, 100),
             ('Emily', 'regular', 0.0, 100),
             ('Josh', 'Instructor', 0.0, 100),
             ('Zizhen', 'Hi', 4.0, 45)])

    def test_default_values_hidden_help(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT DEFAULT '', health INTEGER DEFAULT 100, grade REAL DEFAULT 0.0, id TEXT DEFAULT 'NONE PROVIDED');")

        conn.execute("INSERT INTO students VALUES ('Zizhen', 45, 4.0, 'Hi');")
        conn.execute("INSERT INTO students DEFAULT VALUES;")
        conn.execute(
            "INSERT INTO students (name, id) VALUES ('Cam', 'Hello'), ('Jie', 'Hi!');")
        conn.execute(
            "INSERT INTO students (id, name, health) VALUES ('Instructor', 'Josh', 99);")
        conn.execute("INSERT INTO students DEFAULT VALUES;")

        conn.execute(
            "INSERT INTO students (id, name, grade) VALUES ('TA', 'Dennis', 3.0);")
        conn.execute(
            "INSERT INTO students (id, name) VALUES ('regular', 'Emily'), ('regular', 'Alex');")

        self.check(
            conn,
            """SELECT name, health, id, grade FROM students ORDER BY health, students.name;""",
            [('Zizhen', 45, 'Hi', 4.0),
             ('Josh', 99, 'Instructor', 0.0),
             ('', 100, 'NONE PROVIDED', 0.0),
             ('', 100, 'NONE PROVIDED', 0.0),
             ('Alex', 100, 'regular', 0.0),
             ('Cam', 100, 'Hello', 0.0),
             ('Dennis', 100, 'TA', 3.0),
             ('Emily', 100, 'regular', 0.0),
             ('Jie', 100, 'Hi!', 0.0)])

    def test_views(self):
        conn = connect("test1.db")
        conn.execute("CREATE TABLE students (name TEXT, grade REAL);")
        conn.execute(
            "CREATE VIEW stu_view AS SELECT * FROM students WHERE grade > 3.0 ORDER BY name;")

        self.check(
            conn,
            """SELECT name FROM stu_view ORDER BY grade;""",
            [])

        conn.execute("""INSERT INTO students VALUES
        ('Josh', 3.5),
        ('Dennis', 2.5),
        ('Cam', 1.5),
        ('Zizhen', 4.0)
        ;""")

        self.check(
            conn,
            """SELECT name FROM stu_view ORDER BY grade;""",
            [('Josh',), ('Zizhen',)])

        conn.execute("""INSERT INTO students VALUES
        ('Emily', 3.7),
        ('Alex', 2.5),
        ('Jake', 3.2)
        ;""")

        self.check(
            conn,
            """SELECT name FROM stu_view ORDER BY grade;""",
            [('Jake',), ('Josh',), ('Emily',), ('Zizhen',)])

    def test_views_advanced(self):
        conn = connect("test1.db")
        conn.execute("CREATE TABLE students (name TEXT, grade REAL);")
        conn.execute(
            "CREATE VIEW stu_view AS SELECT * FROM students WHERE grade > 3.0 ORDER BY name;")

        self.check(
            conn,
            """SELECT name FROM stu_view ORDER BY grade;""",
            [])

        conn.execute("""INSERT INTO students VALUES
        ('Josh', 3.5),
        ('Dennis', 2.5),
        ('Cam', 1.5),
        ('Zizhen', 4.0)
        ;""")

        self.check(
            conn,
            """SELECT name FROM stu_view ORDER BY grade;""",
            [('Josh',), ('Zizhen',)])

        conn.execute("""INSERT INTO students VALUES
        ('Emily', 3.7),
        ('Alex', 2.5),
        ('Jake', 3.2)
        ;""")

        self.check(
            conn,
            """SELECT grade, name FROM stu_view WHERE name < 'W' ORDER BY grade DESC;""",
            [(3.7, 'Emily'), (3.5, 'Josh'), (3.2, 'Jake')])

        conn.execute(
            "CREATE TABLE enroll (student_name TEXT, course INTEGER);")
        conn.execute("""INSERT INTO enroll VALUES
        ('Josh', 480),
        ('Dennis', 331),
        ('Emily', 231),
        ('Zizhen', 231)
        ;""")

        self.check(
            conn,
            """SELECT students.name, students.grade, enroll.course
            FROM students LEFT OUTER JOIN enroll ON students.name = enroll.student_name
            ORDER BY students.name DESC;""",
            [('Zizhen', 4.0, 231),
             ('Josh', 3.5, 480),
             ('Jake', 3.2, None),
             ('Emily', 3.7, 231),
             ('Dennis', 2.5, 331),
             ('Cam', 1.5, None),
             ('Alex', 2.5, None)])

        conn.execute("""CREATE VIEW stu_view2 AS
        SELECT students.name, students.grade, enroll.course
        FROM students LEFT OUTER JOIN enroll ON students.name = enroll.student_name
        ORDER BY students.name DESC;
        """)

        self.check(
            conn,
            """SELECT name, course
            FROM stu_view2 WHERE grade > 2.0
            ORDER BY grade, name;""",
            [('Alex', None),
             ('Dennis', 331),
             ('Jake', None),
             ('Josh', 480),
             ('Emily', 231),
             ('Zizhen', 231)])

        conn.execute("""INSERT INTO enroll VALUES ('Jake', 480);""")

        self.check(
            conn,
            """SELECT name, course
            FROM stu_view2 WHERE grade > 2.0
            ORDER BY grade DESC, name;""",
            [('Zizhen', 231),
             ('Emily', 231),
             ('Josh', 480),
             ('Jake', 480),
             ('Alex', None),
             ('Dennis', 331)])

    def test_param_queries(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, 480);",
                         [('Josh', 3.5), ('Tyler', 2.5), ('Grant', 3.0)])

        self.check(
            conn,
            """SELECT name, class, grade FROM students ORDER BY grade;""",
            [('Tyler', 480, 2.5), ('Grant', 480, 3.0), ('Josh', 480, 3.5)])

    def test_param_queries_more(self):
        conn = connect("test1.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER DEFAULT 231);")
        conn.executemany("INSERT INTO students VALUES (?, ?, 480);", [
                        ('Josh', 3.5), ('Tyler', 2.5), ('Grant', 3.0)])
        conn.executemany("INSERT INTO students VALUES (?, 0.0, ?);",
                         [('Jim', 231), ('Tim', 331), ('Gary', 450)])

        conn.executemany("INSERT INTO students (grade, name) VALUES (?, ?);", [
                        (4.1, 'Tess'), (1.1, 'Jane')])

        self.check(
            conn,
            """SELECT name, class, grade FROM students ORDER BY grade, name;""",
            [('Gary', 450, 0.0),
             ('Jim', 231, 0.0),
             ('Tim', 331, 0.0),
             ('Jane', 231, 1.1),
             ('Tyler', 480, 2.5),
             ('Grant', 480, 3.0),
             ('Josh', 480, 3.5),
             ('Tess', 231, 4.1)])

    def test_custom_collation(self):
        conn = connect("test.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, ?);",
                         [('Josh', 3.5, 480),
                          ('Tyler', 2.5, 480),
                          ('Tosh', 4.5, 450),
                          ('Losh', 3.2, 450),
                          ('Grant', 3.3, 480),
                          ('Emily', 2.25, 450),
                          ('James', 2.25, 450)])
        self.check(
            conn,
            "SELECT * FROM students ORDER BY class, name;",
            [('Emily', 2.25, 450),
             ('James', 2.25, 450),
             ('Losh', 3.2, 450),
             ('Tosh', 4.5, 450),
             ('Grant', 3.3, 480),
             ('Josh', 3.5, 480),
             ('Tyler', 2.5, 480)])

        def collate_ignore_first_letter(string1, string2):
            string1 = string1[1:]
            string2 = string2[1:]
            if string1 == string2:
                return 0
            if string1 < string2:
                return -1
            else:
                return 1

        conn.create_collation("skip", collate_ignore_first_letter)

        self.check(
            conn,
            "SELECT * FROM students ORDER BY name COLLATE skip, grade;",
            [('James', 2.25, 450),
             ('Emily', 2.25, 450),
             ('Losh', 3.2, 450),
             ('Josh', 3.5, 480),
             ('Tosh', 4.5, 450),
             ('Grant', 3.3, 480),
             ('Tyler', 2.5, 480)])

    def test_custom_collation_desc(self):
        conn = connect("test.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, ?);",
                         [('Josh', 3.5, 480),
                          ('Tyler', 2.5, 480),
                          ('Tosh', 4.5, 450),
                          ('Losh', 3.2, 450),
                          ('Grant', 3.3, 480),
                          ('Emily', 2.25, 450),
                          ('James', 2.25, 450)])
        self.check(
            conn,
            "SELECT * FROM students ORDER BY class, name;",
            [('Emily', 2.25, 450),
             ('James', 2.25, 450),
             ('Losh', 3.2, 450),
             ('Tosh', 4.5, 450),
             ('Grant', 3.3, 480),
             ('Josh', 3.5, 480),
             ('Tyler', 2.5, 480)])

        def collate_ignore_first_letter(string1, string2):
            string1 = string1[1:]
            string2 = string2[1:]
            if string1 == string2:
                return 0
            if string1 < string2:
                return -1
            else:
                return 1

        conn.create_collation("skip", collate_ignore_first_letter)

        self.check(
            conn,
            "SELECT students.name FROM students ORDER BY name COLLATE skip;",
            [('James',),
             ('Emily',),
             ('Tosh',),
             ('Josh',),
             ('Losh',),
             ('Grant',),
             ('Tyler',)])

        self.check(
            conn,
            "SELECT * FROM students ORDER BY name COLLATE skip DESC, grade;",
            [('Tyler', 2.5, 480),
             ('Grant', 3.3, 480),
             ('Losh', 3.2, 450),
             ('Josh', 3.5, 480),
             ('Tosh', 4.5, 450),
             ('Emily', 2.25, 450),
             ('James', 2.25, 450)])

        self.check(
            conn,
            "SELECT * FROM students WHERE class = 480 ORDER BY grade DESC, name COLLATE skip DESC;",
            [('Josh', 3.5, 480), ('Grant', 3.3, 480), ('Tyler', 2.5, 480)])

    def test_custom_collation_more(self):
        conn = connect("test.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, ?);",
                         [('Josh', 3.5, 480),
                          ('Tyler', 2.5, 480),
                          ('Alice', 2.2, 231),
                          ('Tosh', 4.5, 450),
                          ('Losh', 3.2, 450),
                          ('Grant', 3.3, 480),
                          ('Emily', 2.25, 450),
                          ('James', 2.25, 450)])

        self.check(
            conn,
            "SELECT * FROM students ORDER BY class, name;",
            [('Alice', 2.2, 231),
             ('Emily', 2.25, 450),
             ('James', 2.25, 450),
             ('Losh', 3.2, 450),
             ('Tosh', 4.5, 450),
             ('Grant', 3.3, 480),
             ('Josh', 3.5, 480),
             ('Tyler', 2.5, 480)])

        def collate_ignore_first_two_letter(string1, string2):
            string1 = string1[2:]
            string2 = string2[2:]
            if string1 == string2:
                return 0
            if string1 < string2:
                return -1
            else:
                return 1

        conn.create_collation("skip2", collate_ignore_first_two_letter)

        self.check(
            conn,
            "SELECT * FROM students ORDER BY name COLLATE skip2 DESC, grade;",
            [('Losh', 3.2, 450),
             ('Josh', 3.5, 480),
             ('Tosh', 4.5, 450),
             ('James', 2.25, 450),
             ('Tyler', 2.5, 480),
             ('Emily', 2.25, 450),
             ('Alice', 2.2, 231),
             ('Grant', 3.3, 480)])

        self.check(
            conn,
            "SELECT * FROM students WHERE class = 480 ORDER BY grade DESC, name COLLATE skip2 DESC;",
            [('Josh', 3.5, 480), ('Grant', 3.3, 480), ('Tyler', 2.5, 480)])

    def test_aggregate_functions(self):
        conn = connect("test.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, ?);",
                         [('Josh', 3.5, 480),
                          ('Tyler', 2.5, 480),
                          ('Tosh', 4.5, 450),
                          ('Losh', 3.2, 450),
                          ('Grant', 3.3, 480),
                          ('Emily', 2.25, 450),
                          ('James', 2.25, 450)])
        self.check(
            conn,
            "SELECT max(grade) FROM students ORDER BY grade;",
            [(4.5,)])

        self.check(
            conn,
            "SELECT min(class), max(name) FROM students ORDER BY grade, name;",
            [(450, 'Tyler')])

    def test_aggregate_functions_where(self):
        conn = connect("test.db")
        conn.execute(
            "CREATE TABLE students (name TEXT, grade REAL, class INTEGER);")
        conn.executemany("INSERT INTO students VALUES (?, ?, ?);",
                         [('Josh', 3.5, 480),
                          ('Tyler', 2.5, 480),
                          ('Tosh', 4.5, 450),
                          ('Losh', 3.2, 450),
                          ('Grant', 3.3, 480),
                          ('Emily', 2.25, 450),
                          ('James', 2.25, 450)])
        self.check(
            conn,
            "SELECT max(grade) FROM students WHERE class = 480 ORDER BY grade;",
            [(3.5,)])

        self.check(
            conn,
            "SELECT min(grade), min(name) FROM students WHERE name > 'T' ORDER BY grade, name;",
            [(2.5, 'Tosh')])


if __name__ == "__main__":
    tests = TestsProject5()
    tests.test_custom_collation_desc()
