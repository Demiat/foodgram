from django import template

register = template.Library()


@register.filter(name='inflect')
def inflect(word):
    words_mapp = {
        'капля': 'капель',
        'батон': 'батонов',
        'кусок': 'кусков',
        'веточка': 'веточек',
        'горсть': 'горстей',
        'банка': 'банок',
        'стакан': 'стаканов',
        'щепотка': 'щепоток',
    }
    return words_mapp.get(word, word)
