from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from django.db.models import Q

def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'vehicle/index.html')


#for showing signup/login button for customer
def customerclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'vehicle/customerclick.html')

#for showing signup/login button for mechanics
def mechanicsclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'vehicle/mechanicsclick.html')


#for showing signup/login button for ADMIN(by sumit)
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')


def customer_signup_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request,'vehicle/customersignup.html',context=mydict)


# def mechanic_signup_view(request):
#     userForm=forms.MechanicUserForm()
#     mechanicForm=forms.MechanicForm()
#     mydict={'userForm':userForm,'mechanicForm':mechanicForm}
#     if request.method=='POST':
#         userForm=forms.MechanicUserForm(request.POST)
#         mechanicForm=forms.MechanicForm(request.POST,request.FILES)
#         if userForm.is_valid() and mechanicForm.is_valid():
#             user=userForm.save()
#             user.set_password(user.password)
#             user.save()
#             mechanic=mechanicForm.save(commit=False)
#             mechanic.user=user
#             mechanic.save()
#             my_mechanic_group = Group.objects.get_or_create(name='MECHANIC')
#             my_mechanic_group[0].user_set.add(user)
#         return HttpResponseRedirect('mechaniclogin')
#     return render(request,'vehicle/mechanicsignup.html',context=mydict)



def mechanic_signup_view(request):
    userForm = forms.MechanicUserForm()
    mechanicForm = forms.MechanicForm()
    mydict = {'userForm': userForm, 'mechanicForm': mechanicForm}
    
    if request.method == 'POST':
        userForm = forms.MechanicUserForm(request.POST)
        mechanicForm = forms.MechanicForm(request.POST, request.FILES)
        
        if userForm.is_valid() and mechanicForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            
            mechanic = mechanicForm.save(commit=False)
            mechanic.user = user
            mechanic.save()
            
            my_mechanic_group = Group.objects.get_or_create(name='MECHANIC')
            my_mechanic_group[0].user_set.add(user)
            
            # Send SNS notification
            send_mechanic_signup_notification(user, mechanic)
            
            return HttpResponseRedirect('mechaniclogin')
    
    return render(request, 'vehicle/mechanicsignup.html', context=mydict)


def send_mechanic_signup_notification(user, mechanic):
    try:
        import boto3
        import json
        
        # Configure SNS client
        sns_client = boto3.client(
            'sns',
            region_name='us-east-1'  
        )
        
        sns_topic_arn = 'arn:aws:sns:us-east-1:105519505372:cpp-sns-x24244228'  
        subject = 'New Mechanic Registration - Vehicle Service Management'
        
        message_body = f"""
        NEW MECHANIC REGISTRATION
        
        Details:
        --------------------------------
        Full Name: {user.first_name} {user.last_name}
        Username: {user.username}
        Email: {user.email if user.email else 'Not provided'}
        Mobile: {mechanic.mobile}
        Address: {mechanic.address}
        Skills: {mechanic.skill}
        Account Status: Pending Approval
        --------------------------------
        
        Please login to admin panel to approve this mechanic.

        """
        
        # Send SNS notification
        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=message_body,
            Subject=subject
        )
        
        print(f"SNS notification sent. Message ID: {response.get('MessageId')}")
        
    except Exception as e:
        print(f"Failed to send SNS notification: {str(e)}")



#for checking user customer, mechanic or admin(by sumit)
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()
def is_mechanic(user):
    return user.groups.filter(name='MECHANIC').exists()


def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-dashboard')
    elif is_mechanic(request.user):
        accountapproval=models.Mechanic.objects.all().filter(user_id=request.user.id,status=True)
        if accountapproval:
            return redirect('mechanic-dashboard')
        else:
            return render(request,'vehicle/mechanic_wait_for_approval.html')
    else:
        return redirect('admin-dashboard')



#============================================================================================
# ADMIN RELATED views start
#============================================================================================

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    enquiry=models.Request.objects.all().order_by('-id')
    customers=[]
    for enq in enquiry:
        customer=models.Customer.objects.get(id=enq.customer_id)
        customers.append(customer)
    dict={
    'total_customer':models.Customer.objects.all().count(),
    'total_mechanic':models.Mechanic.objects.all().count(),
    'total_request':models.Request.objects.all().count(),
    'total_feedback':models.Feedback.objects.all().count(),
    'data':zip(customers,enquiry),
    }
    return render(request,'vehicle/admin_dashboard.html',context=dict)


