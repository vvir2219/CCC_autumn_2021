# valid elements to parse: whitespace, strings in quotes, commas, open & closed parethesis
# hierarchy -> "(" name [, hierarchy ...] ")"
# name -> \"(\\.|[^\"])*\"

# i will parse using "combinators", each combinator would be given a string and will return a token and the rest of the string
# combinator --string--> (token, string)

# function -> name [statement..] end
# program -> [function..] start_function
# start_function -> start [statement..] end

import re

# token regular expressions
WHITESPACE = re.compile(r'\s*')
TOKEN_START = re.compile(r'start')
TOKEN_END = re.compile(r'end')
TOKEN_PRINT = re.compile(r'print')
BOOLEAN = re.compile(r'true|false')
INTEGER = re.compile(r'[1-9][0-9]*')
ANYTHING_ELSE = re.compile(r'[^\s]+')

ALL_TOKENS = [
        TOKEN_START,
        TOKEN_END,
        TOKEN_PRINT,
        BOOLEAN,
        INTEGER
]


COMMA = re.compile(r',')
OPEN_PAREN = re.compile(r'\(')
CLOSED_PAREN = re.compile(r'\)')
STRING = re.compile(r'"(\\.|[^"])*"')

# string -> (token, string)
# or None or Error (depends on flag)
def parse_token(s, token_re, error_on_no_match=True):
    match = token_re.match(s)
    if match is None:
        if error_on_no_match:
            raise ValueError(f'Token not found.\nString: {s}\nPattern: {token_re.pattern}')
        else:
            return None

    return (match.group(), s[match.end():])

# skips whitespace, returns the string without whitespace
def skip_whitespace(s):
    return parse_token(s, WHITESPACE, error_on_no_match=False)[1]

class ParseableString:
    def __init__(self, s):
        self._value = s

    def string(self):
        return self._value

    def skip_whitespace(self):
        self._value = skip_whitespace(self._value)

    def need_next_token(self, token_re, skip_whitespace=True):
        if skip_whitespace: self.skip_whitespace()

        token, self._value = parse_token(self._value, token_re, error_on_no_match=True)
        return token

    def get_next_token(self, token_re, skip_whitespace=True):
        if skip_whitespace: self.skip_whitespace()

        match = parse_token(self._value, token_re, error_on_no_match=False)
        if match is None: return None

        self._value = match[1]
        return match[0]

def print_statement(unparsed):
    unparsed.need_next_token(TOKEN_PRINT)
    token = unparsed.get_next_token(BOOLEAN)
    if token is None:
        token = unparsed.get_next_token(INTEGER)

    if token is None:
        token = unparsed.get_next_token(ANYTHING_ELSE)

    return (lambda args: print(args[0], end=""), [token])


def program(unparsed):
    commands = []

    unparsed.need_next_token(TOKEN_START)
    while not unparsed.get_next_token(TOKEN_END):
        commands.append(print_statement(unparsed))

    return commands

def execute_program(commands):
    for f, args in commands:
        f(args)

if __name__ == "__main__":
    input_string = 'start print is print this print the print matrix end'

    execute_program(program(ParseableString(input_string)))
