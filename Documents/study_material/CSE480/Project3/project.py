"""
Name: Kevin Jeong
Time To Completion: 12~ hours
Comments: The project was fair and fun to work on.

Sources: Professor Nahum's project 2 solution;
"""
import copy
import string
from operator import itemgetter

_ALL_DATABASES = {}


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
            table_name = tokens.pop(0)
            pop_and_check(tokens, "(")
            column_name_type_pairs = []
            while True:
                column_name = tokens.pop(0)
                column_type = tokens.pop(0)
                assert column_type in {"TEXT", "INTEGER", "REAL"}
                column_name_type_pairs.append((column_name, column_type))
                comma_or_close = tokens.pop(0)
                if comma_or_close == ")":
                    break
                assert comma_or_close == ','
            self.database.create_new_table(table_name, column_name_type_pairs)

        def insert(tokens):
            """
            Determines the table name and row values to add.
            """
            pop_and_check(tokens, "INSERT")
            pop_and_check(tokens, "INTO")
            table_name = tokens.pop(0)
            ins_specify = tokens.pop(0)
            row_contents = []
            row_elem = []
            col_input = []
            if ins_specify == "(":
                item = tokens.pop(0)
                while item != ")":
                    col_input.append(item)
                    item = tokens.pop(0)
                    if item == ",":
                        item = tokens.pop(0)
                pop_and_check(tokens, "VALUES")
            pop_and_check(tokens, "(")
            item = tokens.pop(0)
            while item != ")" or tokens:
                if item == ")":
                    pop_and_check(tokens, ",")
                    pop_and_check(tokens, "(")
                    item = tokens.pop(0)
                row_elem.append(item)
                item = tokens.pop(0)
                if item == ",":
                    item = tokens.pop(0)
                elif item == ")":
                    row_contents.append(row_elem)
                    row_elem = []
            self.database.insert_into(table_name, row_contents, col=col_input)

        def delete(tokens):
            """
            handles queries with delete required
            and removes necessary rows from
            the specified table in database
            """
            pop_and_check(tokens, "DELETE")
            pop_and_check(tokens, "FROM")
            table_name = tokens.pop(0)
            conditional = False
            if tokens and tokens[0] == "WHERE":
                conditional = self.where(tokens)
            self.database.delete(table_name, conditional)

        def update(tokens):
            """
            Handles queries with update required
            and modifies rows from
            the specified table in database
            """
            pop_and_check(tokens, "UPDATE")
            table_name = tokens.pop(0)
            pop_and_check(tokens, "SET")
            update_columns = []
            conditional = False
            while tokens and tokens[0] != "WHERE":
                column_name = tokens.pop(0)
                operand = tokens.pop(0)
                update_value = tokens.pop(0)
                update_columns.append([column_name, operand, update_value])
                if tokens and tokens[0] == ",":
                    tokens.pop(0)
            if tokens:
                conditional = self.where(tokens)
            self.database.update(table_name, update_columns, conditional)

        def select(tokens):
            """
            Determines the table name, output_columns, and order_by_columns.
            If there is a join involved, creates new table required and
            finishes selection query.
            """
            pop_and_check(tokens, "SELECT")
            output_columns = []
            conditional = []
            distinct_flag = False
            join_conditional = False
            if tokens[0] == "DISTINCT":
                tokens.pop(0)
                distinct_flag = tokens[0]
            while True:
                col = tokens.pop(0)
                if tokens[0] == '*':
                    col = tokens.pop(0)
                output_columns.append(col)
                comma_or_from = tokens.pop(0)
                if comma_or_from == "FROM":
                    break
                assert comma_or_from == ','
            table_name = tokens.pop(0)
            if tokens[0] == "WHERE":
                pop_and_check(tokens, "WHERE")
                cond_columns = []
                col_name = tokens.pop(0)
                operand = tokens.pop(0)
                item = tokens.pop(0)
                while item != "ORDER":
                    cond_columns.append(item)
                    item = tokens.pop(0)
                    if item == ",":
                        item = tokens.pop(0)
                conditional = [col_name, operand, cond_columns]
            elif tokens[0] == "LEFT":
                pop_and_check(tokens, "LEFT")
                pop_and_check(tokens, "OUTER")
                pop_and_check(tokens, "JOIN")
                join_table_name = tokens.pop(0)
                pop_and_check(tokens, "ON")
                join_col1 = tokens.pop(0)
                pop_and_check(tokens, "=")
                join_col2 = tokens.pop(0)
                if tokens and tokens[0] == "WHERE":
                    conditional = self.where(tokens)
                pop_and_check(tokens, "ORDER")
                join_conditional = [join_table_name, join_col1, join_col2]
            else:
                pop_and_check(tokens, "ORDER")
            pop_and_check(tokens, "BY")
            order_by_columns = []
            while True:
                col = tokens.pop(0)
                order_by_columns.append(col)
                if not tokens:
                    break
                pop_and_check(tokens, ",")
            return self.database.select(
                output_columns, table_name, order_by_columns, conditional, distinct_flag, join_conditional)

        tokens = tokenize(statement)
        assert tokens[0] in {"CREATE", "INSERT", "SELECT", "DELETE", "UPDATE"}
        last_semicolon = tokens.pop()
        assert last_semicolon == ";"
        if tokens[0] == "CREATE":
            create_table(tokens)
            return []
        elif tokens[0] == "INSERT":
            insert(tokens)
            return []
        elif tokens[0] == "DELETE":
            delete(tokens)
            return []
        elif tokens[0] == "UPDATE":
            update(tokens)
            return []
        else:  # tokens[0] == "SELECT"
            return select(tokens)
        assert not tokens

    def where(self, tokens):
        """
        Pulls information required that
        specifies which row they want to target
        """
        pop_and_check(tokens, "WHERE")
        cond_columns = []
        col_name = tokens.pop(0)
        if col_name.find("."):
            period_index = col_name.find(".")
            col_name = col_name[(period_index + 1):]
        operand = tokens.pop(0)
        cond_columns.append(tokens.pop(0))
        return [col_name, operand, cond_columns]

    def close(self):
        """
        Empty method that will be used in future projects
        """
        pass