@login_required(login_url='adminlogin')
def admin_customer_view(request):
    return render(request,'vehicle/admin_customer.html')

@login_required(login_url='adminlogin')
def admin_view_customer_view(request):
    customers=models.Customer.objects.all()
    return render(request,'vehicle/admin_view_customer.html',{'customers':customers})


@login_required(login_url='adminlogin')
def delete_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('admin-view-customer')


@login_required(login_url='adminlogin')
def update_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,request.FILES,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('admin-view-customer')
    return render(request,'vehicle/update_customer.html',context=mydict)


@login_required(login_url='adminlogin')
def admin_add_customer_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('/admin-view-customer')
    return render(request,'vehicle/admin_add_customer.html',context=mydict)


@login_required(login_url='adminlogin')
def admin_view_customer_enquiry_view(request):
    enquiry=models.Request.objects.all().order_by('-id')
    customers=[]
    for enq in enquiry:
        customer=models.Customer.objects.get(id=enq.customer_id)
        customers.append(customer)
    return render(request,'vehicle/admin_view_customer_enquiry.html',{'data':zip(customers,enquiry)})


@login_required(login_url='adminlogin')
def admin_view_customer_invoice_view(request):
    enquiry=models.Request.objects.values('customer_id').annotate(Sum('cost'))
    print(enquiry)
    customers=[]
    for enq in enquiry:
        print(enq)
        customer=models.Customer.objects.get(id=enq['customer_id'])
        customers.append(customer)
    return render(request,'vehicle/admin_view_customer_invoice.html',{'data':zip(customers,enquiry)})

@login_required(login_url='adminlogin')
def admin_mechanic_view(request):
    return render(request,'vehicle/admin_mechanic.html')


@login_required(login_url='adminlogin')
def admin_approve_mechanic_view(request):
    mechanics=models.Mechanic.objects.all().filter(status=False)
    return render(request,'vehicle/admin_approve_mechanic.html',{'mechanics':mechanics})

@login_required(login_url='adminlogin')
def approve_mechanic_view(request,pk):
    mechanicSalary=forms.MechanicSalaryForm()
    if request.method=='POST':
        mechanicSalary=forms.MechanicSalaryForm(request.POST)
        if mechanicSalary.is_valid():
            mechanic=models.Mechanic.objects.get(id=pk)
            mechanic.salary=mechanicSalary.cleaned_data['salary']
            mechanic.status=True
            mechanic.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-approve-mechanic')
    return render(request,'vehicle/admin_approve_mechanic_details.html',{'mechanicSalary':mechanicSalary})


@login_required(login_url='adminlogin')
def delete_mechanic_view(request,pk):
    mechanic=models.Mechanic.objects.get(id=pk)
    user=models.User.objects.get(id=mechanic.user_id)
    user.delete()
    mechanic.delete()
    return redirect('admin-approve-mechanic')


@login_required(login_url='adminlogin')
def admin_add_mechanic_view(request):
    userForm=forms.MechanicUserForm()
    mechanicForm=forms.MechanicForm()
    mechanicSalary=forms.MechanicSalaryForm()
    mydict={'userForm':userForm,'mechanicForm':mechanicForm,'mechanicSalary':mechanicSalary}
    if request.method=='POST':
        userForm=forms.MechanicUserForm(request.POST)
        mechanicForm=forms.MechanicForm(request.POST,request.FILES)
        mechanicSalary=forms.MechanicSalaryForm(request.POST)
        if userForm.is_valid() and mechanicForm.is_valid() and mechanicSalary.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            mechanic=mechanicForm.save(commit=False)
            mechanic.user=user
            mechanic.status=True
            mechanic.salary=mechanicSalary.cleaned_data['salary']
            mechanic.save()
            my_mechanic_group = Group.objects.get_or_create(name='MECHANIC')
            my_mechanic_group[0].user_set.add(user)
            return HttpResponseRedirect('admin-view-mechanic')
        else:
            print('problem in form')
    return render(request,'vehicle/admin_add_mechanic.html',context=mydict)


