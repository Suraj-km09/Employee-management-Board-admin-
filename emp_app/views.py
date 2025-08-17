from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from .models import Employee, Position, Department
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Employee, Department, Leave, PerformanceReview, Position
import json

# Create your views here.

def index(request):
    return render(request, 'index.html')

def all_emp(request):
    emps = Employee.objects.all()
    context = {
        'emps': emps
    }
    print(context)
    return render(request, 'all_emp.html', context)




def add_emp(request):
    positions = Position.objects.all()  # Get positions for both GET and POST cases
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        position_id = request.POST.get('position')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        dob_str = request.POST.get('date_of_birth')
        hire_str = request.POST.get('hire_date')

        # Validate and convert dates
        try:
            date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            hire_date = datetime.strptime(hire_str, '%Y-%m-%d').date()

            # Prevent unrealistic years (like 0232)
            if date_of_birth and date_of_birth.year < 1900:
                messages.error(request, "Date of birth must be after 1900.")
                return render(request, 'add_emp.html', {'positions': positions})
                
            if hire_date.year < 1900:
                messages.error(request, "Hire date must be after 1900.")
                return render(request, 'add_emp.html', {'positions': positions})

            # Get Position instance
            position = Position.objects.get(id=position_id)

            # Save new employee
            new_emp = Employee(
                first_name=first_name,
                last_name=last_name,
                position=position,
                email=email,
                phone=phone,
                address=address,
                date_of_birth=date_of_birth,
                hire_date=hire_date
            )
            new_emp.save()
            
            # Add success message and redirect to same page to show the message
            messages.success(request, "Employee added successfully!")
            return redirect('add_emp')

        except Position.DoesNotExist:
            messages.error(request, "Position not found.")
        except ValueError as e:
            messages.error(request, f"Invalid date format or value: {e}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {e}")
        
        # If we get here, there was an error - redisplay form with error message
        return render(request, 'add_emp.html', {
            'positions': positions,
            'form_data': request.POST  # Pass back form data to repopulate fields
        })

    # GET request - just show the form
    return render(request, 'add_emp.html', {'positions': positions})
   



def remove_emp(request, emp_id=0):
    if emp_id:
        try:
            emp_to_be_removed = Employee.objects.get(id=emp_id)
            emp_name = f"{emp_to_be_removed.first_name} {emp_to_be_removed.last_name}"
            emp_to_be_removed.delete()
            messages.success(request, f"Successfully removed employee: {emp_name}")
            return redirect('remove_emp')
        except Employee.DoesNotExist:
            messages.error(request, "Employee with the given ID does not exist.")
            return redirect('remove_emp')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('remove_emp')

    emps = Employee.objects.all()
    context = {'emps': emps}
    return render(request, 'remove_emp.html', context)



def filter_emp(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        position = request.POST.get('position', '').strip()
        hire_date = request.POST.get('hire_date', '').strip()

        emps = Employee.objects.all()

        if name:
            emps = emps.filter(first_name__icontains=name) | emps.filter(last_name__icontains=name)
        
        if position:
            emps = emps.filter(position__name__icontains=position)

        if hire_date:
            emps = emps.filter(hire_date__gte=hire_date)

        context = {'emps': emps}
        return render(request, 'filter_emp.html', context)
    
    return render(request, 'filter_emp.html')


def index(request):
    today = timezone.now().date()
    one_month_ago = today - timedelta(days=30)

    # Employee statistics
    employees = Employee.objects.all()
    total_employees = employees.count()
    active_employees = employees.filter(is_active=True).count()
    new_hires = employees.filter(hire_date__gte=one_month_ago).count()
    resignations = employees.filter(is_active=False, termination_date__gte=one_month_ago).count()

    # Gender distribution
    gender_stats = employees.values('gender').annotate(count=Count('id'))
    male_count = next((x['count'] for x in gender_stats if x['gender'] == 'M'), 0)
    female_count = next((x['count'] for x in gender_stats if x['gender'] == 'F'), 0)
    other_count = next((x['count'] for x in gender_stats if x['gender'] == 'O'), 0)

    # Department distribution (avoid property conflict)
    departments = Department.objects.annotate(
        total_employees=Count('positions__employees')
    ).order_by('-total_employees')
    dept_names = [dept.name for dept in departments]
    dept_counts = [dept.total_employees for dept in departments]

    # Turnover trend (last 12 months)
    months = []
    hires_data = []
    resignations_data = []
    for i in range(11, -1, -1):
        month = today - timedelta(days=30*i)
        months.append(month.strftime("%b %Y"))

        hires = Employee.objects.filter(
            hire_date__month=month.month,
            hire_date__year=month.year
        ).count()
        hires_data.append(hires)

        resigns = Employee.objects.filter(
            is_active=False,
            termination_date__month=month.month,
            termination_date__year=month.year
        ).count()
        resignations_data.append(resigns)

    # Performance
    avg_performance = PerformanceReview.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    # Attendance
    on_leave = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        status='Approved'
    ).count()
    present_today = active_employees - on_leave
    attendance_rate = round((present_today / active_employees) * 100) if active_employees else 0

    # Upcoming leaves
    upcoming_leaves = Leave.objects.filter(start_date__gte=today, status='Approved').order_by('start_date')[:5]

    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'new_hires': new_hires,
        'resignations': resignations,
        'male_count': male_count,
        'female_count': female_count,
        'other_count': other_count,
        'dept_names': json.dumps(dept_names),
        'dept_counts': json.dumps(dept_counts),
        'months': json.dumps(months),
        'hires_data': json.dumps(hires_data),
        'resignations_data': json.dumps(resignations_data),
        'avg_performance': round(avg_performance, 1),
        'present_today': present_today,
        'attendance_rate': attendance_rate,
        'on_leave': on_leave,
        'upcoming_leaves': upcoming_leaves,
        'pending_approvals': Leave.objects.filter(status='Pending').count(),
        'expiring_contracts': Employee.objects.filter(
            contract_end_date__range=(today, today + timedelta(days=30))
        ).count(),
    }
    return render(request, 'index.html', context)