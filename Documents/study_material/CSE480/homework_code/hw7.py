class LegalityOfScheduleViolation(Exception): pass


class TwoPhasedLockingViolation(Exception): pass


class ConsistencyOfTransactionViolation(Exception): pass


def validate_locking_schedule(actions):
    """
    Takes in actions for a scheduler
    and validates it against rules
    of consistency for database
    """
    ls_cache = {}
    for action in actions:
        trans_info = (action.object_, action.transaction)
        if action.type_ == "LOCK":
            if trans_info in ls_cache and ls_cache[trans_info]["lock_flag"]:
                continue
            unlock_flag = finder(trans_info, ls_cache, unlock=True)
            if unlock_flag:
                raise TwoPhasedLockingViolation
            obj_flag = finder(trans_info, ls_cache)
            if obj_flag in ls_cache:
                if not ls_cache[obj_flag]["lock_flag"]:
                    continue
                else:
                    raise LegalityOfScheduleViolation
            if trans_info not in ls_cache:
                ls_cache[trans_info] = {"lock_flag": 1, "READ": 0, "WRITE": 0}
        elif action.type_ == "UNLOCK":
            if trans_info in ls_cache:
                ls_cache[trans_info]["lock_flag"] = 0
            else:
                ls_cache[trans_info] = {"lock_flag": 0, "READ": 0, "WRITE": 0}
        else:
            if trans_info in ls_cache and ls_cache[trans_info]["lock_flag"]:
                ls_cache[trans_info][action.type_] = 1
            else:
                raise ConsistencyOfTransactionViolation
    if finder((0,0), ls_cache, all_unlock=True):
        raise ConsistencyOfTransactionViolation


def finder(search_info, cache, unlock=False, all_unlock=False):
    for key in cache:
        if not unlock:
            obj = key[0]
            if obj == search_info[0]:
                return key
        if unlock:
            trans = key[1]
            if trans == search_info[1] and not cache[key]["lock_flag"]:
                return True
        if all_unlock and cache[key]["lock_flag"]:
            return True
    return False