@login_required(login_url='adminlogin')
def admin_view_mechanic_view(request):
    mechanics=models.Mechanic.objects.all()
    return render(request,'vehicle/admin_view_mechanic.html',{'mechanics':mechanics})


@login_required(login_url='adminlogin')
def delete_mechanic_view(request,pk):
    mechanic=models.Mechanic.objects.get(id=pk)
    user=models.User.objects.get(id=mechanic.user_id)
    user.delete()
    mechanic.delete()
    return redirect('admin-view-mechanic')


@login_required(login_url='adminlogin')
def update_mechanic_view(request,pk):
    mechanic=models.Mechanic.objects.get(id=pk)
    user=models.User.objects.get(id=mechanic.user_id)
    userForm=forms.MechanicUserForm(instance=user)
    mechanicForm=forms.MechanicForm(request.FILES,instance=mechanic)
    mydict={'userForm':userForm,'mechanicForm':mechanicForm}
    if request.method=='POST':
        userForm=forms.MechanicUserForm(request.POST,instance=user)
        mechanicForm=forms.MechanicForm(request.POST,request.FILES,instance=mechanic)
        if userForm.is_valid() and mechanicForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            mechanicForm.save()
            return redirect('admin-view-mechanic')
    return render(request,'vehicle/update_mechanic.html',context=mydict)

@login_required(login_url='adminlogin')
def admin_view_mechanic_salary_view(request):
    mechanics=models.Mechanic.objects.all()
    return render(request,'vehicle/admin_view_mechanic_salary.html',{'mechanics':mechanics})

@login_required(login_url='adminlogin')
def update_salary_view(request,pk):
    mechanicSalary=forms.MechanicSalaryForm()
    if request.method=='POST':
        mechanicSalary=forms.MechanicSalaryForm(request.POST)
        if mechanicSalary.is_valid():
            mechanic=models.Mechanic.objects.get(id=pk)
            mechanic.salary=mechanicSalary.cleaned_data['salary']
            mechanic.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-mechanic-salary')
    return render(request,'vehicle/admin_approve_mechanic_details.html',{'mechanicSalary':mechanicSalary})


@login_required(login_url='adminlogin')
def admin_request_view(request):
    return render(request,'vehicle/admin_request.html')

@login_required(login_url='adminlogin')
def admin_view_request_view(request):
    enquiry=models.Request.objects.all().order_by('-id')
    customers=[]
    for enq in enquiry:
        customer=models.Customer.objects.get(id=enq.customer_id)
        customers.append(customer)
    return render(request,'vehicle/admin_view_request.html',{'data':zip(customers,enquiry)})


@login_required(login_url='adminlogin')
def change_status_view(request,pk):
    adminenquiry=forms.AdminApproveRequestForm()
    if request.method=='POST':
        adminenquiry=forms.AdminApproveRequestForm(request.POST)
        if adminenquiry.is_valid():
            enquiry_x=models.Request.objects.get(id=pk)
            enquiry_x.mechanic=adminenquiry.cleaned_data['mechanic']
            enquiry_x.cost=adminenquiry.cleaned_data['cost']
            enquiry_x.status=adminenquiry.cleaned_data['status']
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-request')
    return render(request,'vehicle/admin_approve_request_details.html',{'adminenquiry':adminenquiry})


@login_required(login_url='adminlogin')
def admin_delete_request_view(request,pk):
    requests=models.Request.objects.get(id=pk)
    requests.delete()
    return redirect('admin-view-request')



@login_required(login_url='adminlogin')
def admin_add_request_view(request):
    enquiry=forms.RequestForm()
    adminenquiry=forms.AdminRequestForm()
    mydict={'enquiry':enquiry,'adminenquiry':adminenquiry}
    if request.method=='POST':
        enquiry=forms.RequestForm(request.POST)
        adminenquiry=forms.AdminRequestForm(request.POST)
        if enquiry.is_valid() and adminenquiry.is_valid():
            enquiry_x=enquiry.save(commit=False)
            enquiry_x.customer=adminenquiry.cleaned_data['customer']
            enquiry_x.mechanic=adminenquiry.cleaned_data['mechanic']
            enquiry_x.cost=adminenquiry.cleaned_data['cost']
            enquiry_x.status='Approved'
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('admin-view-request')
    return render(request,'vehicle/admin_add_request.html',context=mydict)

