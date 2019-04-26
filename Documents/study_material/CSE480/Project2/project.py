"""
Name: Kevin Jeong
Time To Completion: 8 hours
Comments: The project was fun. Going to spend
some time refactoring and learning more efficient
ways to organize my code.

Sources: CSE480 videos
"""
import string

_ALL_DATABASES = {}


class Tokenizer:
    @staticmethod
    def tokenize(query):
        def collect_characters(sub_query, allowed_char):
            letters = []
            for letter in sub_query:
                if letter not in allowed_char:
                    break
                letters.append(letter)
            return "".join(letters)

        def remove_leading_whitespace(sub_query):
            whitespace = collect_characters(sub_query, string.whitespace)
            return sub_query[len(whitespace):]

        def remove_word(sub_query, cache):
            word = collect_characters(sub_query,
                                      string.ascii_letters + "_" + string.digits)
            if word == "NULL":
                cache.append(None)
            else:
                cache.append(word)
            return sub_query[len(word):]

        def remove_text(sub_query, cache):
            assert sub_query[0] == "'"
            sub_query = sub_query[1:]
            end_quote_index = sub_query.find("'")
            text = sub_query[:end_quote_index]
            cache.append(text)
            sub_query = sub_query[end_quote_index + 1:]
            return sub_query

        def remove_number(sub_query, cache):
            sub_query = remove_int(sub_query, cache)
            if len(sub_query) > 0:
                if sub_query[0] == '.':
                    whole_str = cache.pop()
                    sub_query = sub_query[1:]
                    sub_query = remove_int(sub_query, cache)
                    fraction_str = cache.pop()
                    float_str = whole_str + "." + fraction_str
                    cache.append(float(float_str))
                else:
                    int_str = cache.pop()
                    cache.append(int(int_str))
            return sub_query

        def remove_int(sub_query, cache):
            int_str = collect_characters(sub_query, string.digits)
            cache.append(int_str)
            return sub_query[len(int_str):]
        old_query = query
        tokens = []
        while query:
            if query[0] in string.whitespace:
                query = remove_leading_whitespace(query)
                continue
            if query[0] in (string.ascii_letters + "_"):
                query = remove_word(query, tokens)
                continue
            if query[0] in "*(),;":
                tokens.append(query[0])
                query = query[1:]
                continue
            if query[0] == "'":
                query = remove_text(query, tokens)
                continue
            if query[0] in string.digits:
                query = remove_number(query, tokens)
                continue
            if len(old_query) == len(query):
                raise AssertionError("Query didn't get shorter")
        return tokens


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
        self.sql_keywords = {"CREATE", "TABLE", "INSERT", "INTO", "VALUES", "SELECT", "FROM", "ORDER", "BY"}

    def execute(self, statement):
        """
        Takes a SQL statement.
        Returns a list of tuples (empty unless select statement
        with rows to return).
        """
        tokens = Tokenizer.tokenize(statement)
        print(tokens)
        # Assuming we always have valid SQL queries
        if tokens[0] == "CREATE":
            self.database.create_table(tokens)
        elif tokens[0] == "INSERT":
            self.database.insert(tokens)
        else:
            return self.database.select(tokens)

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


class Database(object):
    def __init__(self, db_filename):
        self.db_filename = db_filename
        self.tables = {}

    def create_table(self, tokens):
        assert tokens[2] not in self.tables
        self.tables[tokens[2]] = Table(tokens[2])
        self.tables[tokens[2]].add_columns(tokens[4:])
        return []

    def insert(self, tokens):
        assert tokens[2] in self.tables
        self.tables[tokens[2]].insert(tokens[5:])
        return []

    def select(self, tokens):
        def order_helper(reorder_rows, order, priority_list, asterisk_flag=False):
            prev = 0
            for ordering, col_name in priority_list:
                if asterisk_flag:
                    if col_name[2] == order[0]:
                        order_column = ordering
                    if len(order) > 1 and col_name[2] == order[1]:
                            second_order = ordering
                else:
                    if col_name == order[0]:
                        order_column = ordering
                    if len(order) > 1 and col_name == order[1]:
                        second_order = ordering
            for row in range(1, len(reorder_rows)):
                if reorder_rows[prev][order_column] > reorder_rows[row][order_column]:
                    reorder_rows[row], reorder_rows[prev] = reorder_rows[prev], reorder_rows[row]
                    order_helper(reorder_rows, order, priority_list, asterisk_flag)
                    prev = row
                elif len(order) > 1 and reorder_rows[prev][order_column] == reorder_rows[row][order_column]:
                    if reorder_rows[prev][second_order] > reorder_rows[row][second_order]:
                        reorder_rows[row], reorder_rows[prev] = reorder_rows[prev], reorder_rows[row]
                        order_helper(reorder_rows, order, priority_list, asterisk_flag)
                        prev = row
                    else:
                        prev = row
                else:
                    prev = row
            return reorder_rows

        def query_finish(query):
            order = []
            for subquery in query[1:]:
                if subquery == "ORDER":
                    order = order_parser(query[(query.index(subquery) + 2):])
            return query[0], order

        def order_parser(query):
            results = []
            for subquery in query:
                if subquery == ';':
                    return results
                elif subquery == ',':
                    continue
                results.append(subquery)
            return results

        def all_select(query):
            table_name = query[0]
            info = query_finish(query)
            results = []
            for priority_order, key in enumerate(self.tables[table_name].data.keys()):
                results.append((priority_order, key))
            return results, info

        columns = []
        priority = 0
        all_flag = False
        for token in tokens[1:]:
            if token == ';':
                break
            elif token == '*':
                columns, query_info = all_select(tokens[3:])
                all_flag = True
                break
            elif token == ',':
                continue
            elif token == "FROM":
                query_info = query_finish(tokens[(tokens.index(token) + 1):])
                break
            else:
                columns.append((priority, token))
                priority += 1
        query_result = []
        for column in columns:
            if all_flag:
                query_result.append(tuple(self.tables[query_info[0]].data_search(column[1][2])))
                continue
            query_result.append(tuple(self.tables[query_info[0]].data_search(column[1])))
        row_result = list(zip(*query_result))
        if query_info[1]:
            row_result = order_helper(row_result, query_info[1], columns, all_flag)
        return tuple(row_result)


class Table(object):
    def __init__(self, table_id):
        self.table_id = table_id
        self.data = dict()
        self.sql_data_types = {"NULL", "INTEGER", "REAL", "TEXT"}

    def unique_id_check(self, col_name):
        for key in self.data.keys():
            if col_name == key[2]:
                return key[0]
        return False

    def data_search(self, search):
        for key in self.data.keys():
            if search == key[0] or search == key[2]:
                return self.data[key]
        return False

    def add_columns(self, tokens):
        unique_id = 0
        for token in tokens:
            if token == ';':
                return
            elif token in ',)':
                continue
            else:
                if token not in self.sql_data_types:
                    column_type = token
                else:
                    self.data[(unique_id, token, column_type)] = []
                    unique_id += 1
        return []

    def insert(self, tokens):
        total_columns = len(self.data)
        round_robin_count = 0
        for token in tokens:
            if token == ';':
                return
            elif token == ',' or token == ')':
                continue
            search = self.data_search(round_robin_count % total_columns)
            if isinstance(search, list):
                search.append(token)
            round_robin_count += 1
        return []



