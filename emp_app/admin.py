from django.contrib import admin
from .models import Department, Position, Employee, Leave, PerformanceReview

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'budget', 'created_at')
    search_fields = ('name', 'location')

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'is_leadership')
    list_filter = ('department', 'is_leadership')
    search_fields = ('name', 'department__name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'position', 'email', 'is_active')
    list_filter = ('position', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')
    # Remove readonly_fields since Employee has no created_at/updated_at
    readonly_fields = ()

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'type', 'start_date', 'end_date', 'status')
    list_filter = ('type', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__email')

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_date', 'rating')
    list_filter = ('rating',)
    search_fields = ('employee__first_name', 'employee__last_name')