@login_required(login_url='adminlogin')
def admin_approve_request_view(request):
    enquiry=models.Request.objects.all().filter(status='Pending')
    return render(request,'vehicle/admin_approve_request.html',{'enquiry':enquiry})

@login_required(login_url='adminlogin')
def approve_request_view(request,pk):
    adminenquiry=forms.AdminApproveRequestForm()
    if request.method=='POST':
        adminenquiry=forms.AdminApproveRequestForm(request.POST)
        if adminenquiry.is_valid():
            enquiry_x=models.Request.objects.get(id=pk)
            enquiry_x.mechanic=adminenquiry.cleaned_data['mechanic']
            enquiry_x.cost=adminenquiry.cleaned_data['cost']
            enquiry_x.status=adminenquiry.cleaned_data['status']
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-approve-request')
    return render(request,'vehicle/admin_approve_request_details.html',{'adminenquiry':adminenquiry})




@login_required(login_url='adminlogin')
def admin_view_service_cost_view(request):
    enquiry=models.Request.objects.all().order_by('-id')
    customers=[]
    for enq in enquiry:
        customer=models.Customer.objects.get(id=enq.customer_id)
        customers.append(customer)
    print(customers)
    return render(request,'vehicle/admin_view_service_cost.html',{'data':zip(customers,enquiry)})


@login_required(login_url='adminlogin')
def update_cost_view(request,pk):
    updateCostForm=forms.UpdateCostForm()
    if request.method=='POST':
        updateCostForm=forms.UpdateCostForm(request.POST)
        if updateCostForm.is_valid():
            enquiry_x=models.Request.objects.get(id=pk)
            enquiry_x.cost=updateCostForm.cleaned_data['cost']
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/admin-view-service-cost')
    return render(request,'vehicle/update_cost.html',{'updateCostForm':updateCostForm})



@login_required(login_url='adminlogin')
def admin_mechanic_attendance_view(request):
    return render(request,'vehicle/admin_mechanic_attendance.html')


@login_required(login_url='adminlogin')
def admin_take_attendance_view(request):
    mechanics=models.Mechanic.objects.all().filter(status=True)
    aform=forms.AttendanceForm()
    if request.method=='POST':
        form=forms.AttendanceForm(request.POST)
        if form.is_valid():
            Attendances=request.POST.getlist('present_status')
            date=form.cleaned_data['date']
            for i in range(len(Attendances)):
                AttendanceModel=models.Attendance()
                
                AttendanceModel.date=date
                AttendanceModel.present_status=Attendances[i]
                print(mechanics[i].id)
                print(int(mechanics[i].id))
                mechanic=models.Mechanic.objects.get(id=int(mechanics[i].id))
                AttendanceModel.mechanic=mechanic
                AttendanceModel.save()
            return redirect('admin-view-attendance')
        else:
            print('form invalid')
    return render(request,'vehicle/admin_take_attendance.html',{'mechanics':mechanics,'aform':aform})

@login_required(login_url='adminlogin')
def admin_view_attendance_view(request):
    form=forms.AskDateForm()
    if request.method=='POST':
        form=forms.AskDateForm(request.POST)
        if form.is_valid():
            date=form.cleaned_data['date']
            attendancedata=models.Attendance.objects.all().filter(date=date)
            mechanicdata=models.Mechanic.objects.all().filter(status=True)
            mylist=zip(attendancedata,mechanicdata)
            return render(request,'vehicle/admin_view_attendance_page.html',{'mylist':mylist,'date':date})
        else:
            print('form invalid')
    return render(request,'vehicle/admin_view_attendance_ask_date.html',{'form':form})

@login_required(login_url='adminlogin')
def admin_report_view(request):
    reports=models.Request.objects.all().filter(Q(status="Repairing Done") | Q(status="Released"))
    dict={
        'reports':reports,
    }
    return render(request,'vehicle/admin_report.html',context=dict)


# @login_required(login_url='adminlogin')
# def admin_feedback_view(request):
#     feedback=models.Feedback.objects.all().order_by('-id')
#     return render(request,'vehicle/admin_feedback.html',{'feedback':feedback})





from feedback_sentiment_lib import SentimentAnalyzer

# Initialize once
sentiment_analyzer = SentimentAnalyzer()

@login_required(login_url='adminlogin')
def admin_feedback_view(request):
    # Get all feedback
    feedbacks = models.Feedback.objects.all().order_by('-id')
    
    # Bulk analyze sentiment
    feedback_with_sentiment = []
    for feedback in feedbacks:
        try:
            result = sentiment_analyzer.analyze(feedback.message)
            feedback.sentiment_label = result.sentiment.value
            feedback.sentiment_score = round(result.score, 3)
            feedback.sentiment_confidence = round(result.confidence, 3)
        except Exception:
            feedback.sentiment_label = 'error'
            feedback.sentiment_score = 0
            feedback.sentiment_confidence = 0
        
        feedback_with_sentiment.append(feedback)
    
    # Generate summary
    total = len(feedback_with_sentiment)
    counts = {
        'positive': sum(1 for f in feedback_with_sentiment if f.sentiment_label == 'positive'),
        'negative': sum(1 for f in feedback_with_sentiment if f.sentiment_label == 'negative'),
        'neutral': sum(1 for f in feedback_with_sentiment if f.sentiment_label == 'neutral'),
        'mixed': sum(1 for f in feedback_with_sentiment if f.sentiment_label == 'mixed'),
        'error': sum(1 for f in feedback_with_sentiment if f.sentiment_label == 'error'),
    }
    
    context = {
        'feedback': feedback_with_sentiment,
        'total_feedback': total,
        'sentiment_counts': counts,
    }
    
    return render(request, 'vehicle/admin_feedback.html', context)



#============================================================================================
# ADMIN RELATED views END
#============================================================================================


#============================================================================================
# CUSTOMER RELATED views start
#============================================================================================

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_dashboard_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    work_in_progress=models.Request.objects.all().filter(customer_id=customer.id,status='Repairing').count()
    work_completed=models.Request.objects.all().filter(customer_id=customer.id).filter(Q(status="Repairing Done") | Q(status="Released")).count()
    new_request_made=models.Request.objects.all().filter(customer_id=customer.id).filter(Q(status="Pending") | Q(status="Approved")).count()
    bill=models.Request.objects.all().filter(customer_id=customer.id).filter(Q(status="Repairing Done") | Q(status="Released")).aggregate(Sum('cost'))
    print(bill)
    dict={
    'work_in_progress':work_in_progress,
    'work_completed':work_completed,
    'new_request_made':new_request_made,
    'bill':bill['cost__sum'],
    'customer':customer,
    }
    return render(request,'vehicle/customer_dashboard.html',context=dict)


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_request_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    return render(request,'vehicle/customer_request.html',{'customer':customer})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_view_request_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    enquiries=models.Request.objects.all().filter(customer_id=customer.id , status="Pending")
    return render(request,'vehicle/customer_view_request.html',{'customer':customer,'enquiries':enquiries})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_delete_request_view(request,pk):
    customer=models.Customer.objects.get(user_id=request.user.id)
    enquiry=models.Request.objects.get(id=pk)
    enquiry.delete()
    return redirect('customer-view-request')

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_view_approved_request_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    enquiries=models.Request.objects.all().filter(customer_id=customer.id).exclude(status='Pending')
    return render(request,'vehicle/customer_view_approved_request.html',{'customer':customer,'enquiries':enquiries})

@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_view_approved_request_invoice_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    enquiries=models.Request.objects.all().filter(customer_id=customer.id).exclude(status='Pending')
    return render(request,'vehicle/customer_view_approved_request_invoice.html',{'customer':customer,'enquiries':enquiries})



