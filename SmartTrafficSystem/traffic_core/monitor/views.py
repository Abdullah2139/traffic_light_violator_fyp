from xhtml2pdf import pisa
from django.shortcuts import render
from .models import Violation
from django.db.models import Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import datetime

def dashbord(request):
    # 1. Fetch the data from the database first
    violations_list = Violation.objects.all().order_by('-timestamp')

    # 2. Run calculations on the 'violations_list' QuerySet, not the Model itself
    total_fines = violations_list.aggregate(total_amount=Sum('fine_amount'))['total_amount'] or 0
    total_count = violations_list.count()

    # 3. Pass the data to the context dictionary
    context = {
        'violations': violations_list, # Make sure this matches the name used in your HTML loop
        'total_fines': total_fines,
        'total_count': total_count,
    }
    
    return render(request, 'monitor/dashboard.html', context)

def export_pdf(request):
    # Fetch data
    violations = Violation.objects.all().order_by('-timestamp')
    total_fines = violations.aggregate(total=Sum('fine_amount'))['total'] or 0

    print(f"DEBUG: Found {violations.count()} violations for PDF")

    context = {
        'violations': violations,
        'total_fines': total_fines,
        'generated_on': datetime.now(),
    }

    html_string = render_to_string('monitor/pdf_report.html', context)
    
    # Prepare response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Traffic_Report.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response