def connect(filename):
    """
    Creates a Connection object with the given filename
    """
    return Connection(filename)


class Database:
    def __init__(self, filename):
        """
        Takes a filename, but doesn't do anything with it.
        (The filename will be used in a future project).
        """
        self.filename = filename
        self.tables = {}

    def create_new_table(self, table_name, column_name_type_pairs):
        """
        Creates new table in database with proper column types.
        """
        assert table_name not in self.tables
        self.tables[table_name] = Table(table_name, column_name_type_pairs)
        return []

    def insert_into(self, table_name, row_contents, col=False):
        """
        Inserts new row content into table specified if
        it exists in the database.
        """
        assert table_name in self.tables
        table = self.tables[table_name]
        table.insert_new_row(row_contents, col)
        return []

    def delete(self, table_name, conditional):
        """
        Deletes either entire table or specific
        rows from specified table
        """
        assert table_name in self.tables
        table = self.tables[table_name]
        return table.delete(conditional)

    def update(self, table_name, update_lst, conditional):
        """
        Modifies rows in target depending on
        conditionals specified
        """
        assert table_name in self.tables
        table = self.tables[table_name]
        return table.update(update_lst, conditional)

    def select(self, output_columns, table_name, order_by_columns, conditional=False, distinct_flag=False, join_cond=False):
        """
        Returns row/rows of table with specified information
        from query. If a join is required, creates a
        new table with desired contents and selects from it.
        """
        def join_tables(conditions, order_by_columns):
            """
            Creates new table using left outer join
            while adhering to any conditionals specified.
            """
            join_table_one = self.tables[table_name]
            join_table_two = self.tables[conditions[0]]
            column_names = tuple(list(join_table_one.column_names) + list(join_table_two.column_names))
            join_table_one.column_names = column_names
            period_index_one = conditions[1].find(".")
            period_index_two = conditions[2].find(".")
            join_column_one = conditions[1][(period_index_one+1):]
            join_column_two = conditions[2][(period_index_two+1):]
            period_index = order_by_columns[0].find(".")
            order_col = order_by_columns[0][(period_index+1):]
            table_two_elem = []
            for row in join_table_two.rows:
                if row[join_column_two] == None:
                    continue
                table_two_elem.append(row[join_column_two])
            for row_two in range(len(join_table_two.rows)):
                for row_one in range(len(join_table_one.rows)):
                    if join_table_one.rows[row_one][join_column_one] == join_table_two.rows[row_two][join_column_two]:
                        for key, value in join_table_two.rows[row_two].items():
                            join_table_one.rows[row_one][key] = value
                    if join_table_one.rows[row_one][join_column_one] not in table_two_elem:
                        for key, value in join_table_two.rows[row_two].items():
                            if join_table_one.rows[row_one][join_column_one] is None:
                                join_table_one.rows[row_one][key] = None
                            if key in join_table_one.column_names:
                                continue
                            join_table_one.rows[row_one][key] = None
            return join_table_one

        assert table_name in self.tables
        if join_cond:
            table = join_tables(join_cond, order_by_columns)
        else:
            table = self.tables[table_name]
        return table.select_rows(output_columns, order_by_columns, conditional, distinct_flag)