@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_add_request_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    enquiry=forms.RequestForm()
    if request.method=='POST':
        enquiry=forms.RequestForm(request.POST)
        if enquiry.is_valid():
            customer=models.Customer.objects.get(user_id=request.user.id)
            enquiry_x=enquiry.save(commit=False)
            enquiry_x.customer=customer
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('customer-dashboard')
    return render(request,'vehicle/customer_add_request.html',{'enquiry':enquiry,'customer':customer})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_profile_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    return render(request,'vehicle/customer_profile.html',{'customer':customer})


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def edit_customer_profile_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm,'customer':customer}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return HttpResponseRedirect('customer-profile')
    return render(request,'vehicle/edit_customer_profile.html',context=mydict)



# views.py
import json
import base64
import boto3
import logging
import traceback
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from . import models

logger = logging.getLogger(__name__)

# Initialize Lambda client
lambda_client = boto3.client(
    'lambda',
    region_name='us-east-1'
)

LAMBDA_FUNCTION_NAME = 'cpp-lambda-x24244228'


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_invoice_view(request):
    customer = models.Customer.objects.get(user_id=request.user.id)
    enquiries = models.Request.objects.all().filter(
        customer_id=customer.id
    ).exclude(status='Pending')
    
    context = {
        'customer': customer,
        'enquiries': enquiries,
    }
    return render(request, 'vehicle/customer_invoice.html', context)


# @login_required(login_url='customerlogin')
# @user_passes_test(is_customer)
# def download_invoice_pdf(request, enquiry_id):
#     """
#     Generate invoice PDF using AWS Lambda - Returns PDF directly (No S3)
#     """
#     try:
#         # Get the enquiry
#         enquiry = get_object_or_404(
#             models.Request,
#             id=enquiry_id,
#             customer__user_id=request.user.id
#         )
        
#         # Validate cost
#         if not enquiry.cost or enquiry.cost == 0:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Invoice not available. Cost is not set for this service.'
#             }, status=400)
        
#         # Get customer details
#         customer = models.Customer.objects.get(user_id=request.user.id)
        
#         # Prepare invoice data for Lambda
#         invoice_data = {
#             'invoice_number': f"INV-{enquiry.id:06d}",
#             'customer_name': customer.get_name,
#             'customer_mobile': customer.mobile,
#             'customer_address': customer.address,
#             'vehicle_name': enquiry.vehicle_name,
#             'vehicle_number': str(enquiry.vehicle_no),
#             'vehicle_brand': enquiry.vehicle_brand,
#             'vehicle_model': enquiry.vehicle_model,
#             'problem_description': enquiry.problem_description,
#             'service_date': enquiry.date.strftime('%Y-%m-%d'),
#             'cost': float(enquiry.cost)
#         }
        
#         logger.info(f"Invoking Lambda for invoice: {invoice_data['invoice_number']}")
        
#         # Invoke Lambda function
#         response = lambda_client.invoke(
#             FunctionName=LAMBDA_FUNCTION_NAME,
#             InvocationType='RequestResponse',
#             Payload=json.dumps({
#                 'invoice_data': invoice_data
#             })
#         )
        
#         # Read the response payload
#         response_payload = response['Payload'].read().decode('utf-8')
#         logger.info(f"Raw Lambda response: {response_payload[:200]}...")
        
#         # Try to parse as JSON
#         try:
#             response_data = json.loads(response_payload)
#         except json.JSONDecodeError:
#             # If not JSON, it might be the PDF response
#             logger.error(f"Invalid JSON response from Lambda: {response_payload[:100]}")
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Invalid response from invoice service'
#             }, status=500)
        
#         logger.info(f"Lambda response status: {response_data.get('statusCode')}")
        
#         # Check if Lambda returned PDF
#         if response_data.get('statusCode') == 200:
#             # Check if response contains base64 encoded PDF
#             if response_data.get('isBase64Encoded') and response_data.get('body'):
#                 try:
#                     # Decode base64 PDF
#                     pdf_data = base64.b64decode(response_data['body'])
                    
#                     # Create HTTP response with PDF
#                     filename = f"invoice_{enquiry.id}.pdf"
#                     http_response = HttpResponse(pdf_data, content_type='application/pdf')
#                     http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
#                     http_response['Content-Length'] = len(pdf_data)
#                     return http_response
                    
#                 except Exception as e:
#                     logger.error(f"Error decoding PDF: {str(e)}")
#                     return JsonResponse({
#                         'success': False,
#                         'error': 'Error generating PDF'
#                     }, status=500)
            
