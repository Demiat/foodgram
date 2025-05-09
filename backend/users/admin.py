from django.contrib import admin

from .models import Follow

admin.site.empty_value_display = '-пусто-'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass
