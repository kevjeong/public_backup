"""
Name: Kevin Jeong
Time To Completion: 2 Hours
Comments:

Sources:
"""
import copy
import string
from operator import itemgetter
from collections import namedtuple
import itertools

_ALL_DATABASES = {}
global connection_count
connection_count = 0

WhereClause = namedtuple("WhereClause", ["col_name", "operator", "constant"])
UpdateClause = namedtuple("UpdateClause", ["col_name", "constant"])
FromJoinClause = namedtuple("FromJoinClause", ["left_table_name",
                                               "right_table_name",
                                               "left_join_col_name",
                                               "right_join_col_name"])


class Connection(object):

    def __init__(self, filename):
        """
        Takes a filename, but doesn't do anything with it.
        (The filename will be used in a future project).
        """
        if filename in _ALL_DATABASES:
            self.database = _ALL_DATABASES[filename]
        else:
            self.database = Database(filename)
            _ALL_DATABASES[filename] = self.database

        global connection_count
        self.id = connection_count
        self.rollback = False
        self.begin_transaction = False
        self.cached_database = {}
        connection_count += 1

    def execute(self, statement):
        """
        Takes a SQL statement.
        Returns a list of tuples (empty unless select statement
        with rows to return).
        """

        def create_table(tokens):
            """
            Determines the name and column information from tokens add
            has the database create a new table within itself.
            """
            pop_and_check(tokens, "CREATE")
            pop_and_check(tokens, "TABLE")
            if tokens[0] == "IF":
                tokens = tokens[3:]
                if self.database.check_table_exists(tokens[0]):
                    return
            table_name = tokens.pop(0)
            pop_and_check(tokens, "(")
            column_name_type_pairs = []
            while True:
                column_name = tokens.pop(0)
                qual_col_name = QualifiedColumnName(column_name, table_name)
                column_type = tokens.pop(0)
                assert column_type in {"TEXT", "INTEGER", "REAL"}
                column_name_type_pairs.append((qual_col_name, column_type))
                comma_or_close = tokens.pop(0)
                if comma_or_close == ")":
                    break
                assert comma_or_close == ','
            self.database.create_new_table(table_name, column_name_type_pairs)

        def insert(tokens):
            """
            Determines the table name and row values to add.
            """

            def get_comma_seperated_contents(tokens):
                contents = []
                pop_and_check(tokens, "(")
                while True:
                    item = tokens.pop(0)
                    contents.append(item)
                    comma_or_close = tokens.pop(0)
                    if comma_or_close == ")":
                        return contents
                    assert comma_or_close == ',', comma_or_close

            if self.database.exclusive_lock is not None and self.database.exclusive_lock != self.id:
                raise AssertionError
            elif self.database.reserved_lock is not None and self.database.reserved_lock != self.id:
                if self.database.reserved_lock != self.id:
                    raise AssertionError
                _ALL_DATABASES[self.database.filename].reserved_lock = self.id
            elif self.database.exclusive_lock is None and self.database.reserved_lock is None:
                if self.begin_transaction:
                    self.database.reserved_lock = self.id
            pop_and_check(tokens, "INSERT")
            pop_and_check(tokens, "INTO")
            table_name = tokens.pop(0)
            if tokens[0] == "(":
                col_names = get_comma_seperated_contents(tokens)
                qual_col_names = [QualifiedColumnName(col_name, table_name)
                                  for col_name in col_names]
            else:
                qual_col_names = None
            pop_and_check(tokens, "VALUES")
            while tokens:
                row_contents = get_comma_seperated_contents(tokens)
                if qual_col_names:
                    assert len(row_contents) == len(qual_col_names)
                if self.begin_transaction and not self.rollback:
                    self.cached_database.insert_into(table_name,
                                                     row_contents,
                                                     qual_col_names=qual_col_names)
                else:
                    _ALL_DATABASES[self.database.filename].insert_into(table_name,
                                              row_contents,
                                              qual_col_names=qual_col_names)
                if tokens:
                    pop_and_check(tokens, ",")

        def get_qualified_column_name(tokens):
            """
            Returns comsumes tokens to  generate tuples to create
            a QualifiedColumnName.
            """
            possible_col_name = tokens.pop(0)
            if tokens and tokens[0] == '.':
                tokens.pop(0)
                actual_col_name = tokens.pop(0)
                table_name = possible_col_name
                return QualifiedColumnName(actual_col_name, table_name)
            return QualifiedColumnName(possible_col_name)

        def update(tokens):
            if self.begin_transaction:
                if self.database.reserved_lock != self.id:
                    raise AssertionError
            pop_and_check(tokens, "UPDATE")
            table_name = tokens.pop(0)
            pop_and_check(tokens, "SET")
            update_clauses = []
            while tokens:
                qual_name = get_qualified_column_name(tokens)
                if not qual_name.table_name:
                    qual_name.table_name = table_name
                pop_and_check(tokens, '=')
                constant = tokens.pop(0)
                update_clause = UpdateClause(qual_name, constant)
                update_clauses.append(update_clause)
                if tokens:
                    if tokens[0] == ',':
                        tokens.pop(0)
                        continue
                    elif tokens[0] == "WHERE":
                        break

            where_clause = get_where_clause(tokens, table_name)

            self.database.update(table_name, update_clauses, where_clause)

        def delete(tokens):
            pop_and_check(tokens, "DELETE")
            pop_and_check(tokens, "FROM")
            table_name = tokens.pop(0)
            where_clause = get_where_clause(tokens, table_name)
            self.database.delete(table_name, where_clause)

        def get_where_clause(tokens, table_name):
            if not tokens or tokens[0] != "WHERE":
                return None
            tokens.pop(0)
            qual_col_name = get_qualified_column_name(tokens)
            if not qual_col_name.table_name:
                qual_col_name.table_name = table_name
            operators = {">", "<", "=", "!=", "IS"}
            found_operator = tokens.pop(0)
            assert found_operator in operators
            if tokens[0] == "NOT":
                tokens.pop(0)
                found_operator += " NOT"
            constant = tokens.pop(0)
            if constant is None:
                assert found_operator in {"IS", "IS NOT"}
            if found_operator in {"IS", "IS NOT"}:
                assert constant is None
            return WhereClause(qual_col_name, found_operator, constant)

        def select(tokens):
            """
            Determines the table name, output_columns, and order_by_columns.
            """

            def get_from_join_clause(tokens):
                left_table_name = tokens.pop(0)
                if tokens[0] != "LEFT":
                    return FromJoinClause(left_table_name, None, None, None)
                pop_and_check(tokens, "LEFT")
                pop_and_check(tokens, "OUTER")
                pop_and_check(tokens, "JOIN")
                right_table_name = tokens.pop(0)
                pop_and_check(tokens, "ON")
                left_col_name = get_qualified_column_name(tokens)
                pop_and_check(tokens, "=")
                right_col_name = get_qualified_column_name(tokens)
                return FromJoinClause(left_table_name,
                                      right_table_name,
                                      left_col_name,
                                      right_col_name)

            if self.database.exclusive_lock is not None:
                if self.database.exclusive_lock != self.id:
                    if not self.begin_transaction:
                        raise AssertionError
            global connection_count
            if self.begin_transaction:
                _ALL_DATABASES[self.database.filename].shared_locks.append(self.id)
            pop_and_check(tokens, "SELECT")
            is_distinct = tokens[0] == "DISTINCT"
            if is_distinct:
                tokens.pop(0)
            output_columns = []
            while True:
                qual_col_name = get_qualified_column_name(tokens)
                output_columns.append(qual_col_name)
                comma_or_from = tokens.pop(0)
                if comma_or_from == "FROM":
                    break
                assert comma_or_from == ','

            # FROM or JOIN
            from_join_clause = get_from_join_clause(tokens)
            table_name = from_join_clause.left_table_name

            # WHERE
            where_clause = get_where_clause(tokens, table_name)

            # ORDER BY
            pop_and_check(tokens, "ORDER")
            pop_and_check(tokens, "BY")
            order_by_columns = []
            while True:
                qual_col_name = get_qualified_column_name(tokens)
                order_by_columns.append(qual_col_name)
                if not tokens:
                    break
                pop_and_check(tokens, ",")
            if self.begin_transaction or self.rollback:
                return self.cached_database.select(
                    output_columns,
                    order_by_columns,
                    from_join_clause=from_join_clause,
                    where_clause=where_clause,
                    is_distinct=is_distinct)
            return _ALL_DATABASES[self.database.filename].select(
                output_columns,
                order_by_columns,
                from_join_clause=from_join_clause,
                where_clause=where_clause,
                is_distinct=is_distinct)

        def drop(tokens):
            pop_and_check(tokens, "DROP")
            pop_and_check(tokens, "TABLE")
            if tokens[0] == "IF":
                table_name = tokens[2]
                if table_name not in self.database.tables:
                    return []
                else:
                    del self.database.tables[table_name]
            else:
                table_name = tokens[0]
                if table_name not in self.database.tables:
                    raise AssertionError
                del self.database.tables[table_name]

        def rollback():
            if not self.rollback:
                if self.database.reserved_lock == self.id:
                    self.database.reserved_lock = None
                if self.database.exclusive_lock == self.id:
                    self.database.exclusive_lock = None
                for lock in self.database.shared_locks:
                    if lock == self.id:
                        self.database.shared_locks.remove(lock)
                self.begin_transaction = False
                self.rollback = True
                self.database = _ALL_DATABASES[self.database.filename]
                self.cached_database = _ALL_DATABASES[self.database.filename]
            else:
                raise AssertionError

        def begin_transaction(tokens):
            if self.begin_transaction:
                self.database = self.cached_database
                raise AssertionError
            if tokens[1] == "EXCLUSIVE":
                if self.database.exclusive_lock is not None and self.database.exclusive_lock != self.id:
                    raise AssertionError
                if self.database.reserved_lock is not None and self.database.reserved_lock != self.id or len(self.database.shared_locks) > 0:
                    raise AssertionError
                else:
                    self.database.exclusive_lock = self.id
            elif tokens[1] == "IMMEDIATE":
                if self.database.reserved_lock is not None and self.database.reserved_lock != self.id:
                    raise AssertionError
                else:
                    self.database.reserved_lock = self.id
            self.begin_transaction = True
            self.cached_database = copy.deepcopy(self.database)

        def commit_transaction():
            if not self.begin_transaction:
                raise AssertionError
            else:
                if self.database.exclusive_lock is not None:
                    if self.database.reserved_lock is not None and self.database.reserved_lock != self.id:
                        if self.database_.exclusivelock != self.database.reserved_lock:
                            raise AssertionError
                    elif len(self.database.shared_locks) > 0:
                        raise AssertionError
                elif self.database.reserved_lock is not None:
                    if self.database.exclusive_lock is not None:
                        raise AssertionError
                    elif len(self.database.shared_locks) > 0:
                        for lock in self.database.shared_locks:
                            if lock != self.id:
                                if lock == self.database.reserved_lock:
                                    continue
                                else:
                                    if self.rollback:
                                        continue
                                    raise AssertionError
                    if self.database.exclusive_lock is None:
                        if self.database.reserved_lock == self.id:
                            self.database.exclusive_lock = self.id
                else:
                    shared_commit = False
                    new_shared_locks = self.database.shared_locks
                    for lock in reversed(new_shared_locks):
                        if not shared_commit and lock == self.id:
                            shared_commit = True
                            self.database.shared_locks.pop()
                            continue
                        else:
                            if shared_commit and lock == self.id:
                                self.database.shared_locks.pop()
                                continue
                            elif shared_commit and lock != self.id:
                                continue
                            raise AssertionError
            _ALL_DATABASES[self.database.filename] = self.cached_database
            self.begin_transaction = False
            if self.database.exclusive_lock == self.id:
                self.database.exclusive_lock = None
            elif self.database.reserved_lock == self.id:
                self.database.reserved_lock = None
            else:
                new_shared_locks = []
                for lock in self.database.shared_locks:
                    if lock != self.id:
                        new_shared_locks.append(lock)
                self.database.shared_locks = new_shared_locks


        tokens = tokenize(statement)
        last_semicolon = tokens.pop()
        assert last_semicolon == ";"

        if tokens[0] == "CREATE":
            create_table(tokens)
            return []
        elif tokens[0] == "BEGIN":
            begin_transaction(tokens)
        elif tokens[0] == "COMMIT":
            commit_transaction(tokens)
        elif tokens[0] == "ROLLBACK":
            rollback()
        elif tokens[0] == "INSERT":
            insert(tokens)
            return []
        elif tokens[0] == "UPDATE":
            update(tokens)
            return []
        elif tokens[0] == "DELETE":
            delete(tokens)
            return []
        elif tokens[0] == "SELECT":
            return select(tokens)
        elif tokens[0] == "DROP":
            return drop(tokens)
        else:
            raise AssertionError(
                "Unexpected first word in statements: " + tokens[0])

    def close(self):
        """
        Empty method that will be used in future projects
        """
        pass


