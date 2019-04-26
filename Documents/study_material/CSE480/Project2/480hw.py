import io
import csv
import datetime
import sqlite3


def add_this_class(conn):
  conn.execute("CREATE VIEW this_class AS \
                SELECT grades.name, grades.grade \
                FROM grades WHERE (grades.semester = 'spring_2019' AND grades.course = 'CSE 480')")
  conn.execute("CREATE TRIGGER update_on_this_class \
                INSTEAD OF INSERT ON this_class \
                BEGIN \
                    INSERT INTO grades (name, semester, course, grade) \
                    SELECT old.name, old.semester, old.course, old.grade; \
                END")

