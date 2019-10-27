import magic

while True:
    text = input('магия > ')
    result, error = magic.run('<stdin>', text)

    if error:
        print(error.as_string())
    elif result:
        print(repr(result))
