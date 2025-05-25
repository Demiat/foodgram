from django import template

register = template.Library()


@register.filter('russian_months')
def russian_months(date):
    """Возвращает дату с месяцем в родительном падеже."""

    month_names = {
        1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля',
        5: 'Мая', 6: 'Июня', 7: 'Июля', 8: 'Августа',
        9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'
    }
    return f'{date.day} {month_names[date.month]} {date.year}'
