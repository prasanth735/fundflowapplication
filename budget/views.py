from django.shortcuts import render,redirect
from django.views.generic import View
from django import forms
from budget.models import Transaction
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.utils import timezone
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.decorators.cache import never_cache

# decarator
def signinrequired(fn):

    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated:
            messages.error(request,"invalid session")
            return redirect("signin")
        else:
            return fn(request,*args,**kwargs)
    return wrapper

decs=[signinrequired,never_cache]
# view for listing all transactions
# localhost:8000/transaction/all/
# method get
@method_decorator(decs,name="dispatch")
class Transactionlistview(View):
   def get(self,request,*args,**kwargs):
        qs=Transaction.objects.filter(user_objects=request.user)
        cu_month=timezone.now().month
        cu_year=timezone.now().year
        # print(cu_month,cu_year)
        # expenses_total=Transaction.objects.filter(
        #     user_objects=request.user,
        #     type="expense",
        #     created_date__month=cu_month,
        #     created_date__year=cu_year
        # ).aggregate(Sum("amount"))
        # print(expenses_total)

        # income_total=Transaction.objects.filter(
        #     user_objects=request.user,
        #     type="income",
        #     created_date__month=cu_month,
        #     created_date__year=cu_year
        # ).aggregate(Sum("amount"))
        # print(income_total)

        data=Transaction.objects.filter(
            created_date__month=cu_month,
            created_date__year=cu_year,
            user_objects=request.user
        ).values("type").annotate(type_sum=Sum("amount"))
        # print(data)
        cat_qs=Transaction.objects.filter(
            created_date__month=cu_month,
            created_date__year=cu_year,
            user_objects=request.user
        ).values("category").annotate(cat_sum=Sum("amount"))


        return render(request,"transaction_list.html",{"data":qs,"type_total":data,"cat_total":cat_qs})
    

class Transactionform(forms.ModelForm):

    class Meta:
        model=Transaction
        # fields"__all__"
        # fields=["field1","field2"]
        exclude=("created_data","user_objects")
        widgets={
            "title":forms.TextInput(attrs={"class":"form-control"}),
            "amount":forms.NumberInput(attrs={"class":"form-control"}),
            "type":forms.Select(attrs={"class":"form-control form-select"}),
            "category":forms.Select(attrs={"class":"form-control form-select"})

        }


class RegistrationForm(forms.ModelForm):
    class Meta:
        model=User
        fields=["username","email","password"]
        widgets={
            "username":forms.TextInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control"}),
            "password":forms.PasswordInput(attrs={"class":"form-control"})
        }


class LoginForm(forms.Form):
    username=forms.CharField(widget=forms.TextInput(attrs={"class":"form-control"}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control"}))


#  view  for create new transaction
#  localhost:8000/transaction/add/
# method get,post
@method_decorator(decs,name="dispatch")
class Transactioncreateview(View):
    def get(self,request,*args,**kwargs):
        form=Transactionform()
        return render (request,"transaction_add.html",{"form":form})
    
    def post(self,request,*args,**kwargs):
        form=Transactionform(request.POST)

        if form.is_valid():
            data=form.cleaned_data
            Transaction.objects.create(**data,user_objects=request.user)
            messages.success(request,"transaction added")
            # form.instance.user_objects=request.user
            # form.save()
            return redirect("transaction-list")
        else:
            messages.error(request,"transaction adding failed")
            return render (request,"transaction_add.html",{"form":form})
        

# transaction deatil
# localhost:8000/transaction/1/detaildecs
@method_decorator(decs,name="dispatch")
class Transactiondetailview(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        data=Transaction.objects.get(id=id)
        return render(request,"transaction_detail.html",{"data":data})
    

# transaction deleteview
# localhost:8000/transaction/id/delete/
# method get   
@method_decorator(decs,name="dispatch")
class Transactiondeleteview(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        data=Transaction.objects.filter(id=id).delete()
        messages.success(request,"transaction has been removed")
        return redirect("transaction-list")


# transaction updateview
# localhost:8000/transaction/id/update/
# method get  
@method_decorator(decs,name="dispatch") 
class Transactionupdateview(View):
    def  get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_objects=Transaction.objects.get(id=id)
        form=Transactionform(instance=transaction_objects)
        return render(request,"transaction_edit.html",{"form":form})
    

    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        transaction_objects=Transaction.objects.get(id=id)
        form=Transactionform(request.POST,instance=transaction_objects)
        if form.is_valid():
            form.save()
            messages.success(request,"transaction has been updated successfully")
            return redirect("transaction-list")
        else:
            messages.error(request,"transaction updation failed")
            return render(request,"transaction_edit.html",{"form":form})


# signup
# localhost:8000/signup/
# method get post
class SignupView(View):
    def get(self,request,*args,**kwargs):
        form=RegistrationForm()
        return render(request,"register.html",{"form":form})
    

    def post(self,request,*args,**kwargs): 
        form=RegistrationForm(request.POST)
        if form.is_valid():
            User.objects.create_user(**form.cleaned_data)
            print("registered")
            return redirect("signin")
        else:
            print("faild")
            return render(request,"register.html",{"form":form})

    
# signin
# localhost:8000/signin/
class SigninView(View):
    def get(self,request,*args,**kwargs):
        form=LoginForm()
        return render(request,"signin.html",{"form":form})
    

    def post(self,request,*args,**kwargs):

        form=LoginForm(request.POST)
        if form.is_valid():
            u_name=form.cleaned_data.get("username")
            pwd=form.cleaned_data.get("password")
            user_object=authenticate(request,username=u_name,password=pwd)
            if user_object:
                login(request,user_object)
                return redirect("transaction-list")
        print("invalid")
        return render(request,"signin.html",{"form":form})


# signout
@method_decorator(decs,name="dispatch")
class SignoutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("signin")

