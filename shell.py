import rus

while True:
    text = input('рус > ')
    result, error = rus.run('<stdin>', text)

    if error:
        print(error.as_string())
    else:
        print(result)
