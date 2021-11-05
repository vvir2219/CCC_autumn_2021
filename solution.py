# i will parse using "combinators", each combinator would be given a string and will return a token and the rest of the string
# combinator --string--> (token, string)

# function -> name [statement..] end
# program -> [function..] start_function
# start_function -> start [statement..] end

# environment = { <variable-name> : (value, type) }

import re

debug = False

# token regular expressions
WHITESPACE = re.compile(r'\s*')
TOKEN_START = re.compile(r'start')
TOKEN_END = re.compile(r'end')
TOKEN_PRINT = re.compile(r'print')
TOKEN_RETURN = re.compile(r'return')
TOKEN_IF = re.compile(r'if')
TOKEN_ELSE = re.compile(r'else')
TOKEN_VAR = re.compile(r'var')
TOKEN_SET = re.compile(r'set')

BOOLEAN = re.compile(r'true|false')
INTEGER = re.compile(r'[1-9][0-9]*')
ANYTHING = re.compile(r'[^\s]+')

TYPE_BOOLEAN = 1
TYPE_INTEGER = 2
TYPE_STRING = 3
TYPE_ANYTHING = 4
TYPE_VAR = 5

ALL_TOKENS = [
        TOKEN_START,
        TOKEN_END,
        TOKEN_PRINT,
        TOKEN_RETURN,
        TOKEN_IF,
        TOKEN_ELSE,
        TOKEN_VAR,
        TOKEN_SET,
        BOOLEAN,
        INTEGER
]

def is_known_token(something):
    return not something[1]

# returns (<parsed-token>, <is_known_token>:boolean)
def anything_else(unparsed):
    global ALL_TOKENS

    for token_def in ALL_TOKENS:
        if unparsed.peek_next_token(token_def):
            token = unparsed.get_next_token(token_def)
            return token, False

    return unparsed.get_next_token(ANYTHING), True


PRINT_STATEMENT = 1;
RETURN_STATEMENT = 2;
IF_STATEMENT = 3;
VAR_STATEMENT = 4;
SET_STATEMENT = 4;


COMMA = re.compile(r',')
OPEN_PAREN = re.compile(r'\(')
CLOSED_PAREN = re.compile(r'\)')
STRING = re.compile(r'"(\\.|[^"])*"')

def type(s):
    return s[1]

def value(s):
    return s[0]

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
    for f, statement_type in commands:
        if f() == False:
            break

def pack(f, args, environ):

    def do():
        nonlocal args, environ
        return f(args, environ)

    return do

def print_statement(unparsed, environ, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_PRINT)

    unparsed.need_next_token(TOKEN_PRINT)
    token = unparsed.get_next_token(BOOLEAN)
    if token is None:
        token = unparsed.get_next_token(INTEGER)

    if token is None:
        token = unparsed.get_next_token(ANYTHING)

    if debug: print(f'print {token}');
    end = "" if not debug else "\n"

    def do_print(args, environ):
        if args[0] in environ:
            print(environ[args[0]], end="")
        else:
            print(args[0])

    return (pack(do_print, [token], environ), PRINT_STATEMENT)

def return_statement(unparsed, environ, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_RETURN)

    unparsed.need_next_token(TOKEN_RETURN)
    token = unparsed.get_next_token(BOOLEAN)
    if token is None:
        token = unparsed.get_next_token(INTEGER)

    if token is None:
        token = unparsed.get_next_token(ANYTHING)

    if debug: print(f'return {token}')
    return (pack(lambda args, environ: False, [token], environ), RETURN_STATEMENT)

def first_statement(unparsed, environ, parsers):
    for parser in parsers:
        if parser(unparsed, environ, peek=True):
            return parser(unparsed, environ)

def first_token(unparsed, token_associations):
    for token_def, type_def in token_associations:
        if unparsed.peek_next_token(token_def):
            return type_def, unparsed.get_next_token(token_def)

    return None, None

