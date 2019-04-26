import json


class NotValidError(Exception):
    pass


class NotWellFormedError(Exception):
    pass


class Validator(object):
    def __init__(self, schema=None):
        try:
            self.schema = json.loads(schema)
        except json.JSONDecodeError:
            raise NotWellFormedError
        self.types = {"object", "null", "boolean", "array", "number", "integer", "string"}
        self.not_valid_error = NotValidError()
        self.not_wf_error = NotWellFormedError()

    def validate(self, data):
        def type_validate(given_data, schema):
            if "type" not in schema:
                return True
            elem_type = schema["type"]
            if elem_type not in self.types:
                raise self.not_wf_error
            elif elem_type == "boolean" and not isinstance(given_data, bool):
                raise self.not_valid_error
            elif elem_type == "string" and isinstance(given_data, str):
                raise self.not_valid_error
            elif elem_type == "integer" and isinstance(given_data, int):
                raise self.not_valid_error
            elif elem_type == "array" and not list_validate(given_data, schema):
                raise self.not_valid_error
            elif elem_type == "number" and not isinstance(given_data, float):
                raise self.not_valid_error
            elif elem_type == "object" and not obj_validate(given_data, schema):
                raise self.not_valid_error
            elif elem_type == "null" and given_data is not None:
                raise self.not_valid_error
            else:
                return True

        def list_validate(given_data, schema):
            def ascending_check(lst):
                if len(lst) <= 1:
                    return True
                prev = lst[0]
                for i in range(1,len(given_data)):
                    if lst[i] > prev or lst[i] == prev:
                        prev = lst[i]
                    else:
                        return False
                return True

            def unique_check(lst):
                cache = {}
                for i in lst:
                    if i in cache:
                        cache[i] += 1
                    else:
                        cache[i] = 1
                for elem in cache.values():
                    if elem != 1:
                        return False
                return True

            def spartan_check(spartan_lst):
                possibilities = {"green", "white"}
                if len(spartan_lst) <= 0:
                    return True
                for spartan in spartan_lst:
                    if spartan not in possibilities:
                        return False
                return True

            def element_check(elem_data, element_schema):
                elem_type = element_schema['type']
                if elem_type not in self.types:
                    raise self.not_wf_error
                if len(elem_data) != 0:
                    for element in elem_data:
                        type_validate(element, elem_schema)

            if isinstance(given_data, list):
                if "qualities" in schema:
                    qualities = schema["qualities"]
                    if len(qualities) > 0:
                        for i in range(len(qualities)):
                            if qualities[i] == "ascending" and not ascending_check(given_data):
                                raise self.not_valid_error
                            if qualities[i] == "unique" and not unique_check(given_data):
                                raise self.not_valid_error
                            if qualities[i] == "nonempty" and len(given_data) <= 0:
                                raise self.not_valid_error
                            if qualities[i] == "spartan" and not spartan_check(given_data):
                                raise self.not_valid_error
                if "element" in schema:
                    elem_schema = json.loads(json.dumps(schema['element']))
                    if element_check(given_data, elem_schema):
                        for elem in given_data:
                                type_validate(decoder.decode(json.dumps(elem)), elem_schema)
                return True
            else:
                raise self.not_valid_error

        def obj_validate(given_data, schema):
            def obj_field_check(obj_field_data, obj_schema):
                if len(obj_field_data.keys()) < len(obj_schema["fields"]):
                    raise self.not_valid_error
                for field in obj_schema["fields"]:
                    if field not in obj_field_data:
                        raise self.not_valid_error
                return True

            if not isinstance(given_data, dict):
                raise self.not_valid_error
            if len(given_data) == 0 and "fields" in schema:
                raise self.not_valid_error
            schema_cache = {}
            if "fields" in schema:
                obj_field_check(given_data, schema)
            if "fields_qualities" in schema:
                if len(schema["fields_qualities"]) > 0 and len(given_data) == 0:
                    raise self.not_valid_error
                for quality in schema["fields_qualities"]:
                    if quality not in given_data:
                        raise self.not_valid_error
                    schema_cache[quality] = json.loads(json.dumps(schema["fields_qualities"][quality]))
            for obj_data in given_data:
                if obj_data in schema_cache:
                    if not type_validate(given_data[obj_data], schema_cache[obj_data]):
                        raise self.not_valid_error
            return True

        decoder = json.JSONDecoder()
        try:
            type_validate(decoder.decode(data), self.schema)
        except json.JSONDecodeError:
            raise self.not_wf_error


def build_validator(schema_string):
    new_validator = Validator(schema_string)
    return new_validator
