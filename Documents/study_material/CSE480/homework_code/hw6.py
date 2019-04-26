def is_conflict_serializable(schedule):
    precedence = determine_precedence(schedule)
    unique_path = set()
    cache = {}
    for element in precedence:
        if element[0] not in cache:
            cache[element[0]] = element[1]

    start = precedence[0][0]
    while start in cache:
        if cache[start] in cache:
            start = cache[start]
            if start not in unique_path:
                unique_path.add(start)
            else:
                return False
    return True

def determine_precedence(list_of_actions):
    conflict_cache = set()
    list_length = len(list_of_actions)
    for i in range(list_length):
        for j in range(i+1, list_length):
            if detect_conflict(list_of_actions[i], list_of_actions[j]) and \
               list_of_actions[i].transaction != list_of_actions[j].transaction:
                conflict_cache.add((list_of_actions[i].transaction, list_of_actions[j].transaction))
    conflict_cache = list(conflict_cache)
    return sorted(conflict_cache)

def detect_conflict(action_a, action_b):
    if action_a.is_write and action_b.is_write:
        if action_a.object_ == action_b.object_:
            return True
    if action_a.is_write and not action_b.is_write:
        if action_a.object_ == action_b.object_:
            return True
    if action_a.object_ == action_b.object_:
        if not action_a.is_write and not action_b.is_write:
            return False
        return True
    if action_a.transaction == action_b.transaction:
            return True
    return False

class Action:
  def __init__(self, object_, transaction, is_write):
    self.object_ = object_
    self.transaction = transaction
    self.is_write = is_write
  def __str__(self):
    return f"Action({self.object_}, {self.transaction}, {self.is_write})"
  __repr__ = __str__

actions = [
  Action(object_="A", transaction="T2", is_write=False),
  Action(object_="B", transaction="T1", is_write=False),
  Action(object_="A", transaction="T2", is_write=True),
  Action(object_="A", transaction="T3", is_write=False),
  Action(object_="B", transaction="T1", is_write=True),
  Action(object_="A", transaction="T3", is_write=True),
  Action(object_="B", transaction="T2", is_write=False),
  Action(object_="B", transaction="T1", is_write=True),
  Action(object_="B", transaction="T2", is_write=True),
  ]

result = is_conflict_serializable(actions)
print(f"Result = {result}")

expected = False
print(f"Expected = {expected}")

assert expected == result
