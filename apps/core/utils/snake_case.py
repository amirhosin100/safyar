import string


def get_model_name_snake_case(class_name, replace="_"):
    word = ""
    for i, char in enumerate(class_name):
        word += char.lower()
        if (i != 0) and (i < len(class_name) - 1):
            if (
                class_name[i - 1] in string.ascii_lowercase
                and class_name[i + 1] in string.ascii_uppercase
                and class_name[i] in string.ascii_lowercase
            ):
                word += replace
    return word
