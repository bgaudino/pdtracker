import re


def average(values):
    return sum(values) / len(values) if values else 0


def snake_to_camel(snake_str):
    components = snake_str.split("-")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_title(camel_str):
    title_str = re.split(r"(?=[A-Z])", camel_str)
    return " ".join(title_str).title()


def camel_to_snake(camel_str):
    snake_str = re.split(r"(?=[A-Z])", camel_str)
    return "-".join(snake_str).lower()