def connect(filename, timeout=None, isolation_level=None):
    """
    Creates a Connection object with the given filename
    """
    return Connection(filename)


class QualifiedColumnName:

    def __init__(self, col_name, table_name=None):
        self.col_name = col_name
        self.table_name = table_name

    def __str__(self):
        return "QualifiedName({}.{})".format(
            self.table_name, self.col_name)

    def __eq__(self, other):
        same_col = self.col_name == other.col_name
        if not same_col:
            return False
        both_have_tables = (self.table_name is not None and
                            other.col_name is not None)
        if not both_have_tables:
            return True
        return self.table_name == other.table_name

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash((self.col_name, self.table_name))

    def __repr__(self):
        return str(self)


class Database:

    def __init__(self, filename):
        self.filename = filename
        self.tables = {}
        self.transactions = {}
        self.shared_locks = []
        self.exclusive_lock = None
        self.reserved_lock = None

    def check_table_exists(self, table_name):
        if table_name in self.tables:
            return True
        return False

    def create_new_table(self, table_name, column_name_type_pairs):
        assert table_name not in self.tables
        self.tables[table_name] = Table(table_name, column_name_type_pairs)
        return []

    def insert_into(self, table_name, row_contents, qual_col_names=None):
        assert table_name in self.tables
        table = self.tables[table_name]
        table.insert_new_row(row_contents, qual_col_names=qual_col_names)
        return []

    def update(self, table_name, update_clauses, where_clause):
        assert table_name in self.tables
        table = self.tables[table_name]
        table.update(update_clauses, where_clause)

    def delete(self, table_name, where_clause):
        assert table_name in self.tables
        table = self.tables[table_name]
        table.delete(where_clause)

    def select(self, output_columns, order_by_columns,
               from_join_clause,
               where_clause=None, is_distinct=False):
        assert from_join_clause.left_table_name in self.tables
        if from_join_clause.right_table_name:
            assert from_join_clause.right_table_name in self.tables
            left_table = self.tables[from_join_clause.left_table_name]
            right_table = self.tables[from_join_clause.right_table_name]
            all_columns = itertools.chain(
                zip(left_table.column_names, left_table.column_types),
                zip(right_table.column_names, right_table.column_types))
            left_col = from_join_clause.left_join_col_name
            right_col = from_join_clause.right_join_col_name
            join_table = Table("", all_columns)
            combined_rows = []
            for left_row in left_table.rows:
                left_value = left_row[left_col]
                found_match = False
                for right_row in right_table.rows:
                    right_value = right_row[right_col]
                    if left_value is None:
                        break
                    if right_value is None:
                        continue
                    if left_row[left_col] == right_row[right_col]:
                        new_row = dict(left_row)
                        new_row.update(right_row)
                        combined_rows.append(new_row)
                        found_match = True
                        continue
                if left_value is None or not found_match:
                    new_row = dict(left_row)
                    new_row.update(zip(right_row.keys(),
                                       itertools.repeat(None)))
                    combined_rows.append(new_row)

            join_table.rows = combined_rows
            table = join_table
        else:
            table = self.tables[from_join_clause.left_table_name]
        return table.select_rows(output_columns, order_by_columns,
                                 where_clause=where_clause,
                                 is_distinct=is_distinct)