class Table:
    def __init__(self, name, column_name_type_pairs):
        """
        Takes in a name, as well as
        column name and types required to make
        required table.
        """
        self.name = name
        self.column_names, self.column_types = zip(*column_name_type_pairs)
        self.rows = []

    def insert_new_row(self, row_contents, col=False):
        """
        Inserts new row contents into table,
        while accounting for any conditionals specified.
        """
        for row_to_insert in row_contents:
            if col:
                new_row_content = [None] * len(self.column_types)
                for i in range(len(self.column_names)):
                    col_name = self.column_names[i]
                    if col_name in col:
                        index = col.index(col_name)
                        new_row_content[i] = row_to_insert[index]
                row_to_insert = new_row_content
            assert len(self.column_names) == len(row_to_insert)
            row = dict(zip(self.column_names, row_to_insert))
            self.rows.append(row)

    def delete(self, conditional):
        """
        Deletes table content (table object left
        alone), or certain rows depending on
        conditionals specified.
        """
        if conditional:
            rows_to_delete = self.row_cleanse(conditional, self.rows, self.column_names)
            for del_row in rows_to_delete:
                if del_row in self.rows:
                    self.rows.remove(del_row)
        else:
            self.rows = []
        return []

    def update(self, update_lst, conditional):
        """
        Updates row/rows of table that
        match with specified conditionals.
        """
        if conditional:
            rows_to_update = self.row_cleanse(conditional, self.rows, self.column_names)
        else:
            rows_to_update = self.rows
        for update in update_lst:
            column, operand, value = update[0], update[1], update[2]
            for row in rows_to_update:
                row[column] = value

    def row_cleanse(self, conditional, rows, output_columns):
        """
        Goes through each row in the table and uses helper
        function to determine whether or not the row should
        appear in final result.
        """
        def row_conditional(row, conditional, null_flag):
            """
            Helper function that looks at one row
            and determines if it meets conditionals specified.
            If it does meet requirements returns True,
            else returns False.
            """
            if null_flag:
                if null_flag == 1:  # where column is None
                    if row[conditional[0]] is None:
                        return True
                else:  # where column is not None
                    if row[conditional[0]] is not None:
                        return True
            else:  # operand can be applied as is against column
                column, operand, cond = conditional
                if '.' in column:
                    period_index = column.find(".")
                    column = column[(period_index+1):]
                if row[column] is None:
                    return False
                elif operand == ">":
                    if row[column] > cond[0]:
                        return True
                elif operand == "<":
                    if row[column] < cond[0]:
                        return True
                elif operand == "=":
                    if row[column] == cond[0]:
                        return True
                elif operand == "!=":
                    if row[column] != cond[0]:
                        return True
            return False

        null_flag = False
        cleansed_rows = []
        if conditional[1] == "IS":
            if conditional[2][0] is None:
                null_flag = 1
            else:
                null_flag = 2
        for row in rows:
            if row_conditional(row, conditional, null_flag):
                cleansed_rows.append(row)
        return cleansed_rows

    def select_rows(self, output_columns, order_by_columns, conditional=False, distinct_flag=False):
        """
        Selects rows specified after making sure it passes
        through necessary tests using helper functions.
        """
        def expand_star_column(output_columns):
            """
            If star is used in selection query,
            adds all available columns to a list
            that specifies outputs.
            """
            new_output_columns = []
            for col in output_columns:
                if col == "*":
                    new_output_columns.extend(self.column_names)
                else:
                    new_output_columns.append(col)
            return new_output_columns

        def check_columns_exist(columns):
            """
            Makes sure that all output columns
            exist in the table to begin with.
            """
            for i in range(len(columns)):
                if '.' in columns[i]:
                    period_index = columns[i].find('.')
                    columns[i] = columns[i][(period_index+1):]
            assert all(col in self.column_names for col in columns)

        def sort_rows(order_by_columns):
            """
            Sorts selection result in order of list from parameter.
            Prioritizes the columns that first appear in the list.
            If there are more than one columns specified in list,
            uses latter columns to further sort query where former
            column values are equal. If column values are equal and
            no other columns mentioned in list, sorts in order it
            was received.
            """
            temp_lst = copy.deepcopy(self.rows)
            for i in range(len(self.rows)):
                if self.rows[i][order_by_columns[0]] == None:
                    temp_lst.remove(self.rows[i])
            self.rows = temp_lst
            return sorted(self.rows, key=itemgetter(*order_by_columns))

        def generate_tuples(rows, output_columns):
            """
            Returns a generator containing tuples of table content.
            """
            for row in rows:
                yield tuple(row[col] for col in output_columns)

        def distinct_output(rows, distinction):
            """
            Returns rows where specified column values are distinct.
            """
            unique_rows = set()
            result = []
            for row in rows:
                if row[distinction] not in unique_rows:
                    unique_rows.add(row[distinction])
                    result.append(row)
            return result

        expanded_output_columns = expand_star_column(output_columns)
        check_columns_exist(expanded_output_columns)
        check_columns_exist(order_by_columns)
        sorted_rows = sort_rows(order_by_columns)
        if conditional:
            sorted_rows = self.row_cleanse(conditional, sorted_rows, expanded_output_columns)
        if distinct_flag:
            sorted_rows = distinct_output(sorted_rows, distinct_flag)
        for i in range(len(sorted_rows)):
            for column in self.column_names:
                if column not in sorted_rows[i]:
                    sorted_rows[i][column] = None
        return generate_tuples(sorted_rows, expanded_output_columns)


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
                              string.ascii_letters + "_" + string.digits + ".")
    if word == "NULL":
        tokens.append(None)
    else:
        tokens.append(word)
    return query[len(word):]


def remove_text(query, tokens):
    assert query[0] == "'"
    query = query[1:]
    text = ""
    if query.find("''") != -1:
        while query.find("''") != -1:
            quote_index = query.find("''")
            text += query[:(quote_index+1)]
            query = query[(quote_index+2):]
    end_quote_index = query.find("'")
    text += query[:end_quote_index]
    query = query[(end_quote_index+1):]
    tokens.append(text)
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
        # print("Query:{}".format(query))
        # print("Tokens: ", tokens)
        old_query = query

        if query[0] in string.whitespace:
            query = remove_leading_whitespace(query, tokens)
            continue

        if query[0] in (string.ascii_letters + "_"):
            query = remove_word(query, tokens)
            continue

        if query[0] in "(),;*><=!":
            if query[0] == "!":
                tokens.append(query[:2])
                query = query[3:]
                continue
            tokens.append(query[0])
            query = query[1:]
            continue

        if query[0] == "'":
            query = remove_text(query, tokens)
            continue

        if query[0] in string.digits:
            query = remove_number(query, tokens)
            continue

        if len(query) == len(old_query):
            raise AssertionError("Query didn't get shorter.")
    return tokens
