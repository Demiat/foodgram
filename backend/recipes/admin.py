from django.contrib import admin

from .models import Recipe, Ingredient, Tag, RecipeIngredient

admin.site.empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin): pass
    # list_display = ('recipe', 'ingredient', 'amount')