class Table:

    def __init__(self, name, column_name_type_pairs):
        self.name = name
        self.column_names, self.column_types = zip(*column_name_type_pairs)
        self.rows = []

    def insert_new_row(self, row_contents, qual_col_names=None):
        if not qual_col_names:
            qual_col_names = self.column_names
        assert len(qual_col_names) == len(row_contents)
        row = dict(zip(qual_col_names, row_contents))
        for null_default_col in set(self.column_names) - set(qual_col_names):
            row[null_default_col] = None
        self.rows.append(row)

    def update(self, update_clauses, where_clause):
        for row in self.rows:
            if self._row_match_where(row, where_clause):
                for update_clause in update_clauses:
                    row[update_clause.col_name] = update_clause.constant

    def delete(self, where_clause):
        self.rows = [row for row in self.rows
                     if not self._row_match_where(row, where_clause)]

    def _row_match_where(self, row, where_clause):
        if not where_clause:
            return True
        new_rows = []
        value = row[where_clause.col_name]

        op = where_clause.operator
        cons = where_clause.constant
        if ((op == "IS NOT" and (value is not cons)) or
                (op == "IS" and value is cons)):
            return True

        if value is None:
            return False

        if ((op == ">" and value > cons) or
                (op == "<" and value < cons) or
                (op == "=" and value == cons) or
                (op == "!=" and value != cons)):
            return True
        return False

    def select_rows(self, output_columns, order_by_columns,
                    where_clause=None, is_distinct=False):
        def expand_star_column(output_columns):
            new_output_columns = []
            for col in output_columns:
                if col.col_name == "*":
                    new_output_columns.extend(self.column_names)
                else:
                    new_output_columns.append(col)
            return new_output_columns

        def check_columns_exist(columns):
            assert all(col in self.column_names
                       for col in columns)

        def ensure_fully_qualified(columns):
            for col in columns:
                if col.table_name is None:
                    col.table_name = self.name

        def sort_rows(rows, order_by_columns):
            return sorted(rows, key=itemgetter(*order_by_columns))

        def generate_tuples(rows, output_columns):
            for row in rows:
                yield tuple(row[col] for col in output_columns)

        def remove_duplicates(tuples):
            seen = set()
            uniques = []
            for row in tuples:
                if row in seen:
                    continue
                seen.add(row)
                uniques.append(row)
            return uniques

        expanded_output_columns = expand_star_column(output_columns)

        check_columns_exist(expanded_output_columns)
        ensure_fully_qualified(expanded_output_columns)
        check_columns_exist(order_by_columns)
        ensure_fully_qualified(order_by_columns)

        filtered_rows = [row for row in self.rows
                         if self._row_match_where(row, where_clause)]
        sorted_rows = sort_rows(filtered_rows, order_by_columns)

        list_of_tuples = generate_tuples(sorted_rows, expanded_output_columns)
        if is_distinct:
            return remove_duplicates(list_of_tuples)
        return list_of_tuples


