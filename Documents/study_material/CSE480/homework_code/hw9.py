def validate_functional_dependency(connection, all_columns, left_columns, right_columns):
    fd_cache = {}
	result = conn.execute("SELECT " + str(left_columns[-1] + ", " + str(right_columns[-1]) + " FROM TABLE my_table;"))
	return


from sqlite3 import connect


all_columns = ['a', 'b', 'c']
left_columns = ['c']
right_columns = ['a']
data = [
	('josh', 30, 'nahumjos'),
	('emily', 28, 'emily_rocks'),
	('josh', 29, 'nahumjos'),
	('josh', 29, 'other_josh'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (a TEXT, b TEXT, c TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('should be true: ' + str(result))

conn.close()



all_columns = ['a', 'b', 'c']
left_columns = ['c']
right_columns = ['a']
data = [
	('josh', 30, 'nahumjos'),
	('emily', 28, 'emily_rocks'),
	('josh', 29, 'nahumjos'),
	('nahum', 30, 'nahumjos'),
	('josh', 29, 'other_josh'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (a TEXT, b TEXT, c TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('should be false: ' + str(result))

conn.close()


all_columns = ['title', 'year', 'rating', 'director']
left_columns = ['title']
right_columns = ['rating']
data = [
	('The Matrix', 1999, 8.7, 'Lana Wachowski'),
	('The Lord of the Rings: The Fellowship of the Ring', 2001, 8.8, 'Peter Jackson'),
	('Serenity', 2005, 7.9,  'Joss Whedon'),
	('Serenity', 2019, 5.2, 'Steven Knight'),
	('The Matrix: Reloaded', 1999, 8.7, 'Lilly Wachowski'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (title TEXT, year INTEGER, rating REAL, director TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('should be false: ' + str(result))

conn.close()


all_columns = ['title', 'year', 'rating', 'director']
left_columns = ['title', 'year']
right_columns = ['rating']
data = [
	('The Matrix', 1999, 8.7, 'Lana Wachowski'),
	('The Lord of the Rings: The Fellowship of the Ring', 2001, 8.8, 'Peter Jackson'),
	('Serenity', 2005, 7.9,  'Joss Whedon'),
	('Serenity', 2019, 5.2, 'Steven Knight'),
	('The Matrix: Reloaded', 1999, 8.7, 'Lilly Wachowski'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (title TEXT, year INTEGER, rating REAL, director TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('result is true: ' + str(result))

conn.close()


all_columns = ['title', 'year', 'rating', 'director']
left_columns = ['title', 'year']
right_columns = ['rating']
data = [
	('The Matrix', 1999, 8.7, 'Lana Wachowski'),
	('The Lord of the Rings: The Fellowship of the Ring', 2001, 8.8, 'Peter Jackson'),
	('Serenity', 2005, 7.9,  'Joss Whedon'),
	('Serenity', 2019, 5.2, 'Steven Knight'),
	('The Matrix', 1999, 8.7, 'Lilly Wachowski'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (title TEXT, year INTEGER, rating REAL, director TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('result is true: ' + str(result))

conn.close()



all_columns = ['title', 'year', 'rating', 'director']
left_columns = ['title', 'year']
right_columns = ['rating', 'director']
data = [
	('The Matrix', 1999, 8.7, 'Lana Wachowski'),
	('The Lord of the Rings: The Fellowship of the Ring', 2001, 8.8, 'Peter Jackson'),
	('Serenity', 2005, 7.9,  'Joss Whedon'),
	('Serenity', 2019, 5.2, 'Steven Knight'),
	('The Matrix', 1999, 8.7, 'Lilly Wachowski'),
]
conn = connect(":memory:")
conn.execute("CREATE TABLE my_table (title TEXT, year INTEGER, rating REAL, director TEXT);")
conn.executemany("INSERT INTO my_table VALUES (?, ?, ?, ?);", data)

result = validate_functional_dependency(
    conn, all_columns, left_columns, right_columns)
print(f"Result is {result}")
print('should be false: ' + str(result))

conn.close()