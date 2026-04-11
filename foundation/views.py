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
    FoundationMasterListMixin,
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


class FoundationEntityListView(
    FoundationAdminMixin,
    FoundationPageContextMixin,
    FoundationMasterListMixin,
    ListView,
):
    """Inventory-style list: filters, search, pagination, row ⋮ menu, print."""

    template_name = "foundation/entity_list.html"
    context_object_name = "object_list"
    entity_subtitle = "Search, filter, and manage master data"
    column_specs = []
    search_fields = []
    sort_allowlist = []
    default_sort = "name"
    sort_choices = []
    has_is_active = True
    detail_url_name = None
    create_url_name = ""
    list_url_name = ""
    edit_url_name = ""
    delete_url_name = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["entity_title"] = getattr(self, "entity_title", self.page_title)
        ctx["entity_subtitle"] = getattr(self, "entity_subtitle", "Search, filter, and manage master data")
        ctx["create_url_name"] = self.create_url_name
        ctx["list_url_name"] = self.list_url_name
        ctx["edit_url_name"] = self.edit_url_name
        ctx["delete_url_name"] = self.delete_url_name
        ctx["column_specs"] = self.column_specs
        ctx["has_is_active"] = getattr(self, "has_is_active", True)
        ctx["new_button_label"] = getattr(self, "new_button_label", "Add")
        if getattr(self, "detail_url_name", None):
            ctx["detail_url_name"] = self.detail_url_name
        return ctx


class FoundationDashboardView(
    FoundationDashboardAccessMixin, FoundationPageContextMixin, TemplateView
):
    template_name = "foundation/dashboard.html"
    page_title = "Foundation setup"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        tenant = getattr(request, "hrm_tenant", None)
        if (
            tenant is not None
            and getattr(request.user, "role", None) in ("staff", "tenant_admin")
            and not request.user.has_tenant_permission("foundation.view")
        ):
            messages.error(request, "You do not have permission for this Foundation action.")
            return redirect("dashboard")
        return response


# ── Warehouses ───────────────────────────────────────────────────────────────────