def pop_and_check(tokens, same_as):
    item = tokens.pop(0)
    assert item == same_as, "{} != {}".format(item, same_as)


def collect_characters(query, allowed_characters):
    letters = []
    for letter in query:
        if letter not in allowed_characters:
            break
        letters.append(letter)
    return "".join(letters)


def remove_leading_whitespace(query, tokens):
    whitespace = collect_characters(query, string.whitespace)
    return query[len(whitespace):]


def remove_word(query, tokens):
    word = collect_characters(query,
                              string.ascii_letters + "_" + string.digits)
    if word == "NULL":
        tokens.append(None)
    else:
        tokens.append(word)
    return query[len(word):]


def remove_text(query, tokens):
    if (query[0] == "'"):
        delimiter = "'"
    else:
        delimiter = '"'
    query = query[1:]
    end_quote_index = query.find(delimiter)
    while query[end_quote_index + 1] == delimiter:
        # Remove Escaped Quote
        query = query[:end_quote_index] + query[end_quote_index + 1:]
        end_quote_index = query.find(delimiter, end_quote_index + 1)
    text = query[:end_quote_index]
    tokens.append(text)
    query = query[end_quote_index + 1:]
    return query


def remove_integer(query, tokens):
    int_str = collect_characters(query, string.digits)
    tokens.append(int_str)
    return query[len(int_str):]


def remove_number(query, tokens):
    query = remove_integer(query, tokens)
    if query[0] == ".":
        whole_str = tokens.pop()
        query = query[1:]
        query = remove_integer(query, tokens)
        frac_str = tokens.pop()
        float_str = whole_str + "." + frac_str
        tokens.append(float(float_str))
    else:
        int_str = tokens.pop()
        tokens.append(int(int_str))
    return query


def tokenize(query):
    tokens = []
    while query:
        old_query = query

        if query[0] in string.whitespace:
            query = remove_leading_whitespace(query, tokens)
            continue

        if query[0] in (string.ascii_letters + "_"):
            query = remove_word(query, tokens)
            continue

        if query[:2] == "!=":
            tokens.append(query[:2])
            query = query[2:]
            continue

        if query[0] in "(),;*.><=":
            tokens.append(query[0])
            query = query[1:]
            continue

        if query[0] in {"'", '"'}:
            query = remove_text(query, tokens)
            continue

        if query[0] in string.digits:
            query = remove_number(query, tokens)
            continue

        if len(query) == len(old_query):
            raise AssertionError(
                "Query didn't get shorter. query = {}".format(query))

    return tokens

