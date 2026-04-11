"""
ERP Mobile Warehouse Views
"""
from .base_crud import MobileListView, MobileDetailView
from erp.models import Warehouse


class WarehouseListView(MobileListView):
    model = Warehouse
    template_name = 'erp/mobile_app/warehouse_list.html'
    context_object_name = 'warehouses'
    search_fields = ['name', 'code']
    ordering = ['name']


class WarehouseDetailView(MobileDetailView):
    model = Warehouse
    template_name = 'erp/mobile_app/warehouse_detail.html'
    context_object_name = 'warehouse'
