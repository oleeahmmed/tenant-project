"""Read-only JSON APIs for Foundation master data (autocomplete + fast lookups)."""

from __future__ import annotations

from django.db.models import Q
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from foundation.models import (
    Category,
    Currency,
    Customer,
    PaymentMethod,
    Product,
    ProductVariant,
    SalesPerson,
    Supplier,
    TaxType,
    UnitOfMeasure,
    Warehouse,
)
from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant


def _resolve_tenant(request):
    """Same workspace scope as Foundation / Inventory dashboards."""
    t = get_hrm_tenant(request)
    if t is None or not request.user.is_authenticated:
        return None
    if getattr(request.user, "role", None) == "super_admin":
        return t
    if user_belongs_to_workspace_tenant(request.user, t):
        return t
    return None


def _limit(request, default=30, cap=100):
    try:
        return min(max(int(request.GET.get("limit", default)), 1), cap)
    except (TypeError, ValueError):
        return default


class FoundationSessionAPIView(APIView):
    """Browser session (cookie) auth for same-origin dashboard + fetch()."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


class ProductAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Product.objects.filter(tenant=tenant, is_active=True).only(
            "id", "sku", "name", "default_unit_cost", "list_price"
        )
        if q:
            qs = qs.filter(Q(sku__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [
            {
                "id": p.id,
                "label": f"{p.sku} — {p.name}",
                "sku": p.sku,
                "name": p.name,
                "default_unit_cost": str(p.default_unit_cost),
                "list_price": str(p.list_price),
            }
            for p in qs
        ]
        return Response({"results": results})


class WarehouseAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Warehouse.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [{"id": w.id, "label": f"{w.code} — {w.name}", "code": w.code, "name": w.name} for w in qs]
        return Response({"results": results})


class CategoryAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Category.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [{"id": c.id, "label": f"{c.code} — {c.name}", "code": c.code, "name": c.name} for c in qs]
        return Response({"results": results})


class CustomerAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Customer.objects.filter(tenant=tenant, is_active=True).only("id", "customer_code", "name")
        if q:
            qs = qs.filter(Q(customer_code__icontains=q) | Q(name__icontains=q) | Q(email__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [
            {"id": c.id, "label": f"{c.customer_code} — {c.name}", "code": c.customer_code, "name": c.name}
            for c in qs
        ]
        return Response({"results": results})


class SupplierAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Supplier.objects.filter(tenant=tenant, is_active=True).only("id", "supplier_code", "name")
        if q:
            qs = qs.filter(Q(supplier_code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [
            {"id": s.id, "label": f"{s.supplier_code} — {s.name}", "code": s.supplier_code, "name": s.name}
            for s in qs
        ]
        return Response({"results": results})


class UnitOfMeasureAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = UnitOfMeasure.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("code")[:limit]
        results = [{"id": u.id, "label": f"{u.code} ({u.name})", "code": u.code, "name": u.name} for u in qs]
        return Response({"results": results})


class CurrencyAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = Currency.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("code")[:limit]
        results = [{"id": c.id, "label": f"{c.code} — {c.name}", "code": c.code, "name": c.name} for c in qs]
        return Response({"results": results})


class PaymentMethodAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = PaymentMethod.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [{"id": p.id, "label": f"{p.code} — {p.name}", "code": p.code, "name": p.name} for p in qs]
        return Response({"results": results})


class SalesPersonAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = SalesPerson.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [{"id": s.id, "label": f"{s.code} — {s.name}", "code": s.code, "name": s.name} for s in qs]
        return Response({"results": results})


class TaxTypeAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        limit = _limit(request)
        qs = TaxType.objects.filter(tenant=tenant, is_active=True).only("id", "code", "name")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q))
        qs = qs.order_by("name")[:limit]
        results = [{"id": t.id, "label": f"{t.code} — {t.name}", "code": t.code, "name": t.name} for t in qs]
        return Response({"results": results})


class ProductVariantAutocompleteView(FoundationSessionAPIView):
    def get(self, request):
        tenant = _resolve_tenant(request)
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)
        q = request.GET.get("q", "").strip()
        product_id = request.GET.get("product_id")
        limit = _limit(request)
        qs = ProductVariant.objects.filter(tenant=tenant, is_active=True).select_related("product")
        if product_id:
            try:
                qs = qs.filter(product_id=int(product_id))
            except (TypeError, ValueError):
                pass
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(name__icontains=q) | Q(product__sku__icontains=q))
        qs = qs.order_by("product__sku", "code")[:limit]
        results = []
        for v in qs:
            results.append(
                {
                    "id": v.id,
                    "label": f"{v.product.sku} / {v.code} — {v.name}" if v.name else f"{v.product.sku} / {v.code}",
                    "code": v.code,
                    "name": v.name or "",
                    "product_id": v.product_id,
                }
            )
        return Response({"results": results})