#             # If Lambda returned JSON with error in body
#             elif response_data.get('body'):
#                 try:
#                     body = json.loads(response_data['body'])
#                     if not body.get('success', True):
#                         return JsonResponse({
#                             'success': False,
#                             'error': body.get('error', 'Unknown error from Lambda')
#                         }, status=500)
#                 except json.JSONDecodeError:
#                     # Body might be the PDF itself
#                     if response_data.get('body', '').startswith('%PDF'):
#                         # This shouldn't happen if isBase64Encoded is True
#                         return JsonResponse({
#                             'success': False,
#                             'error': 'PDF received but not encoded properly'
#                         }, status=500)
#                     else:
#                         return JsonResponse({
#                             'success': False,
#                             'error': f'Unexpected response: {response_data["body"][:100]}'
#                         }, status=500)
        
        
        
        
        
        
        
        
        
        
        
        
        
@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def download_invoice_pdf(request, enquiry_id):
    """
    Generate invoice PDF using AWS Lambda
    """
    try:
        # Get enquiry
        enquiry = get_object_or_404(
            models.Request,
            id=enquiry_id,
            customer__user_id=request.user.id
        )

        # Validate cost
        if not enquiry.cost or enquiry.cost == 0:
            return JsonResponse({
                "success": False,
                "error": "Invoice not available. Cost is not set for this service."
            }, status=400)

        # Customer
        customer = models.Customer.objects.get(user_id=request.user.id)

        # Prepare invoice data
        invoice_data = {
            "invoice_number": f"INV-{enquiry.id:06d}",
            "customer_name": customer.get_name,
            "customer_mobile": customer.mobile,
            "customer_address": customer.address,
            "vehicle_name": enquiry.vehicle_name,
            "vehicle_number": str(enquiry.vehicle_no),
            "vehicle_brand": enquiry.vehicle_brand,
            "vehicle_model": enquiry.vehicle_model,
            "problem_description": enquiry.problem_description,
            "service_date": enquiry.date.strftime("%Y-%m-%d"),
            "cost": float(enquiry.cost)
        }

        logger.info(f"Invoking Lambda for invoice {invoice_data['invoice_number']}")

        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "invoice_data": invoice_data
            })
        )

        # Read Lambda response
        payload = response["Payload"].read().decode("utf-8")
        logger.info(f"Lambda Response: {payload}")

        response_data = json.loads(payload)

        # Lambda execution failed
        if response_data.get("FunctionError"):
            logger.error(response_data)
            return JsonResponse({
                "success": False,
                "error": "Lambda execution failed."
            }, status=500)

        # Lambda returned error
        if response_data.get("statusCode") != 200:
            try:
                body = json.loads(response_data.get("body", "{}"))
                error = body.get("error", "Unknown Lambda error")
            except Exception:
                error = response_data.get("body", "Unknown Lambda error")

            return JsonResponse({
                "success": False,
                "error": error
            }, status=500)

        # Parse Lambda body
        body = json.loads(response_data["body"])

        if not body.get("success"):
            return JsonResponse({
                "success": False,
                "error": body.get("error", "Invoice generation failed")
            }, status=500)

        # Decode PDF
        pdf_bytes = base64.b64decode(body["pdf_base64"])

        filename = body.get(
            "filename",
            f"invoice_{enquiry.id}.pdf"
        )

        # Return PDF
        http_response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf"
        )

        http_response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        http_response["Content-Length"] = len(pdf_bytes)

        return http_response

    except models.Request.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Enquiry not found."
        }, status=404)

    except lambda_client.exceptions.ResourceNotFoundException:
        logger.exception("Lambda function not found")
        return JsonResponse({
            "success": False,
            "error": "Invoice service unavailable."
        }, status=503)

    except lambda_client.exceptions.ClientError as e:
        logger.exception("AWS Lambda ClientError")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=503)

    except Exception as e:
        logger.exception("Unexpected error")
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)
        
        
        
        
        
        
        
        


