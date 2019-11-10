#######################################
# RUN
#######################################

from .parser import *
from .lexer import *
from .interpreter import *
from .symboltable import *
import math

# Constants
Number.null = Number(0)
Number.true = Number(1)
Number.false = Number(0)
Number.math_E = Number(math.e)
Number.math_PI = Number(math.pi)
Number.math_TAU = Number(math.tau)
Number.math_INF = Number(math.inf)

global_symbol_table = SymbolTable()
# Constants
global_symbol_table.set("ПУСТОЙ", Number.null)
global_symbol_table.set("ИСТИНА", Number.true)
global_symbol_table.set("ЛОЖЬ", Number.false)
global_symbol_table.set("Е", Number.math_E)
global_symbol_table.set("ПИ", Number.math_PI)
global_symbol_table.set("ТАУ", Number.math_TAU)
global_symbol_table.set("БЕСКОНЕЧНОСТЬ", Number.math_INF)
# General Functions
global_symbol_table.set("СООБЩИТЬ", BuiltInFunction.print)
global_symbol_table.set("СТРОКА", BuiltInFunction.string)
global_symbol_table.set("ЦЕЛОЕ", BuiltInFunction.int)
global_symbol_table.set("ВВОД", BuiltInFunction.input)
global_symbol_table.set("ВВОД_ЧИС", BuiltInFunction.input_int)
global_symbol_table.set("ОЧИСТИТЬ", BuiltInFunction.clear)
global_symbol_table.set("ЕСТЬ_ЧИСЛО", BuiltInFunction.is_number)
global_symbol_table.set("ЕСТЬ_СТРОКА", BuiltInFunction.is_string)
global_symbol_table.set("ЕСТЬ_СПИСОК", BuiltInFunction.is_list)
global_symbol_table.set("ЕСТЬ_ФУНКЦИЯ", BuiltInFunction.is_function)
global_symbol_table.set("ЗАПУСК", BuiltInFunction.run)
# List Functions
global_symbol_table.set("ДОБАВИТЬ", BuiltInFunction.append)
global_symbol_table.set("ИЗВЛЕКАТЬ", BuiltInFunction.pop)
global_symbol_table.set("ОБЬЕДИНИТЬ", BuiltInFunction.extend)
global_symbol_table.set("ДЛИНА", BuiltInFunction.length)
global_symbol_table.set("СОРТ", BuiltInFunction.sorted)
global_symbol_table.set("МИН", BuiltInFunction.min)
global_symbol_table.set("МАКС", BuiltInFunction.max)
global_symbol_table.set("СУМ", BuiltInFunction.sum)
global_symbol_table.set("КОМПЛЕКТ", BuiltInFunction.set)
global_symbol_table.set("ОБРАТНЫЙ", BuiltInFunction.reverse)

# Math Functions
global_symbol_table.set("КВАД_КОР", BuiltInFunction.sqrt)
global_symbol_table.set("ЭКСПОНЕНТА", BuiltInFunction.pow)
global_symbol_table.set("АБСОЛЮТНАЯ", BuiltInFunction.abs)
global_symbol_table.set("ОКРУГЛИТЬ", BuiltInFunction.round)
global_symbol_table.set("СЛУЧАЙНЫЙ", BuiltInFunction.randint)
global_symbol_table.set("ПОТОЛОК", BuiltInFunction.ceil)
global_symbol_table.set("ПОЛ", BuiltInFunction.floor)
global_symbol_table.set("ФАКТОРИАЛ", BuiltInFunction.factorial)
global_symbol_table.set("СБОД", BuiltInFunction.gcd)
global_symbol_table.set("КОС", BuiltInFunction.cos)
global_symbol_table.set("СИН", BuiltInFunction.sin)
global_symbol_table.set("ТАН", BuiltInFunction.tan)

def run(fn, text):
    # Generate tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run program
    interpreter = Interpreter()
    context = Context('<программа>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
