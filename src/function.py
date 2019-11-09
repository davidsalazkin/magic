from . import magic as ron
from .value import *
from .symboltable import *
from .rtresult import *
from .context import *
from .errors import *
from .number import *
from .String import *
from .List import *

import sys, os, math, random

class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<анонимная>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)

        return new_context

    def check_args(self, arg_names, args):
        res = RTResult()

        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"слишком много аргументов передано в '{self.name}' (количество: {len(args) - len(arg_names)})",
                self.context
            ))

        if len(args) < len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"слишком мало аргументов передано в '{self.name}' (количество: {len(arg_names) - len(args)})",
                self.context
            ))

        return res.success(None)

    def populate_args(self, arg_names, args, exec_ctx):
        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return(): return res
        self.populate_args(arg_names, args, exec_ctx)
        return res.success(None)

class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return

    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
        if res.should_return(): return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value == None: return res

        ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
        return res.success(ret_value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<Функция {self.name}>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RTResult()
        exec_ctx = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
        if res.should_return(): return res

        return_value = res.register(method(exec_ctx))
        if res.should_return(): return res
        return res.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f'execute_{self.name} метод не определён')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<встроенная функция {self.name}>"

    ######### Built-In Functions #########

    ## General functions ##

    def execute_print(self, exec_ctx):
        print(str(exec_ctx.symbol_table.get('value')))
        return RTResult().success(Number.null)
    execute_print.arg_names = ['value']

    def execute_string(self, exec_ctx):
        return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
    execute_string.arg_names = ['value']

    def execute_int(self, exec_ctx):
        element = exec_ctx.symbol_table.get('value')
        while True:
            try:
                number = int(element.value)
                break
            except ValueError:
                print(f"Аргумент должен быть числом.")
        return RTResult().success(Number(number))
    execute_int.arg_names = ['value']

    def execute_input(self, exec_ctx):
        text = input()
        return RTResult().success(String(text))
    execute_input.arg_names = []

    def execute_input_int(self, exec_ctx):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' должен быть целым числом. Попробуй еще раз!")
        return RTResult().success(Number(number))
    execute_input_int.arg_names = []

    def execute_clear(self, exec_ctx):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ["value"]

    def execute_is_string(self, exec_ctx):
        is_string = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ['value']

    def execute_is_list(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_list.arg_names = ["value"]

    def execute_is_function(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_function.arg_names = ["value"]

    def execute_run(self, exec_ctx):
        fn = exec_ctx.symbol_table.get("fn")

        if not isinstance(fn, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть строкой", exec_ctx))

        fn = fn.value

        try:
            with open(fn, "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, f"Не удалось загрузить файл \"{fn}\"\n" + str(e), exec_ctx))

        _, error = ron.run(fn, script)

        if error:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, f"Не удалось загрузить файл \"{fn}\"\n" + error.as_string(), exec_ctx))

        return RTResult().success(Number.null)
    execute_run.arg_names = ["fn"]

    ## List functions

    def execute_append(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Первый аргумент должен быть список.", exec_ctx))

        list_.elements.append(value)
        return RTResult().success(Number.null)
    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Первый аргумент должен быть список.", exec_ctx))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Второй аргумент должен быть индекс элемента.", exec_ctx))

        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Элемент у этого индекса не может быть удален из списка, поскольку индекс находится за пределами границ", exec_ctx))
        return RTResult().success(element)
    execute_pop.arg_names = ['list', 'index']

    def execute_extend(self, exec_ctx):
        listA = exec_ctx.symbol_table.get("listA")
        listB = exec_ctx.symbol_table.get("listB")

        if not isinstance(listA, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Первый аргумент должен быть список.", exec_ctx))

        if not isinstance(listB, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Второй аргумент должен быть список.", exec_ctx))

        listA.elements.extend(listB.elements)
        return RTResult().success(Number.null)
    execute_extend.arg_names = ["listA", "listB"]

    def execute_length(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        length = len(list_.elements)
        return RTResult().success(Number(length))
    execute_length.arg_names = ['list_']

    def execute_sorted(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")
        pythonList = []

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        for number in list_.elements:
            pythonList.append(number.value)

        return RTResult().success(List(sorted(pythonList)))
    execute_sorted.arg_names = ["list_"]

    def execute_min(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")
        pythonList = []

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        for number in list_.elements:
            pythonList.append(number.value)

        return RTResult().success(Number(min(pythonList)))
    execute_min.arg_names = ["list_"]

    def execute_max(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")
        pythonList = []

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        for number in list_.elements:
            pythonList.append(number.value)

        return RTResult().success(Number(max(pythonList)))
    execute_max.arg_names = ["list_"]

    def execute_sum(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")
        pythonList = []

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        for number in list_.elements:
            pythonList.append(number.value)

        return RTResult().success(Number(sum(pythonList)))
    execute_sum.arg_names = ["list_"]

    def execute_set(self, exec_ctx):
        list_ = exec_ctx.symbol_table.get("list_")
        pythonList = []

        if not isinstance(list_, List):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть список.", exec_ctx))

        for number in list_.elements:
            pythonList.append(number.value)

        return RTResult().success(List(list(set(pythonList))))
    execute_set.arg_names = ["list_"]

    # Math functions

    def execute_sqrt(self, exec_ctx):
        number = exec_ctx.symbol_table.get("value")

        if not isinstance(number, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(math.sqrt(number.value)))
    execute_sqrt.arg_names = ["value"]

    def execute_pow(self, exec_ctx):
        base = exec_ctx.symbol_table.get("base")
        exp = exec_ctx.symbol_table.get("exp")

        if not isinstance(base, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Первый аргумент должен быть числом.", exec_ctx))

        if not isinstance(exp, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Второй аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(math.pow(base.value, exp.value)))
    execute_pow.arg_names = ["base", "exp"]

    def execute_abs(self, exec_ctx):
        number = exec_ctx.symbol_table.get("value")

        if not isinstance(number, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(abs(number.value)))
    execute_abs.arg_names = ["value"]

    def execute_round(self, exec_ctx):
        number = exec_ctx.symbol_table.get("value")

        if not isinstance(number, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(round(number.value)))
    execute_round.arg_names = ["value"]

    def execute_randint(self, exec_ctx):
        lo = exec_ctx.symbol_table.get("lo")
        hi = exec_ctx.symbol_table.get("hi")

        if not isinstance(lo, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Первый аргумент должен быть числом.", exec_ctx))

        if not isinstance(hi, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Второй аргумент должен быть числом.", exec_ctx))

        if lo.value >= hi.value:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Второй аргумент должен быть больше первого.", exec_ctx))
        else:
            return RTResult().success(Number(random.randint(lo.value, hi.value)))
    execute_randint.arg_names = ["lo", "hi"]

    def execute_ceil(self, exec_ctx):
        number = exec_ctx.symbol_table.get("value")

        if not isinstance(number, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(math.ceil(number.value)))
    execute_ceil.arg_names = ["value"]

    def execute_floor(self, exec_ctx):
        number = exec_ctx.symbol_table.get("value")

        if not isinstance(number, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Аргумент должен быть числом.", exec_ctx))

        return RTResult().success(Number(math.floor(number.value)))
    execute_floor.arg_names = ["value"]

# General
BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.string      = BuiltInFunction("string")
BuiltInFunction.int         = BuiltInFunction("int")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.run         = BuiltInFunction("run")
# List
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.length      = BuiltInFunction("length")
BuiltInFunction.sorted      = BuiltInFunction("sorted")
BuiltInFunction.min         = BuiltInFunction("min")
BuiltInFunction.max         = BuiltInFunction("max")
BuiltInFunction.sum         = BuiltInFunction("sum")
BuiltInFunction.set         = BuiltInFunction("set")
# Math
BuiltInFunction.sqrt        = BuiltInFunction("sqrt")
BuiltInFunction.pow         = BuiltInFunction("pow")
BuiltInFunction.abs         = BuiltInFunction("abs")
BuiltInFunction.round       = BuiltInFunction("round")
BuiltInFunction.randint     = BuiltInFunction("randint")
BuiltInFunction.ceil        = BuiltInFunction("ceil")
BuiltInFunction.floor       = BuiltInFunction("floor")

from .interpreter import Interpreter