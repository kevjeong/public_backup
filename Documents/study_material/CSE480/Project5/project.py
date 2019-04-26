"""
Name: Kevin Jeong
Time To Completion: 6 hours
Comments: Was fun

Sources: Dr. Nahum's project 3 solution; project 2 (own code);
"""
import copy
import functools
import itertools
import string
from operator import itemgetter
from collections import namedtuple

_ALL_DATABASES = {}

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

    def create_collation(self, collation_name, collation_funct):
        self.database.create_collation(collation_name, collation_funct)

    def executemany(self, statement, multiple_values):
        tokens = tokenize(statement)
        last_semicolon = tokens.pop()
        assert last_semicolon == ";"
        parameterized_list = []
        for token in range(len(tokens)):
            if tokens[token] == "?":
                parameterized_list.append(token)
        assert len(multiple_values[0]) == len(parameterized_list)
        parameterized_list *= len(multiple_values)
        for entry_index in range(len(multiple_values)):
            entry_query = copy.deepcopy(tokens)
            for value in multiple_values[entry_index]:
                entry_query[parameterized_list.pop(0)] = value
            self.execute(" ".join([str(entry) for entry in entry_query]) + ";")
        return []

    def execute(self, statement, view_exe=False):
        """
        Takes a SQL statement.
        Returns a list of tuples (empty unless select statement
        with rows to return).
        """

        def create_view(tokens):
            pop_and_check(tokens, "VIEW")
            view_name = tokens.pop(0)
            pop_and_check(tokens, "AS")
            token_copy = copy.deepcopy(tokens)
            view_query_table_name = tokens[tokens.index("FROM") + 1]
            view_query = " ".join([str(token) for token in tokens]) + ";"
            self.database.views[view_name] = [None] * 4
            view_query_result = list(self.execute(view_query, view_exe=view_name))
            if self.database.views[view_name][1] == None:
                copy_table = copy.deepcopy(self.database.tables[view_query_table_name])
            else:
                copy_table = copy.deepcopy(self.database.views[view_name][1])
                self.database.views[view_name] = [token_copy, copy_table, view_query_result, view_query_table_name]
                return self.database.views[view_name]
            view_table = result_to_table(view_query_result, copy_table)
            self.database.views[view_name] = [token_copy, view_table, view_query_result, view_query_table_name]
            return self.database.views[view_name]

        def refresh_view2(view_name):
            view_tokens = self.database.views[view_name][0]
            view_query = " ".join([str(token) for token in view_tokens]) + ";"
            view_query_table_name = self.database.views[view_name][3]
            self.database.views[view_name] = [None] * 4
            view_query_result = list(self.execute(view_query, view_exe=view_name))
            if self.database.views[view_name][1] == None:
                copy_table = copy.deepcopy(self.database.tables[view_query_table_name])
            else:
                copy_table = copy.deepcopy(self.database.views[view_name][1])
                self.database.views[view_name] = [view_tokens, copy_table, view_query_result, view_query_table_name]
                return self.database.views[view_name]
            view_table = result_to_table(view_query_result, copy_table)
            self.database.views[view_name] = [view_tokens, view_table, view_query_result, view_query_table_name]
            return self.database.views[view_name]

        def refresh_view(view_name):
            view_tokens = self.database.views[view_name][0]
            if len(view_tokens) == 0:
                self.database.views[view_name][1] = copy.deepcopy(self.database.tables[self.database.views[view_name][3]])
                return result_to_table([], self.database.views[view_name][1])
            result = list(select(view_tokens))
            final_table = result_to_table(result, self.database.tables[self.database.views[view_name][3]],
                                          self.database.views[view_name][1])
            self.database.views[view_name][1] = final_table
            return final_table

        def result_to_table(result, table, join_table=False):
            if len(result) == 0:
                table.rows = []
                return table
            else:
                if table.rows and len(table.rows[0]) != len(result[0]) and join_table is not None:
                    return join_table
            to_keep_list = []
            final_table = copy.deepcopy(table)
            for row_val_index in range(len(table.rows)):
                row_value = tuple(table.rows[row_val_index].values())
                for elem in result:
                    elem_comp = tuple([elem[0], elem[1]])
                    if elem_comp == row_value:
                        to_keep_list.append(table.rows[row_val_index])
            final_table.rows = to_keep_list
            return final_table

        def create_table(tokens):
            """
            Determines the name and column information from tokens add
            has the database create a new table within itself.
            """
            pop_and_check(tokens, "CREATE")
            if tokens[0] == "VIEW":
                return create_view(tokens)
            pop_and_check(tokens, "TABLE")
            table_name = tokens.pop(0)
            pop_and_check(tokens, "(")
            column_name_type_pairs = []
            col_default = {}
            while True:
                column_name = tokens.pop(0)
                qual_col_name = QualifiedColumnName(column_name, table_name)
                column_type = tokens.pop(0)
                assert column_type in {"TEXT", "INTEGER", "REAL"}
                if len(tokens) > 0 and tokens[0] == "DEFAULT":
                    pop_and_check(tokens, "DEFAULT")
                    col_default[column_name] = tokens.pop(0)
                else:
                    col_default[column_name] = None
                column_name_type_pairs.append((qual_col_name, column_type))
                comma_or_close = tokens.pop(0)
                if comma_or_close == ")":
                    break
                assert comma_or_close == ','
            self.database.create_new_table(table_name, column_name_type_pairs, col_default)

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

            pop_and_check(tokens, "INSERT")
            pop_and_check(tokens, "INTO")
            table_name = tokens.pop(0)
            if tokens[0] == "(":
                col_names = get_comma_seperated_contents(tokens)
                qual_col_names = [QualifiedColumnName(col_name, table_name)
                                  for col_name in col_names]
            elif len(tokens) > 0 and tokens[0] == "DEFAULT":
                pop_and_check(tokens, "DEFAULT")
                pop_and_check(tokens, "VALUES")
                qual_col_names = list(self.database.tables[table_name].column_names)
                row_contents = [col_value for col_value in self.database.tables[table_name].default.values()]
                self.database.insert_into(table_name,
                                          row_contents,
                                          qual_col_names=qual_col_names)
            else:
                qual_col_names = None
            if len(tokens) > 0:
                pop_and_check(tokens, "VALUES")
            while tokens:
                row_contents = get_comma_seperated_contents(tokens)
                if qual_col_names:
                    assert len(row_contents) == len(qual_col_names)
                self.database.insert_into(table_name,
                                          row_contents,
                                          qual_col_names=qual_col_names)
                if tokens:
                    pop_and_check(tokens, ",")

            for key, value in self.database.views.items():
                for col_name in self.database.views[key][1].column_names:
                    if col_name.table_name == table_name:
                        refresh_view2(key)

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

        def select(copy_tokens, view_exe=False):
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

            copy_tokens = copy.deepcopy(copy_tokens)
            desc_list = []
            pop_and_check(copy_tokens, "SELECT")

            if copy_tokens[0] == "max" or copy_tokens[0] == "min":
                aggregate_func = copy_tokens[0]
            else:
                aggregate_func = False

            agg_col, output_columns = [], []
            if aggregate_func:
                is_distinct = False
                item = copy_tokens.pop(0)
                while item != "FROM":
                    if item == ")" and copy_tokens[0] == "FROM":
                        break
                    elif item == "max" or item == "min":
                        agg_col.append(item)
                        item = copy_tokens.pop(0)
                    elif item == "(":
                        qual_col_name = get_qualified_column_name(copy_tokens)
                        output_columns.append(qual_col_name)
                        item = copy_tokens.pop(0)
                    else:
                        item = copy_tokens.pop(0)

                pop_and_check(copy_tokens, "FROM")
            else:
                is_distinct = copy_tokens[0] == "DISTINCT"
                if is_distinct:
                    copy_tokens.pop(0)

                while True:
                    qual_col_name = get_qualified_column_name(copy_tokens)
                    output_columns.append(qual_col_name)
                    comma_or_from = copy_tokens.pop(0)
                    if comma_or_from == "FROM":
                        break
                    assert comma_or_from == ','

            # FROM or JOIN
            from_join_clause = get_from_join_clause(copy_tokens)
            possible_view = from_join_clause.left_table_name
            if possible_view in self.database.views:
                possible_view = self.database.views[possible_view][3]
            else:
                possible_view = from_join_clause.left_table_name

            table_name = from_join_clause.left_table_name

            # WHERE
            where_clause = get_where_clause(copy_tokens, possible_view)

            # ORDER BY
            pop_and_check(copy_tokens, "ORDER")
            pop_and_check(copy_tokens, "BY")
            order_by_columns = []
            collate = False
            while True:
                qual_col_name = get_qualified_column_name(copy_tokens)
                order_by_columns.append(qual_col_name)
                if copy_tokens and copy_tokens[0] == "DESC":
                    desc_list.append(qual_col_name)
                    pop_and_check(copy_tokens, "DESC")
                elif copy_tokens and copy_tokens[0] == "COLLATE":
                    pop_and_check(copy_tokens, "COLLATE")
                    collate_name = copy_tokens.pop(0)
                    collate = (self.database.collates[collate_name], collate_name, qual_col_name)
                    if copy_tokens and copy_tokens[0] == "DESC":
                        desc_list.append(qual_col_name)
                        pop_and_check(copy_tokens, "DESC")
                if not copy_tokens:
                    break
                pop_and_check(copy_tokens, ",")
            if table_name in self.database.views:
                fresh_view = refresh_view(table_name)
                view = [fresh_view, table_name]
            else:
                view = False
            return self.database.select(
                output_columns,
                order_by_columns,
                from_join_clause=from_join_clause,
                where_clause=where_clause,
                is_distinct=is_distinct, desc=desc_list,
                view=view, collate=collate, agg=agg_col, view_exe=view_exe)

        tokens = tokenize(statement)
        last_semicolon = tokens.pop()
        assert last_semicolon == ";"

        if tokens[0] == "CREATE":
            create_table(tokens)
            return []
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
            return select(tokens, view_exe=view_exe)
        else:
            raise AssertionError(
                "Unexpected first word in statements: " + tokens[0])

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
        self.views = {}
        self.collates = {}

    def create_collation(self, name, funct):
        self.collates[name] = funct

    def create_new_table(self, table_name, column_name_type_pairs, default):
        assert table_name not in self.tables
        self.tables[table_name] = Table(table_name, column_name_type_pairs, default)
        return []

    def insert_into(self, table_name, row_contents, qual_col_names=None):
        assert table_name in self.tables
        table = self.tables[table_name]
        table.insert_new_row(row_contents, qual_col_names=qual_col_names)
        for row in range(len(self.tables[table_name].rows)):
            for key, value in self.tables[table_name].rows[row].items():
                if value is None and key.col_name in self.tables[table_name].default:
                    self.tables[table_name].rows[row][key] = self.tables[table_name].default[key.col_name]
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
               from_join_clause, where_clause=None,
               is_distinct=False, desc=False,
               view=False, collate=False, agg=False, view_exe=False):
        if view:
            selection_table = self.views
        else:
            selection_table = self.tables
        assert from_join_clause.left_table_name in selection_table
        if from_join_clause.right_table_name:
            assert from_join_clause.right_table_name in selection_table
            left_table = selection_table[from_join_clause.left_table_name]
            right_table = selection_table[from_join_clause.right_table_name]
            all_columns = itertools.chain(
                zip(left_table.column_names, left_table.column_types),
                zip(right_table.column_names, right_table.column_types))
            left_col = from_join_clause.left_join_col_name
            right_col = from_join_clause.right_join_col_name
            join_table = Table("", all_columns, {})
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
            if view_exe:
                self.views[view_exe][1] = copy.deepcopy(table)
        else:
            if view:
                table = selection_table[from_join_clause.left_table_name][1]
                view_exe = [output_columns, order_by_columns]
            else:
                table = selection_table[from_join_clause.left_table_name]
        return table.select_rows(output_columns, order_by_columns,
                                 where_clause=where_clause,
                                 is_distinct=is_distinct,
                                 desc=desc, view=view,
                                 collate=collate, agg=agg, view_exe=view_exe)


