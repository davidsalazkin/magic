from src import magic
import sys

runCommand = "ЗАПУСК(\"" + sys.argv[1] + "\")"

result, error = magic.run('<stdin>', runCommand)

if error:
    print(error.as_string())
elif result:
    if len(result.elements) == 1:
        print(repr(result.elements[0]))
    else:
        print(repr(result))