@login_required(login_url='customerlogin')
@user_passes_test(is_customer)
def customer_feedback_view(request):
    customer=models.Customer.objects.get(user_id=request.user.id)
    feedback=forms.FeedbackForm()
    if request.method=='POST':
        feedback=forms.FeedbackForm(request.POST)
        if feedback.is_valid():
            feedback.save()
        else:
            print("form is invalid")
        return render(request,'vehicle/feedback_sent_by_customer.html',{'customer':customer})
    return render(request,'vehicle/customer_feedback.html',{'feedback':feedback,'customer':customer})
#============================================================================================
# CUSTOMER RELATED views END
#============================================================================================






#============================================================================================
# MECHANIC RELATED views start
#============================================================================================


@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_dashboard_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    work_in_progress=models.Request.objects.all().filter(mechanic_id=mechanic.id,status='Repairing').count()
    work_completed=models.Request.objects.all().filter(mechanic_id=mechanic.id,status='Repairing Done').count()
    new_work_assigned=models.Request.objects.all().filter(mechanic_id=mechanic.id,status='Approved').count()
    dict={
    'work_in_progress':work_in_progress,
    'work_completed':work_completed,
    'new_work_assigned':new_work_assigned,
    'salary':mechanic.salary,
    'mechanic':mechanic,
    }
    return render(request,'vehicle/mechanic_dashboard.html',context=dict)

@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_work_assigned_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    works=models.Request.objects.all().filter(mechanic_id=mechanic.id)
    return render(request,'vehicle/mechanic_work_assigned.html',{'works':works,'mechanic':mechanic})


@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_update_status_view(request,pk):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    updateStatus=forms.MechanicUpdateStatusForm()
    if request.method=='POST':
        updateStatus=forms.MechanicUpdateStatusForm(request.POST)
        if updateStatus.is_valid():
            enquiry_x=models.Request.objects.get(id=pk)
            enquiry_x.status=updateStatus.cleaned_data['status']
            enquiry_x.save()
        else:
            print("form is invalid")
        return HttpResponseRedirect('/mechanic-work-assigned')
    return render(request,'vehicle/mechanic_update_status.html',{'updateStatus':updateStatus,'mechanic':mechanic})

@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_attendance_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    attendaces=models.Attendance.objects.all().filter(mechanic=mechanic)
    return render(request,'vehicle/mechanic_view_attendance.html',{'attendaces':attendaces,'mechanic':mechanic})





@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_feedback_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    feedback=forms.FeedbackForm()
    if request.method=='POST':
        feedback=forms.FeedbackForm(request.POST)
        if feedback.is_valid():
            feedback.save()
        else:
            print("form is invalid")
        return render(request,'vehicle/feedback_sent.html',{'mechanic':mechanic})
    return render(request,'vehicle/mechanic_feedback.html',{'feedback':feedback,'mechanic':mechanic})

@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_salary_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    workdone=models.Request.objects.all().filter(mechanic_id=mechanic.id).filter(Q(status="Repairing Done") | Q(status="Released"))
    return render(request,'vehicle/mechanic_salary.html',{'workdone':workdone,'mechanic':mechanic})

@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def mechanic_profile_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    return render(request,'vehicle/mechanic_profile.html',{'mechanic':mechanic})

@login_required(login_url='mechaniclogin')
@user_passes_test(is_mechanic)
def edit_mechanic_profile_view(request):
    mechanic=models.Mechanic.objects.get(user_id=request.user.id)
    user=models.User.objects.get(id=mechanic.user_id)
    userForm=forms.MechanicUserForm(instance=user)
    mechanicForm=forms.MechanicForm(request.FILES,instance=mechanic)
    mydict={'userForm':userForm,'mechanicForm':mechanicForm,'mechanic':mechanic}
    if request.method=='POST':
        userForm=forms.MechanicUserForm(request.POST,instance=user)
        mechanicForm=forms.MechanicForm(request.POST,request.FILES,instance=mechanic)
        if userForm.is_valid() and mechanicForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            mechanicForm.save()
            return redirect('mechanic-profile')
    return render(request,'vehicle/edit_mechanic_profile.html',context=mydict)






#============================================================================================
# MECHANIC RELATED views start
#============================================================================================




# for aboutus and contact
def aboutus_view(request):
    return render(request,'vehicle/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'vehicle/contactussuccess.html')
    return render(request, 'vehicle/contactus.html', {'form':sub})