class Table:

    def __init__(self, name, column_name_type_pairs, default):
        self.name = name
        self.column_names, self.column_types = zip(*column_name_type_pairs)
        self.rows = []
        self.default = default

    def insert_new_row(self, row_contents, qual_col_names=None):
        if not qual_col_names:
            qual_col_names = self.column_names
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
                    where_clause=None, is_distinct=False,
                    desc=False, view= False,
                    collate=False, agg=False, view_exe=False):
        def expand_star_column(output_columns):
            new_output_columns = []
            for col in output_columns:
                if not view_exe and col.table_name == None:
                    col.table_name = self.name
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

        def collate_manual(funct, rows, collate, next_priority, col_names=False):
            original = copy.deepcopy(rows)
            for i in range(len(rows)):
                for j in range(0, len(rows)-i-1):
                    result = funct(rows[j][collate[2]], rows[j+1][collate[2]])
                    if result == 1:
                        rows[j], rows[j+1] = rows[j+1], rows[j]
                    elif result == 0:
                        if next_priority and rows[j][next_priority] > rows[j+1][next_priority]:
                            rows[j], rows[j+1] = rows[j+1], rows[j]
                        else:
                            if col_names and len(col_names) > 1:
                                next_priority = col_names[1]
                            if rows[j][next_priority] > rows[j+1][next_priority]:
                                rows[j], rows[j+1] = rows[j+1], rows[j]
            return rows

        def sort_rows(rows, desc, order_by_columns, collate, col_name=False):
            stabilizing_rows = rows
            for order_elem in order_by_columns[::-1]:
                reverse_flag = False
                if order_by_columns.index(order_elem) != (len(order_by_columns)-1):
                    next_priority = order_by_columns[order_by_columns.index(order_elem)+1]
                else:
                    next_priority = False
                if desc and order_elem in desc:
                    reverse_flag = True
                if collate and order_elem == collate[2]:
                    stabilizing_rows = collate_manual(collate[0], rows, collate, next_priority, col_name)
                    if reverse_flag:
                        stabilizing_rows = stabilizing_rows[::-1]
                else:
                    stabilizing_rows = sorted(stabilizing_rows, key=itemgetter(order_elem),
                                              reverse=reverse_flag)
            return stabilizing_rows

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

        def aggregate(func, rows, output_col):
            if func == "min":
                result = sorted(rows, key=itemgetter(output_col), reverse=True)
            else:
                result = sorted(rows, key=itemgetter(output_col))
            return result[-1][output_col]

        if view:
            for col_index in range(len(output_columns)):
                if not output_columns[col_index].table_name and len(self.column_names) != 0:
                    for name in self.column_names:
                        if name and name.col_name == output_columns[col_index].col_name:
                            output_columns[col_index].table_name = name.table_name
            for col_index in range(len(order_by_columns)):
                if not order_by_columns[col_index].table_name and len(self.column_names) != 0:
                    for name in self.column_names:
                        if name and name.col_name == order_by_columns[col_index].col_name:
                            order_by_columns[col_index].table_name = name.table_name

        expanded_output_columns = expand_star_column(output_columns)

        if view:
            check_columns_exist(list(view[0].column_names))
        else:
            check_columns_exist(expanded_output_columns)
        ensure_fully_qualified(expanded_output_columns)
        check_columns_exist(order_by_columns)
        ensure_fully_qualified(order_by_columns)

        filtered_rows = [row for row in self.rows
                         if self._row_match_where(row, where_clause)]
        sorted_rows = sort_rows(filtered_rows, desc, order_by_columns, collate, self.column_names)
        list_of_tuples = generate_tuples(sorted_rows, expanded_output_columns)
        if is_distinct:
            return remove_duplicates(list_of_tuples)
        if agg:
            rows_req_pickle = list(list_of_tuples)
            ans = []
            for agg_col in agg:
                rows_req = copy.deepcopy(rows_req_pickle)
                output_col_index = expanded_output_columns.index(output_columns.pop(0))
                ans.append(aggregate(agg_col, rows_req, output_col_index))
            return set([tuple(ans)])
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

        if query[0] in "(),;*.><=?":
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
