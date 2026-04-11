"""
Generic CRUD Base Views for ERP Mobile
"""
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q


class MobileListView(LoginRequiredMixin, View):
    """Generic List View"""
    model = None
    template_name = None
    context_object_name = 'objects'
    paginate_by = 20
    search_fields = []
    ordering = ['-created_at']
    login_url = 'erp:erp-mobile-login'
    
    def get_queryset(self):
        queryset = self.model.objects.all()
        
        # Search
        search = self.request.GET.get('search', '').strip()
        if search and self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f'{field}__icontains': search})
            queryset = queryset.filter(q_objects)
        
        # Ordering
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        
        return queryset
    
    def get(self, request):
        queryset = self.get_queryset()
        context = {
            self.context_object_name: queryset[:self.paginate_by],
            'search_query': request.GET.get('search', ''),
        }
        return render(request, self.template_name, context)


class MobileDetailView(LoginRequiredMixin, View):
    """Generic Detail View"""
    model = None
    template_name = None
    context_object_name = 'object'
    login_url = 'erp:erp-mobile-login'
    
    def get(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        context = {
            self.context_object_name: obj,
        }
        return render(request, self.template_name, context)


class MobileCreateView(LoginRequiredMixin, View):
    """Generic Create View"""
    model = None
    template_name = None
    success_url = None
    login_url = 'erp:erp-mobile-login'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        # Override in subclass
        pass


class MobileUpdateView(LoginRequiredMixin, View):
    """Generic Update View"""
    model = None
    template_name = None
    success_url = None
    login_url = 'erp:erp-mobile-login'
    
    def get(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        context = {'object': obj}
        return render(request, self.template_name, context)
    
    def post(self, request, pk):
        # Override in subclass
        pass


class MobileDeleteView(LoginRequiredMixin, View):
    """Generic Delete View"""
    model = None
    success_url = None
    login_url = 'erp:erp-mobile-login'
    
    def post(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.delete()
        return JsonResponse({'success': True, 'message': 'Deleted successfully'})
