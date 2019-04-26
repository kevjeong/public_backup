import requests
import re
from bs4 import BeautifulSoup


def GrabIMDBPage(url):
    """
    This function converts the top250 movies from IMDB page to a list of tuples
    :param url: The url inputed
    :return: The list of parsed information.
    """
    # Convert the url into a html string
    response = requests.get(url)
    html = response.text
    # Parse the string into a readable table
    column_pattern = re.compile(
        '<td class="titleColumn">.*?(\d+).*?<a.*?title="(.*?)" >(.*?)<.*?user ratings">(\d+\.+\d)', re.S)
    return column_pattern.findall(html)


def GrabCSE480Page(url):
    if url == "" or url is None:
        return 0
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find('table')
    table_rows = table.find_all('tr')
    result = []
    for row in table_rows:
        column = row.contents
        week = column[1].string if not None else None
        link = column[3].string if not None else None
        date = column[5].text if not None else None
        notes = column[7].text if not None else None
        result.append((week, link, date, notes,))
    return result


class Action:
    """
    This is the Action class. Do not modify this.
    """

    def __init__(self, object_, transaction, type_):
        self.object_ = object_
        self.transaction = transaction
        assert type_ in ("REQUEST_LOCK", "REQUEST_UNLOCK")
        self.type_ = type_

    def __repr__(self):
        return f"Action({self.object_}, {self.transaction}, {self.type_})"

    def __eq__(self, other):
        return self.object_ == other.object_ and self.transaction == other.transaction and self.type_ == other.type_

