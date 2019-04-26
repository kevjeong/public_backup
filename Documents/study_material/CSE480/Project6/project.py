"""
Name: Kevin Jeong
Time To Completion: 1 hour
Comments: Was fun
"""
import copy
global _ALL_DATABASES
_ALL_DATABASES = {}


class Collection:
    """
    a list of dictionaries (documents) accessible in a db-like way.
    """

    def __init__(self, data=[]):
        """
        initialize an empty collection.
        """
        self.data = copy.deepcopy(data)

    def insert(self, document):
        """
        add a new document (a.k.a. python dict) to the collection.
        """
        self.data.append(document)

    def find_all(self):
        """
        return list of all docs in database.
        """
        result = []
        for value in self.data:
            result.append(value)
        return result

    def delete_all(self):
        """
        truncate the collection.
        """
        self.data = []

    def find_one(self, where_dict):
        """
        return the first matching doc.
        if none is found, return none.
        """
        for doc in self.data:
            for key in where_dict.keys():
                if key in doc and where_dict[key] == doc[key]:
                    return doc

    def find(self, where_dict):
        """
        return matching list of matching doc(s).
        """
        if where_dict == {}:
            return self.data
        result = []
        for doc in self.data:
            criteria_count = 0
            criteria_total = len(where_dict.keys())
            for key in where_dict.keys():
                if key in doc:
                    val_at_doc = doc[key]
                    val_at_where_dict = where_dict[key]
                    if type(val_at_where_dict) == dict:
                        for more_keys in val_at_where_dict.keys():
                            if more_keys in val_at_doc and val_at_doc[more_keys] == val_at_where_dict[more_keys]:
                                criteria_count += 1
                                if criteria_count == criteria_total:
                                    result.append(doc)
                    else:
                        if val_at_doc == val_at_where_dict:
                            criteria_count += 1
                            if criteria_count == criteria_total:
                                result.append(doc)
                else:
                    break
        return result

    def count(self, where_dict):
        """
        return the number of matching docs.
        """
        count = 0
        for doc in self.data:
            criteria_count = 0
            criteria_total = len(where_dict.keys())
            for key in where_dict.keys():
                if key in doc:
                    val_at_doc = doc[key]
                    val_at_where_dict = where_dict[key]
                    if isinstance(val_at_where_dict) == dict:
                        for more_keys in val_at_where_dict.keys():
                            if more_keys in val_at_doc and val_at_doc[more_keys] == val_at_where_dict[more_keys]:
                                criteria_count += 1
                                if criteria_count == criteria_total:
                                    count += 1
                    else:
                        if val_at_doc == val_at_where_dict:
                            criteria_count += 1
                            if criteria_count == criteria_total:
                                count += 1
                else:
                    break
        return count

    def delete(self, where_dict):
        """
        delete matching doc(s) from the collection.
        """
        if where_dict == {}:
            self.data = []
        for doc in self.data:
            criteria_count = 0
            criteria_total = len(where_dict.keys())
            for key in where_dict.keys():
                if key in doc:
                    val_at_doc = doc[key]
                    val_at_where_dict = where_dict[key]
                    if isinstance(val_at_where_dict) == dict:
                        for more_keys in val_at_where_dict.keys():
                            if more_keys in val_at_doc and val_at_doc[more_keys] == val_at_where_dict[more_keys]:
                                criteria_count += 1
                                if criteria_count == criteria_total:
                                    self.data.remove(doc)
                    else:
                        if val_at_doc == val_at_where_dict:
                            criteria_count += 1
                            if criteria_count == criteria_total:
                                self.data.remove(doc)
                else:
                    break

    def update(self, where_dict, changes_dict):
        """
        update matching doc(s) with the values provided.
        """
        for doc in self.data:
            criteria_count = 0
            criteria_total = len(where_dict.keys())
            for key in where_dict.keys():
                if key in doc:
                    val_at_doc = doc[key]
                    val_at_where_dict = where_dict[key]
                    if type(val_at_where_dict) == dict:
                        for more_keys in val_at_where_dict.keys():
                            if more_keys in val_at_doc and val_at_doc[more_keys] == val_at_where_dict[more_keys]:
                                criteria_count += 1
                                if criteria_count == criteria_total:
                                    for k in changes_dict.keys():
                                        self.data[doc][k] = changes_dict[k]
                    else:
                        if val_at_doc == val_at_where_dict:
                            criteria_count += 1
                            if criteria_count == criteria_total:
                                for k in changes_dict.keys():
                                    doc[k] = changes_dict[k]
                else:
                    break

    def map_reduce(self, map_function, reduce_function):
        """
        applies a map_function to each document, collating the results.
        then applies a reduce function to the set, returning the result.
        """
        map_func_result_lst = []
        for doc in self.data:
            result = map_function(doc)
            map_func_result_lst.append(result)
        ans = 0
        reduce_result = reduce_function(map_func_result_lst)
        ans += reduce_result
        return ans


class database:
    """
    dictionary-like object containing one or more named collections.
    """

    def __init__(self, filename):
        """
        initialize the underlying database. if filename contains data, load it.
        """
        global _ALL_DATABASES
        if filename in _ALL_DATABASES:
            self.db = _ALL_DATABASES[filename]
        else:
            self.db = {}
        self.name = filename

    def get_collection(self, name):
        """
        Create a collection (if new) in the DB and return it.
        """
        if name in self.db:
            return self.db[name]
        else:
            self.db[name] = Collection()
            return self.db[name]

    def drop_collection(self, name):
        """
        Drop the specified collection from the database.
        """
        if name in self.db:
            del self.db[name]

    def get_names_of_collections(self):
        """
        Return a list of the sorted names of the collections in the database.
        """
        result = []
        for collection in self.db:
            result.append(collection)
        return sorted(result)

    def close(self):
        """
        Save and close file.
        """
        global _ALL_DATABASES
        _ALL_DATABASES[self.name] = self.db
        for key, value in self.db.items():
            _ALL_DATABASES[self.name][key] = value.data


names = Collection()
quotes = Collection()

name_docs = [
  {"First": "Josh", "Last":"Nahum"},
  {"First": "Emily", "Last":"Dolson"},
  {"age": 5, "Last": "Nahum"},
  {},
  {"other": "data"},
  {"First": "RaceTrack", "Last": "Nahum"},
  {"First": "RaceTrack", "Last": "Nahum"},
  {"First": "CrashDown", "Last": "Dolson"},
]

quote_docs = [
  {"Name": "Josh", "Quote":"Hello Class"},
  {"Name": "Archon", "Quote":"Power Overwhelming"},
  {"Quote":"Hello World!"},
]

for doc in name_docs:
  names.insert(doc)

for doc in quote_docs:
  quotes.insert(doc)

assert names.find_all() == name_docs
assert quotes.find_all() == quote_docs
