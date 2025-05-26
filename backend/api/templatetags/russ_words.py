import pymorphy2
from django import template

register = template.Library()
morph = pymorphy2.MorphAnalyzer()


@register.filter(name='inflect')
def inflect(value, word):
    """
    Автоматически склоняет существительное в зависимости от числа.

    :param value: Мера продукта
    :param word: Исходное слово в именительном падеже единственного числа
    :return: Слово в правильной форме

    - morph.parse(word)[0] - морфологический разбор структуры слова,
    возвращает список вариантов, берем первый самый вероятный.
    - make_agree_with_number() служит для согласования формы слова
    с заданным числом, формирует окончание.
    """
    ANSWER = '{} {}'
    return ANSWER.format(
        value,
        morph.parse(word)[0].make_agree_with_number(int(value)).word
    )
