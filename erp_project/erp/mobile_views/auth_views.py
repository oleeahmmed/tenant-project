"""
ERP Mobile Authentication Views
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin


class ERPMobileLoginView(View):
    """ERP Mobile Login"""
    template_name = 'erp/mobile_app/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('erp:erp-mobile-dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            return render(request, self.template_name, {
                'error': 'Please enter both username and password'
            })
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_active:
            login(request, user)
            return redirect('erp:erp-mobile-dashboard')
        else:
            return render(request, self.template_name, {
                'error': 'Invalid credentials'
            })


class ERPMobileLogoutView(View):
    """ERP Mobile Logout"""
    
    def get(self, request):
        logout(request)
        return redirect('erp:erp-mobile-login')