class WaitsForGraphTracker:
    """
    Please modify this class.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.object_to_transaction_lock_holder = {}
        self.actions_queued = []

    def _attempt_perform_action(self, action, transaction_to_desired_lock):
        """
        Attempts to perform the action (provided that the transaction is not waiting).
        Returns True if successful.
        """

        # Check if transaction is waiting for another action first
        if (action.transaction in transaction_to_desired_lock and
                transaction_to_desired_lock[action.transaction] != action.object_):
            return False

        if action.type_ == "REQUEST_LOCK":
            lock_holder = self.object_to_transaction_lock_holder.get(action.object_)
            if lock_holder == action.transaction:
                return True
            if lock_holder is None:
                self.object_to_transaction_lock_holder[action.object_] = action.transaction
                return True
        if action.type_ == "REQUEST_UNLOCK":
            lock_holder = self.object_to_transaction_lock_holder.get(action.object_)
            if lock_holder == action.transaction:
                del self.object_to_transaction_lock_holder[action.object_]
                return True
        return False

    def add_action(self, action):
        """
        Indicates the action that the database is trying to perform (see class above).
        Return the list of actions that are queued to be performed once waiting transactions
        are able to run.
        """
        self.actions_queued.append(action)

        while True:
            starting_number_of_actions = len(self.actions_queued)
            unsuccessful_actions = []
            transaction_to_desired_lock = {}
            for action in self.actions_queued:
                was_successful = self._attempt_perform_action(action, transaction_to_desired_lock)
                if not was_successful:
                    unsuccessful_actions.append(action)
                    if action.type_ == "REQUEST_LOCK" and action.transaction not in transaction_to_desired_lock:
                        transaction_to_desired_lock[action.transaction] = action.object_
            self.actions_queued = unsuccessful_actions
            if starting_number_of_actions == len(self.actions_queued):
                break
        return self.actions_queued

    def get_current_graph(self):
        """
        Return a dictionary that represents the waits-for graph of the transactions. The key is
        the name of the transaction that is waiting, and the value the name of the transaction that
        is holding the desired lock.
        """
        graph = {}

        for action in self.actions_queued:
            if action.transaction in graph:
                continue
            if action.type_ == "REQUEST_UNLOCK":
                continue
            assert action.object_ in self.object_to_transaction_lock_holder
            lock_holder = self.object_to_transaction_lock_holder[action.object_]
            graph[action.transaction] = lock_holder

        return graph


result = 0
count = 0
wfgt = WaitsForGraphTracker()
if {} == wfgt.get_current_graph():
    print(result)
    result += 1

count += 1
print(str(count) + ":   " + str(count == result))
remaining_actions = wfgt.add_action(Action("Table_A", "trans_Josh", "REQUEST_LOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Josh", "REQUEST_LOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
# 5
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Josh", "REQUEST_UNLOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_A", "trans_Josh", "REQUEST_UNLOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
print(str(9 == result) + ":    1st part")
####################################################
#
# 10
#
wfgt = WaitsForGraphTracker()
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_A", "trans_Josh", "REQUEST_LOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_LOCK"))
if not remaining_actions:
    print(result)
    result += 1
count += 1

print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
####################
#        15
###############
remaining_actions = wfgt.add_action(Action("Table_B", "trans_Josh", "REQUEST_LOCK"))
if [Action("Table_B", "trans_Josh", "REQUEST_LOCK")] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {"trans_Josh": "trans_Emily"} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_LOCK"))
if [Action("Table_B", "trans_Josh", "REQUEST_LOCK")] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {"trans_Josh": "trans_Emily"} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Josh", "REQUEST_LOCK"))
if [Action("Table_B", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"), ] == remaining_actions:
    print(result)
    result += 1
count += 1
############
# 20
##########
print(str(count) + ":   " + str(count == result))
if {"trans_Josh": "trans_Emily"} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
print(str(count == result) + ":   2nd part")

wfgt = WaitsForGraphTracker()
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_A", "trans_Josh", "REQUEST_LOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_LOCK"))
if [] == remaining_actions:
    # 5
    print(result)
    result += 1
count += 1
############
# 25
#############
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Charles", "REQUEST_LOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_B", "trans_Emily", "REQUEST_UNLOCK"))
if [] == remaining_actions:
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {} == wfgt.get_current_graph():
    # 9
    print(result)
    result += 1
count += 1
##########
# 30
#########
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Josh", "REQUEST_LOCK"))
if [Action("Table_C", "trans_Josh", "REQUEST_LOCK")] == remaining_actions:
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
#  19
if {"trans_Josh": "trans_Charles"} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_A", "trans_Charles", "REQUEST_LOCK"))
if [
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_A", "trans_Charles", "REQUEST_LOCK"),
] == remaining_actions:
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

if {
    'trans_Charles': 'trans_Josh',
    "trans_Josh": "trans_Charles",
} == wfgt.get_current_graph():
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Josh", "REQUEST_UNLOCK"))
if [
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_A", "trans_Charles", "REQUEST_LOCK"),
    Action("Table_C", "trans_Josh", "REQUEST_UNLOCK"),
] == remaining_actions:
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {
    'trans_Charles': 'trans_Josh',
    "trans_Josh": "trans_Charles",
} == wfgt.get_current_graph():
    # 15
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Charles", "REQUEST_UNLOCK"))
if [
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_A", "trans_Charles", "REQUEST_LOCK"),
    Action("Table_C", "trans_Josh", "REQUEST_UNLOCK"),
    Action("Table_C", "trans_Charles", "REQUEST_UNLOCK"),
] == remaining_actions:
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

if {
    'trans_Charles': 'trans_Josh',
    "trans_Josh": "trans_Charles",
} == wfgt.get_current_graph():
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))

remaining_actions = wfgt.add_action(Action("Table_C", "trans_Emily", "REQUEST_LOCK"))
if [
    Action("Table_C", "trans_Josh", "REQUEST_LOCK"),
    Action("Table_A", "trans_Charles", "REQUEST_LOCK"),
    Action("Table_C", "trans_Josh", "REQUEST_UNLOCK"),
    Action("Table_C", "trans_Charles", "REQUEST_UNLOCK"),
    Action("Table_C", "trans_Emily", "REQUEST_LOCK"),
] == remaining_actions:
    print(remaining_actions)
    print(result)
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
if {
    'trans_Charles': 'trans_Josh',
    'trans_Josh': 'trans_Charles',
    'trans_Emily': 'trans_Charles',
} == wfgt.get_current_graph():
    # 19
    print(remaining_actions)
    print(result)
    print(str(38 == result) + ":   all done")
    result += 1
count += 1
print(str(count) + ":   " + str(count == result))
