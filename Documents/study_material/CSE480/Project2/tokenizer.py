import string


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