def var_statement(unparsed, environ, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_VAR)

    unparsed.need_next_token(TOKEN_VAR)
    var_name, is_var_name = anything_else(unparsed)
    if not is_var_name:
        raise ValueError(f'Token not found.\nString: {unparsed}\nPattern: {ANYTHING}')

    variable_types = [ (BOOLEAN, TYPE_BOOLEAN), (INTEGER, TYPE_INTEGER) ]
    var_type, var_value = first_token(unparsed, variable_types) 
    if var_type is None:
        var_type, var_value = TYPE_ANYTHING, unparsed.need_next_token(ANYTHING)

    def do_var_declaration(args, environ):
        nonlocal var_name, var_type, var_value

        if var_name in environ:
            print("ERROR")
            return False
        
        if var_type == TYPE_ANYTHING:
            if var_value in environ:
                environ[var_name] = environ[var_value]
            else:
                environ[var_name] = (var_value, TYPE_STRING)
        else:
            environ[var_name] = (var_value, var_type)

    return (pack(do_var_declaration, [], environ), VAR_STATEMENT)
    
def set_statement(unparsed, environ, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_SET)

    unparsed.need_next_token(TOKEN_SET)
    var_name, is_var_name = anything_else(unparsed)
    if not is_var_name:
        raise ValueError(f'Token not found.\nString: {unparsed}\nPattern: {ANYTHING}')

    variable_types = [ (BOOLEAN, TYPE_BOOLEAN), (INTEGER, TYPE_INTEGER) ]
    var_type, var_value = first_token(unparsed, variable_types) 
    if var_type is None:
        var_type, var_value = TYPE_ANYTHING, unparsed.need_next_token(ANYTHING)

    def do_set(args, environ):
        nonlocal var_name, var_type, var_value

        if var_name not in environ:
            print("ERROR")
            return False
        
        if var_type == TYPE_ANYTHING:
            if var_value in environ:
                environ[var_name] = environ[var_value]
            else:
                environ[var_name] = (var_value, TYPE_STRING)
        else:
            environ[var_name] = (var_value, var_type)

    return (pack(do_var_declaration, [], environ), VAR_STATEMENT)


def if_statement(unparsed, environ, peek=False):
    if peek:
        return unparsed.peek_next_token(TOKEN_IF)

    condition = None
    condition_type = None 

    main_branch = []
    alternative_branch = []

    unparsed.need_next_token(TOKEN_IF)

    token = unparsed.get_next_token(BOOLEAN);
    if token is None:
        condition = unparsed.need_next_token(ANYTHING)
        condition_type = TYPE_VAR
    else:
        condition = True if token == "true" else False
        condition_type = TYPE_BOOLEAN


    if debug: print(f'if {token}')

    while not unparsed.get_next_token(TOKEN_END):
        curr_statement = statement(unparsed, environ)
        main_branch.append(curr_statement)

    if debug: print(f'end')

    unparsed.need_next_token(TOKEN_ELSE)
    if debug: print(f'else')
    while not unparsed.get_next_token(TOKEN_END):
        curr_statement = statement(unparsed, environ)
        alternative_branch.append(curr_statement)

    if debug: print(f'end')


    def do_if(args, environ):
        nonlocal condition, condition_type
        main_branch, alternative_branch = args

        cond = None
        if condition_type == TOKEN_VAR:
            if condition not in environ or \
                type(environ[condition]) != TYPE_BOOLEAN:
                    print("ERROR")
                    return False
            cond = value(environ[condition])
        else:
            cond = condition

        if cond:
            return execute_statements(main_branch, environ)
        else:
            return execute_statements(alternative_branch, environ)

    
    return (pack(do_if, (main_branch, alternative_branch), environ)
            , IF_STATEMENT)


def statement(unparsed, environ):
    parsers = [print_statement, return_statement, if_statement, var_statement, set_statement]
    return first_statement(unparsed, environ, parsers)

def program(unparsed, environ):
    commands = []

    unparsed.need_next_token(TOKEN_START)
    if debug: print(f'start')
    while not unparsed.get_next_token(TOKEN_END):
        curr_statement = statement(unparsed, environ)
        commands.append(curr_statement)

    if debug: print(f'end')

    return commands, unparsed


## read code
def read_code(filename):
    with open(filename, 'r') as f:
        n = int(f.readline().strip())
        code = f.read()

    return n, code

def run(lvl, no):
    n, code = read_code(f'./level{lvl}/level{lvl}_{no}.in')
    unparsed = ParseableString(code)

    while len(unparsed.string()) > 0:
        environ = {}
        commands, unparsed = program(ParseableString(code), environ)

        if debug: print("Execution: \n\n")
        if not debug: execute_statements(commands)


from sys import argv

if __name__ == "__main__":
    run(3, argv[1])
