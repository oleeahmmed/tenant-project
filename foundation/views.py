from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    CategoryForm,
    CurrencyForm,
    CustomerForm,
    ExchangeRateForm,
    PaymentMethodForm,
    PaymentTermForm,
    ProductForm,
    SalesPersonForm,
    SupplierForm,
    TaxRateForm,
    TaxTypeForm,
    UnitOfMeasureForm,
    UomConversionForm,
    WarehouseForm,
)
from .mixins import (
    FoundationAdminMixin,
    FoundationDashboardAccessMixin,
    FoundationPageContextMixin,
)
from .models import (
    Category,
    Currency,
    Customer,
    ExchangeRate,
    PaymentMethod,
    PaymentTerm,
    Product,
    SalesPerson,
    Supplier,
    TaxRate,
    TaxType,
    UnitOfMeasure,
    UomConversion,
    Warehouse,
)


class FoundationDashboardView(
    FoundationDashboardAccessMixin, FoundationPageContextMixin, TemplateView
):
    template_name = "foundation/dashboard.html"
    page_title = "Foundation setup"


# ── Warehouses ───────────────────────────────────────────────────────────────────


class WarehouseListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Warehouse
    template_name = "foundation/warehouse_list.html"
    context_object_name = "warehouses"
    page_title = "Warehouses"

    def get_queryset(self):
        return Warehouse.objects.filter(tenant=self.request.hrm_tenant).order_by("name")


class WarehouseCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = "foundation/warehouse_form.html"
    success_url = reverse_lazy("foundation:warehouse_list")
    page_title = "Add warehouse"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Warehouse created.")
        return redirect(self.success_url)


class WarehouseUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = "foundation/warehouse_form.html"
    context_object_name = "warehouse"
    success_url = reverse_lazy("foundation:warehouse_list")
    page_title = "Edit warehouse"

    def get_queryset(self):
        return Warehouse.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Warehouse updated.")
        return super().form_valid(form)


class WarehouseDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Warehouse
    template_name = "foundation/warehouse_confirm_delete.html"
    context_object_name = "warehouse"
    success_url = reverse_lazy("foundation:warehouse_list")
    page_title = "Delete warehouse"

    def get_queryset(self):
        return Warehouse.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = f"{self.object.code} — {self.object.name}"
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Warehouse “{label}” deleted.")
        return response


# ── Categories ───────────────────────────────────────────────────────────────────


class CategoryListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Category
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Categories"

    def get_queryset(self):
        return Category.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Categories",
                "create_url_name": "foundation:category_create",
                "edit_url_name": "foundation:category_edit",
                "delete_url_name": "foundation:category_delete",
                "list_url_name": "foundation:category_list",
            }
        )
        return ctx


class CategoryCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:category_list")
    page_title = "Add category"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:category_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Category created.")
        return redirect(self.success_url)


class CategoryUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:category_list")
    page_title = "Edit category"

    def get_queryset(self):
        return Category.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:category_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Category updated.")
        return super().form_valid(form)


class CategoryDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Category
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:category_list")
    page_title = "Delete category"

    def get_queryset(self):
        return Category.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:category_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Products ─────────────────────────────────────────────────────────────────────


class ProductListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Product
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Products"

    def get_queryset(self):
        return Product.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Products",
                "create_url_name": "foundation:product_create",
                "detail_url_name": "foundation:product_detail",
                "edit_url_name": "foundation:product_edit",
                "delete_url_name": "foundation:product_delete",
                "list_url_name": "foundation:product_list",
            }
        )
        return ctx


class ProductDetailView(FoundationAdminMixin, FoundationPageContextMixin, DetailView):
    model = Product
    template_name = "foundation/product_detail.html"
    context_object_name = "product"
    page_title = "Product details"

    def get_queryset(self):
        return (
            Product.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("category", "default_uom")
        )

    def get_context_data(self, **kwargs):
        from inventory.models import StockTransaction, WarehouseStock

        ctx = super().get_context_data(**kwargs)
        product = self.object
        tenant = self.request.hrm_tenant
        stocks = (
            WarehouseStock.objects.filter(tenant=tenant, product=product)
            .select_related("warehouse")
            .order_by("warehouse__code")
        )
        total_qty = sum((row.quantity for row in stocks), 0)
        ctx["warehouse_stocks"] = stocks
        ctx["total_stock"] = total_qty
        ctx["recent_transactions"] = (
            StockTransaction.objects.filter(tenant=tenant, product=product)
            .select_related("warehouse")
            .order_by("-created_at")[:10]
        )
        return ctx


class ProductCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:product_list")
    page_title = "Add product"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:product_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Product created.")
        return redirect(self.success_url)


class ProductUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:product_list")
    page_title = "Edit product"

    def get_queryset(self):
        return Product.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:product_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Product updated.")
        return super().form_valid(form)


class ProductDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Product
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:product_list")
    page_title = "Delete product"

    def get_queryset(self):
        return Product.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:product_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Units of measure ─────────────────────────────────────────────────────────────


class UomListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = UnitOfMeasure
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Units of measure"

    def get_queryset(self):
        return UnitOfMeasure.objects.filter(tenant=self.request.hrm_tenant).order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Units of measure",
                "create_url_name": "foundation:uom_create",
                "edit_url_name": "foundation:uom_edit",
                "delete_url_name": "foundation:uom_delete",
                "list_url_name": "foundation:uom_list",
            }
        )
        return ctx


class UomCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:uom_list")
    page_title = "Add unit of measure"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:uom_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Unit of measure created.")
        return redirect(self.success_url)


class UomUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = UnitOfMeasure
    form_class = UnitOfMeasureForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:uom_list")
    page_title = "Edit unit of measure"

    def get_queryset(self):
        return UnitOfMeasure.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:uom_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Unit of measure updated.")
        return super().form_valid(form)


class UomDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = UnitOfMeasure
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:uom_list")
    page_title = "Delete unit of measure"

    def get_queryset(self):
        return UnitOfMeasure.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:uom_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── UOM conversions ──────────────────────────────────────────────────────────────


class UomConversionListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = UomConversion
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "UOM conversions"

    def get_queryset(self):
        return UomConversion.objects.filter(tenant=self.request.hrm_tenant).order_by(
            "from_uom__code", "to_uom__code"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "UOM conversions",
                "create_url_name": "foundation:uom_conversion_create",
                "edit_url_name": "foundation:uom_conversion_edit",
                "delete_url_name": "foundation:uom_conversion_delete",
                "list_url_name": "foundation:uom_conversion_list",
            }
        )
        return ctx


class UomConversionCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = UomConversion
    form_class = UomConversionForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:uom_conversion_list")
    page_title = "Add UOM conversion"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:uom_conversion_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "UOM conversion created.")
        return redirect(self.success_url)


class UomConversionUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = UomConversion
    form_class = UomConversionForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:uom_conversion_list")
    page_title = "Edit UOM conversion"

    def get_queryset(self):
        return UomConversion.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:uom_conversion_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "UOM conversion updated.")
        return super().form_valid(form)


class UomConversionDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = UomConversion
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:uom_conversion_list")
    page_title = "Delete UOM conversion"

    def get_queryset(self):
        return UomConversion.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:uom_conversion_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Customers ──────────────────────────────────────────────────────────────────────


class CustomerListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Customer
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Customers"

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Customers",
                "create_url_name": "foundation:customer_create",
                "edit_url_name": "foundation:customer_edit",
                "delete_url_name": "foundation:customer_delete",
                "list_url_name": "foundation:customer_list",
            }
        )
        return ctx


class CustomerCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:customer_list")
    page_title = "Add customer"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:customer_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Customer created.")
        return redirect(self.success_url)


class CustomerUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:customer_list")
    page_title = "Edit customer"

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:customer_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Customer updated.")
        return super().form_valid(form)


class CustomerDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Customer
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:customer_list")
    page_title = "Delete customer"

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:customer_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Suppliers ────────────────────────────────────────────────────────────────────


class SupplierListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Supplier
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Suppliers"

    def get_queryset(self):
        return Supplier.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Suppliers",
                "create_url_name": "foundation:supplier_create",
                "edit_url_name": "foundation:supplier_edit",
                "delete_url_name": "foundation:supplier_delete",
                "list_url_name": "foundation:supplier_list",
            }
        )
        return ctx


class SupplierCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:supplier_list")
    page_title = "Add supplier"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:supplier_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Supplier created.")
        return redirect(self.success_url)


class SupplierUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:supplier_list")
    page_title = "Edit supplier"

    def get_queryset(self):
        return Supplier.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:supplier_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Supplier updated.")
        return super().form_valid(form)


class SupplierDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Supplier
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:supplier_list")
    page_title = "Delete supplier"

    def get_queryset(self):
        return Supplier.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:supplier_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Sales persons ────────────────────────────────────────────────────────────────


class SalesPersonListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = SalesPerson
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Sales persons"

    def get_queryset(self):
        return SalesPerson.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Sales persons",
                "create_url_name": "foundation:sales_person_create",
                "edit_url_name": "foundation:sales_person_edit",
                "delete_url_name": "foundation:sales_person_delete",
                "list_url_name": "foundation:sales_person_list",
            }
        )
        return ctx


class SalesPersonCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = SalesPerson
    form_class = SalesPersonForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:sales_person_list")
    page_title = "Add sales person"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:sales_person_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Sales person created.")
        return redirect(self.success_url)


class SalesPersonUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = SalesPerson
    form_class = SalesPersonForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:sales_person_list")
    page_title = "Edit sales person"

    def get_queryset(self):
        return SalesPerson.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:sales_person_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Sales person updated.")
        return super().form_valid(form)


class SalesPersonDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = SalesPerson
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:sales_person_list")
    page_title = "Delete sales person"

    def get_queryset(self):
        return SalesPerson.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:sales_person_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Payment methods ────────────────────────────────────────────────────────────


class PaymentMethodListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = PaymentMethod
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Payment methods"

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Payment methods",
                "create_url_name": "foundation:payment_method_create",
                "edit_url_name": "foundation:payment_method_edit",
                "delete_url_name": "foundation:payment_method_delete",
                "list_url_name": "foundation:payment_method_list",
            }
        )
        return ctx


class PaymentMethodCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:payment_method_list")
    page_title = "Add payment method"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:payment_method_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Payment method created.")
        return redirect(self.success_url)


class PaymentMethodUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:payment_method_list")
    page_title = "Edit payment method"

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:payment_method_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Payment method updated.")
        return super().form_valid(form)


class PaymentMethodDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = PaymentMethod
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:payment_method_list")
    page_title = "Delete payment method"

    def get_queryset(self):
        return PaymentMethod.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:payment_method_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Currencies ───────────────────────────────────────────────────────────────────


class CurrencyListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = Currency
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Currencies"

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.hrm_tenant).order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Currencies",
                "create_url_name": "foundation:currency_create",
                "edit_url_name": "foundation:currency_edit",
                "delete_url_name": "foundation:currency_delete",
                "list_url_name": "foundation:currency_list",
            }
        )
        return ctx


class CurrencyCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:currency_list")
    page_title = "Add currency"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:currency_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Currency created.")
        return redirect(self.success_url)


class CurrencyUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:currency_list")
    page_title = "Edit currency"

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:currency_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Currency updated.")
        return super().form_valid(form)


class CurrencyDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = Currency
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:currency_list")
    page_title = "Delete currency"

    def get_queryset(self):
        return Currency.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:currency_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Exchange rates ─────────────────────────────────────────────────────────────────


class ExchangeRateListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = ExchangeRate
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Exchange rates"

    def get_queryset(self):
        return ExchangeRate.objects.filter(tenant=self.request.hrm_tenant).order_by(
            "-effective_date", "from_currency__code"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Exchange rates",
                "create_url_name": "foundation:exchange_rate_create",
                "edit_url_name": "foundation:exchange_rate_edit",
                "delete_url_name": "foundation:exchange_rate_delete",
                "list_url_name": "foundation:exchange_rate_list",
            }
        )
        return ctx


class ExchangeRateCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:exchange_rate_list")
    page_title = "Add exchange rate"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:exchange_rate_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Exchange rate created.")
        return redirect(self.success_url)


class ExchangeRateUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:exchange_rate_list")
    page_title = "Edit exchange rate"

    def get_queryset(self):
        return ExchangeRate.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:exchange_rate_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Exchange rate updated.")
        return super().form_valid(form)


class ExchangeRateDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = ExchangeRate
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:exchange_rate_list")
    page_title = "Delete exchange rate"

    def get_queryset(self):
        return ExchangeRate.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:exchange_rate_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Tax types ────────────────────────────────────────────────────────────────────


class TaxTypeListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = TaxType
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Tax types"

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.hrm_tenant).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Tax types",
                "create_url_name": "foundation:tax_type_create",
                "edit_url_name": "foundation:tax_type_edit",
                "delete_url_name": "foundation:tax_type_delete",
                "list_url_name": "foundation:tax_type_list",
            }
        )
        return ctx


class TaxTypeCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:tax_type_list")
    page_title = "Add tax type"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:tax_type_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Tax type created.")
        return redirect(self.success_url)


class TaxTypeUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = TaxType
    form_class = TaxTypeForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:tax_type_list")
    page_title = "Edit tax type"

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:tax_type_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Tax type updated.")
        return super().form_valid(form)


class TaxTypeDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = TaxType
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:tax_type_list")
    page_title = "Delete tax type"

    def get_queryset(self):
        return TaxType.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:tax_type_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Tax rates ────────────────────────────────────────────────────────────────────


class TaxRateListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = TaxRate
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Tax rates"

    def get_queryset(self):
        return TaxRate.objects.filter(tenant=self.request.hrm_tenant).order_by(
            "-effective_from", "tax_type__code"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Tax rates",
                "create_url_name": "foundation:tax_rate_create",
                "edit_url_name": "foundation:tax_rate_edit",
                "delete_url_name": "foundation:tax_rate_delete",
                "list_url_name": "foundation:tax_rate_list",
            }
        )
        return ctx


class TaxRateCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:tax_rate_list")
    page_title = "Add tax rate"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:tax_rate_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Tax rate created.")
        return redirect(self.success_url)


class TaxRateUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = TaxRate
    form_class = TaxRateForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:tax_rate_list")
    page_title = "Edit tax rate"

    def get_queryset(self):
        return TaxRate.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:tax_rate_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Tax rate updated.")
        return super().form_valid(form)


class TaxRateDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = TaxRate
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:tax_rate_list")
    page_title = "Delete tax rate"

    def get_queryset(self):
        return TaxRate.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:tax_rate_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response


# ── Payment terms ────────────────────────────────────────────────────────────────


class PaymentTermListView(FoundationAdminMixin, FoundationPageContextMixin, ListView):
    model = PaymentTerm
    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    page_title = "Payment terms"

    def get_queryset(self):
        return PaymentTerm.objects.filter(tenant=self.request.hrm_tenant).order_by("code")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "entity_title": "Payment terms",
                "create_url_name": "foundation:payment_term_create",
                "edit_url_name": "foundation:payment_term_edit",
                "delete_url_name": "foundation:payment_term_delete",
                "list_url_name": "foundation:payment_term_list",
            }
        )
        return ctx


class PaymentTermCreateView(FoundationAdminMixin, FoundationPageContextMixin, CreateView):
    model = PaymentTerm
    form_class = PaymentTermForm
    template_name = "foundation/entity_form.html"
    success_url = reverse_lazy("foundation:payment_term_list")
    page_title = "Add payment term"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = False
        ctx["list_url_name"] = "foundation:payment_term_list"
        return ctx

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Payment term created.")
        return redirect(self.success_url)


class PaymentTermUpdateView(FoundationAdminMixin, FoundationPageContextMixin, UpdateView):
    model = PaymentTerm
    form_class = PaymentTermForm
    template_name = "foundation/entity_form.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:payment_term_list")
    page_title = "Edit payment term"

    def get_queryset(self):
        return PaymentTerm.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["list_url_name"] = "foundation:payment_term_list"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Payment term updated.")
        return super().form_valid(form)


class PaymentTermDeleteView(FoundationAdminMixin, FoundationPageContextMixin, DeleteView):
    model = PaymentTerm
    template_name = "foundation/entity_confirm_delete.html"
    context_object_name = "object"
    success_url = reverse_lazy("foundation:payment_term_list")
    page_title = "Delete payment term"

    def get_queryset(self):
        return PaymentTerm.objects.filter(tenant=self.request.hrm_tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["list_url_name"] = "foundation:payment_term_list"
        return ctx

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        label = str(self.object)
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f"Deleted: {label}")
        return response
