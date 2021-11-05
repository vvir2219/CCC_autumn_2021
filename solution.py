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
TOKEN_RETURN = re.compile(r'return')
TOKEN_IF = re.compile(r'if')
TOKEN_ELSE = re.compile(r'else')
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

    def peek_next_token(self, token_re, skip_whitespace=True):
        if skip_whitespace: self.skip_whitespace()

        return bool(parse_token(self._value, token_re, error_on_no_match=False))

def execute_statements(commands):
    for f, args in commands:
        f(args)

def print_statement(unparsed, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_PRINT)

    unparsed.need_next_token(TOKEN_PRINT)
    token = unparsed.get_next_token(BOOLEAN)
    if token is None:
        token = unparsed.get_next_token(INTEGER)

    if token is None:
        token = unparsed.get_next_token(ANYTHING_ELSE)

    return (lambda args: print(args[0], end=""), [token])

def return_statement(unparsed, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_RETURN)

    unparsed.need_next_token(TOKEN_RETURN)
    token = unparsed.get_next_token(BOOLEAN)
    if token is None:
        token = unparsed.get_next_token(INTEGER)

    if token is None:
        token = unparsed.get_next_token(ANYTHING_ELSE)

    return (lambda args: args, [token])

def first_statement(unparsed, parsers):
    for parser in parsers:
        if parser(unparsed, peek=True):
            return parser(unparsed)


def if_statement(unparsed, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_IF)

    boolean = None
    main_branch = []
    alternative_branch = []

    parsers = [print_statement, return_statement]

    unparsed.need_next_token(TOKEN_IF)
    token = unparsed.need_next_token(BOOLEAN); boolean = True if token == "true" else False
    while not unparsed.get_next_token(TOKEN_END):
        main_branch.append(first_statement(unparsed, parsers))

    unparsed.need_next_token(TOKEN_ELSE)
    token = unparsed.need_next_token(BOOLEAN); boolean = True if token == "true" else False
    while not unparsed.get_next_token(TOKEN_END):
        alternative_branch.append(first_statement(unparsed, parsers))
    
    return (lambda args: execute_statements(main_branch) if boolean else execute_statements(alternative_branch), [])


def statement(unparsed):
    parsers = [print_statement, return_statement, if_statement]
    return first_statement(unparsed, parsers)

def program(unparsed):
    commands = []

    unparsed.need_next_token(TOKEN_START)
    while not unparsed.get_next_token(TOKEN_END):
        commands.append(statement(unparsed))

    return commands



## read code
def read_code(filename):
    with open(filename, 'r') as f:
        n = int(f.readline().strip())
        code = f.read()

    return n, code

def run(lvl, no):
    n, code = read_code(f'./level{lvl}/level{lvl}_{no}.in')

    commands = program(ParseableString(code))
    execute_statements(commands)


from sys import argv

if __name__ == "__main__":
    run(2, argv[1])
