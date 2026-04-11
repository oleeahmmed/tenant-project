"""Inventory JSON APIs (session + tenant scope)."""

from __future__ import annotations

from decimal import Decimal

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from foundation.models import Product, Warehouse
from inventory.models import WarehouseStock

from foundation.api.views import _resolve_tenant


class InventorySessionAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]


class ProductWarehouseContextView(InventorySessionAPIView):
    """
    GET product by ``product_id`` or ``product_sku`` (one required).
    Optional warehouse: ``warehouse_id`` or ``warehouse_code``.
    Without warehouse: product prices only (default unit cost auto-fill).
    With warehouse: on-hand qty and min/max from WarehouseStock.
    """

    def get(self, request):
        tenant = _resolve_tenant(
            request,
            module_code="inventory",
            required_permission="inventory.view",
        )
        if not tenant:
            return Response({"detail": "No workspace tenant."}, status=403)

        sku_raw = (request.GET.get("product_sku") or "").strip()
        if sku_raw:
            product = (
                Product.objects.filter(tenant=tenant, sku=sku_raw)
                .only("id", "sku", "name", "default_unit_cost", "list_price")
                .first()
            )
        else:
            try:
                product_id = int(request.GET.get("product_id", ""))
            except (TypeError, ValueError):
                return Response({"detail": "product_id or product_sku is required."}, status=400)
            product = Product.objects.filter(pk=product_id, tenant=tenant).only(
                "id", "sku", "name", "default_unit_cost", "list_price"
            ).first()
        if not product:
            return Response({"detail": "Product not found."}, status=404)

        def _d(v):
            if v is None:
                return None
            return str(v)

        raw_wh_id = request.GET.get("warehouse_id", "").strip()
        raw_wh_code = (request.GET.get("warehouse_code") or "").strip()
        warehouse_id = None
        warehouse = None

        if raw_wh_id:
            try:
                warehouse_id = int(raw_wh_id)
            except (TypeError, ValueError):
                return Response({"detail": "warehouse_id must be an integer."}, status=400)
            warehouse = Warehouse.objects.filter(pk=warehouse_id, tenant=tenant).only("id", "code", "name").first()
        elif raw_wh_code:
            warehouse = Warehouse.objects.filter(code=raw_wh_code, tenant=tenant).only("id", "code", "name").first()
            if warehouse:
                warehouse_id = warehouse.id

        if warehouse_id is None:
            return Response(
                {
                    "product_id": product.id,
                    "sku": product.sku,
                    "name": product.name,
                    "warehouse_id": None,
                    "warehouse_code": None,
                    "default_unit_cost": str(product.default_unit_cost),
                    "list_price": str(product.list_price),
                    "qty_on_hand": "0",
                    "min_quantity": None,
                    "max_quantity": None,
                }
            )

        if not warehouse:
            return Response({"detail": "Warehouse not found."}, status=404)

        ws = (
            WarehouseStock.objects.filter(
                tenant=tenant,
                product_id=product.id,
                warehouse_id=warehouse_id,
            )
            .only("quantity", "min_quantity", "max_quantity")
            .first()
        )

        qty = ws.quantity if ws else Decimal("0")
        min_q = ws.min_quantity if ws else None
        max_q = ws.max_quantity if ws else None

        return Response(
            {
                "product_id": product.id,
                "sku": product.sku,
                "name": product.name,
                "warehouse_id": warehouse.id,
                "warehouse_code": warehouse.code,
                "default_unit_cost": str(product.default_unit_cost),
                "list_price": str(product.list_price),
                "qty_on_hand": str(qty),
                "min_quantity": _d(min_q),
                "max_quantity": _d(max_q),
            }
        )