class WarehouseListView(FoundationEntityListView):
    model = Warehouse
    page_title = "Warehouses"
    entity_title = "Warehouses"
    entity_subtitle = "Storage and fulfillment locations for inventory"
    create_url_name = "foundation:warehouse_create"
    list_url_name = "foundation:warehouse_list"
    edit_url_name = "foundation:warehouse_edit"
    delete_url_name = "foundation:warehouse_delete"
    new_button_label = "Add warehouse"
    search_fields = ["code", "name", "city", "country"]
    sort_allowlist = ["name", "-name", "code", "-code", "city", "-city"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "city", "label": "City"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Warehouse.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class CategoryListView(FoundationEntityListView):
    model = Category
    page_title = "Categories"
    entity_title = "Categories"
    create_url_name = "foundation:category_create"
    list_url_name = "foundation:category_list"
    edit_url_name = "foundation:category_edit"
    delete_url_name = "foundation:category_delete"
    new_button_label = "Add category"
    search_fields = ["name", "code", "description"]
    sort_allowlist = ["name", "-name", "code", "-code"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "parent", "label": "Parent"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Category.objects.filter(tenant=self.request.hrm_tenant).select_related("parent")
        return self.apply_master_filters(qs)


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


class ProductListView(FoundationEntityListView):
    model = Product
    page_title = "Products"
    entity_title = "Products"
    create_url_name = "foundation:product_create"
    detail_url_name = "foundation:product_detail"
    list_url_name = "foundation:product_list"
    edit_url_name = "foundation:product_edit"
    delete_url_name = "foundation:product_delete"
    new_button_label = "Add product"
    search_fields = ["sku", "name", "description", "category__name"]
    sort_allowlist = ["name", "-name", "sku", "-sku", "list_price", "-list_price"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("sku", "SKU A–Z"),
        ("-sku", "SKU Z–A"),
        ("list_price", "List price ↑"),
        ("-list_price", "List price ↓"),
    ]
    column_specs = [
        {"field": "sku", "label": "SKU", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "category", "label": "Category"},
        {"field": "list_price", "label": "List price", "money": True},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Product.objects.filter(tenant=self.request.hrm_tenant).select_related("category", "default_uom")
        return self.apply_master_filters(qs)


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


class UomListView(FoundationEntityListView):
    model = UnitOfMeasure
    page_title = "Units of measure"
    entity_title = "Units of measure"
    create_url_name = "foundation:uom_create"
    list_url_name = "foundation:uom_list"
    edit_url_name = "foundation:uom_edit"
    delete_url_name = "foundation:uom_delete"
    new_button_label = "Add UOM"
    search_fields = ["code", "name"]
    sort_allowlist = ["code", "-code", "name", "-name"]
    default_sort = "code"
    sort_choices = [
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "decimal_places", "label": "Decimals"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = UnitOfMeasure.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class UomConversionListView(FoundationEntityListView):
    model = UomConversion
    page_title = "UOM conversions"
    entity_title = "UOM conversions"
    create_url_name = "foundation:uom_conversion_create"
    list_url_name = "foundation:uom_conversion_list"
    edit_url_name = "foundation:uom_conversion_edit"
    delete_url_name = "foundation:uom_conversion_delete"
    new_button_label = "Add conversion"
    has_is_active = False
    search_fields = ["from_uom__code", "from_uom__name", "to_uom__code", "to_uom__name"]
    sort_allowlist = [
        "from_uom__code",
        "-from_uom__code",
        "to_uom__code",
        "-to_uom__code",
        "factor",
        "-factor",
    ]
    default_sort = "from_uom__code"
    sort_choices = [
        ("from_uom__code", "From UOM A–Z"),
        ("-from_uom__code", "From UOM Z–A"),
        ("to_uom__code", "To UOM A–Z"),
        ("factor", "Factor ↑"),
        ("-factor", "Factor ↓"),
    ]
    column_specs = [
        {"field": "from_uom", "label": "From"},
        {"field": "to_uom", "label": "To"},
        {"field": "factor", "label": "Factor", "money": True},
    ]

    def get_queryset(self):
        qs = UomConversion.objects.filter(tenant=self.request.hrm_tenant).select_related("from_uom", "to_uom")
        return self.apply_master_filters(qs)


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


class CustomerListView(FoundationEntityListView):
    model = Customer
    page_title = "Customers"
    entity_title = "Customers"
    create_url_name = "foundation:customer_create"
    list_url_name = "foundation:customer_list"
    edit_url_name = "foundation:customer_edit"
    delete_url_name = "foundation:customer_delete"
    new_button_label = "Add customer"
    search_fields = ["customer_code", "name", "email", "phone", "city"]
    sort_allowlist = ["name", "-name", "customer_code", "-customer_code", "city", "-city"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("customer_code", "Code A–Z"),
        ("-customer_code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "customer_code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "city", "label": "City"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Customer.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class SupplierListView(FoundationEntityListView):
    model = Supplier
    page_title = "Suppliers"
    entity_title = "Suppliers"
    create_url_name = "foundation:supplier_create"
    list_url_name = "foundation:supplier_list"
    edit_url_name = "foundation:supplier_edit"
    delete_url_name = "foundation:supplier_delete"
    new_button_label = "Add supplier"
    search_fields = ["supplier_code", "name", "email", "phone", "city"]
    sort_allowlist = ["name", "-name", "supplier_code", "-supplier_code", "city", "-city"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("supplier_code", "Code A–Z"),
        ("-supplier_code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "supplier_code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "city", "label": "City"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Supplier.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class SalesPersonListView(FoundationEntityListView):
    model = SalesPerson
    page_title = "Sales persons"
    entity_title = "Sales persons"
    create_url_name = "foundation:sales_person_create"
    list_url_name = "foundation:sales_person_list"
    edit_url_name = "foundation:sales_person_edit"
    delete_url_name = "foundation:sales_person_delete"
    new_button_label = "Add sales person"
    search_fields = ["code", "name", "email", "phone"]
    sort_allowlist = ["name", "-name", "code", "-code"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "email", "label": "Email"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = SalesPerson.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class PaymentMethodListView(FoundationEntityListView):
    model = PaymentMethod
    page_title = "Payment methods"
    entity_title = "Payment methods"
    create_url_name = "foundation:payment_method_create"
    list_url_name = "foundation:payment_method_list"
    edit_url_name = "foundation:payment_method_edit"
    delete_url_name = "foundation:payment_method_delete"
    new_button_label = "Add method"
    search_fields = ["code", "name"]
    sort_allowlist = ["name", "-name", "code", "-code"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = PaymentMethod.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class CurrencyListView(FoundationEntityListView):
    model = Currency
    page_title = "Currencies"
    entity_title = "Currencies"
    create_url_name = "foundation:currency_create"
    list_url_name = "foundation:currency_list"
    edit_url_name = "foundation:currency_edit"
    delete_url_name = "foundation:currency_delete"
    new_button_label = "Add currency"
    search_fields = ["code", "name", "symbol"]
    sort_allowlist = ["code", "-code", "name", "-name"]
    default_sort = "code"
    sort_choices = [
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "symbol", "label": "Symbol"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = Currency.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class ExchangeRateListView(FoundationEntityListView):
    model = ExchangeRate
    page_title = "Exchange rates"
    entity_title = "Exchange rates"
    create_url_name = "foundation:exchange_rate_create"
    list_url_name = "foundation:exchange_rate_list"
    edit_url_name = "foundation:exchange_rate_edit"
    delete_url_name = "foundation:exchange_rate_delete"
    new_button_label = "Add rate"
    has_is_active = False
    search_fields = ["from_currency__code", "to_currency__code", "from_currency__name", "to_currency__name"]
    sort_allowlist = [
        "-effective_date",
        "effective_date",
        "from_currency__code",
        "-from_currency__code",
        "rate",
        "-rate",
    ]
    default_sort = "-effective_date"
    sort_choices = [
        ("-effective_date", "Newest effective date"),
        ("effective_date", "Oldest effective date"),
        ("from_currency__code", "From currency A–Z"),
        ("rate", "Rate ↑"),
        ("-rate", "Rate ↓"),
    ]
    column_specs = [
        {"field": "from_currency", "label": "From"},
        {"field": "to_currency", "label": "To"},
        {"field": "rate", "label": "Rate", "money": True},
        {"field": "effective_date", "label": "Effective"},
    ]

    def get_queryset(self):
        qs = ExchangeRate.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "from_currency", "to_currency"
        )
        return self.apply_master_filters(qs)


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


class TaxTypeListView(FoundationEntityListView):
    model = TaxType
    page_title = "Tax types"
    entity_title = "Tax types"
    create_url_name = "foundation:tax_type_create"
    list_url_name = "foundation:tax_type_list"
    edit_url_name = "foundation:tax_type_edit"
    delete_url_name = "foundation:tax_type_delete"
    new_button_label = "Add tax type"
    search_fields = ["code", "name", "description"]
    sort_allowlist = ["name", "-name", "code", "-code"]
    default_sort = "name"
    sort_choices = [
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = TaxType.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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


class TaxRateListView(FoundationEntityListView):
    model = TaxRate
    page_title = "Tax rates"
    entity_title = "Tax rates"
    create_url_name = "foundation:tax_rate_create"
    list_url_name = "foundation:tax_rate_list"
    edit_url_name = "foundation:tax_rate_edit"
    delete_url_name = "foundation:tax_rate_delete"
    new_button_label = "Add tax rate"
    has_is_active = False
    search_fields = ["tax_type__code", "tax_type__name"]
    sort_allowlist = ["-effective_from", "effective_from", "tax_type__code", "rate_percent", "-rate_percent"]
    default_sort = "-effective_from"
    sort_choices = [
        ("-effective_from", "Newest effective from"),
        ("effective_from", "Oldest effective from"),
        ("tax_type__code", "Tax type A–Z"),
        ("rate_percent", "Rate % ↑"),
        ("-rate_percent", "Rate % ↓"),
    ]
    column_specs = [
        {"field": "tax_type", "label": "Tax type"},
        {"field": "rate_percent", "label": "Rate %"},
        {"field": "effective_from", "label": "Effective from"},
    ]

    def get_queryset(self):
        qs = TaxRate.objects.filter(tenant=self.request.hrm_tenant).select_related("tax_type")
        return self.apply_master_filters(qs)


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


class PaymentTermListView(FoundationEntityListView):
    model = PaymentTerm
    page_title = "Payment terms"
    entity_title = "Payment terms"
    create_url_name = "foundation:payment_term_create"
    list_url_name = "foundation:payment_term_list"
    edit_url_name = "foundation:payment_term_edit"
    delete_url_name = "foundation:payment_term_delete"
    new_button_label = "Add term"
    search_fields = ["code", "name", "description"]
    sort_allowlist = ["code", "-code", "name", "-name"]
    default_sort = "code"
    sort_choices = [
        ("code", "Code A–Z"),
        ("-code", "Code Z–A"),
        ("name", "Name A–Z"),
        ("-name", "Name Z–A"),
    ]
    column_specs = [
        {"field": "code", "label": "Code", "mono": True},
        {"field": "name", "label": "Name"},
        {"field": "days_until_due", "label": "Days due"},
        {"field": "is_active", "label": "Active", "bool": True},
    ]

    def get_queryset(self):
        qs = PaymentTerm.objects.filter(tenant=self.request.hrm_tenant)
        return self.apply_master_filters(qs)


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
