from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .forms import CustomUserCreationForm

# Create your views here.
def home(request):
    return render(request, "home.html", {})

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            messages.success(request, ("You Have Been Logged in."))
            print("You Have Been Logged in.")
            return redirect('leafletmap')
        else:
            messages.success(request, ("Error Logging In - Please Try Again..."))
            print("Error Logging In - Please Try Again...")
            return redirect('login')

    else:
        return render(request, "login.html", {})
    
def logout_user(request):
    logout(request)
    messages.success(request, ("You Have Been Logged Out."))
    return redirect('leafletmap')

def register_user(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, ("You Have Created An Account."))
                return redirect('leafletmap')
            else:
                messages.error(request, "Authentication Failed.")
                print("Authentication Failed.")
        else:
            messages.error(request, "Form Invalid - Please Try Again.")
            print("Form Invalid - Please Try Again.")
            print(form.errors)
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {'form': form})

def collections(request):
    return render(request, "collections.html", {})