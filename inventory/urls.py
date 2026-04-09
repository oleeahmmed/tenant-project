from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.InventoryDashboardView.as_view(), name="inventory_dashboard"),
    path("stock-adjustments/", views.StockAdjustmentListView.as_view(), name="stock_adjustment_list"),
    path("stock-adjustments/add/", views.StockAdjustmentCreateView.as_view(), name="stock_adjustment_create"),
    path(
        "stock-adjustments/<int:pk>/",
        views.StockAdjustmentDetailView.as_view(),
        name="stock_adjustment_detail",
    ),
    path(
        "stock-adjustments/<int:pk>/edit/",
        views.StockAdjustmentUpdateView.as_view(),
        name="stock_adjustment_update",
    ),
    path(
        "stock-adjustments/<int:pk>/post/",
        views.StockAdjustmentPostView.as_view(),
        name="stock_adjustment_post",
    ),
    path(
        "stock-adjustments/<int:pk>/delete/",
        views.StockAdjustmentDeleteView.as_view(),
        name="stock_adjustment_delete",
    ),
    path("goods-issues/", views.GoodsIssueListView.as_view(), name="goods_issue_list"),
    path("goods-issues/add/", views.GoodsIssueCreateView.as_view(), name="goods_issue_create"),
    path("goods-issues/<int:pk>/", views.GoodsIssueDetailView.as_view(), name="goods_issue_detail"),
    path("goods-issues/<int:pk>/edit/", views.GoodsIssueUpdateView.as_view(), name="goods_issue_update"),
    path("goods-issues/<int:pk>/release/", views.GoodsIssuePostView.as_view(), name="goods_issue_release"),
    path("goods-issues/<int:pk>/delete/", views.GoodsIssueDeleteView.as_view(), name="goods_issue_delete"),
    path(
        "inventory-transfers/",
        views.InventoryTransferListView.as_view(),
        name="inventory_transfer_list",
    ),
    path(
        "inventory-transfers/add/",
        views.InventoryTransferCreateView.as_view(),
        name="inventory_transfer_create",
    ),
    path(
        "inventory-transfers/<int:pk>/",
        views.InventoryTransferDetailView.as_view(),
        name="inventory_transfer_detail",
    ),
    path(
        "inventory-transfers/<int:pk>/edit/",
        views.InventoryTransferUpdateView.as_view(),
        name="inventory_transfer_update",
    ),
    path(
        "inventory-transfers/<int:pk>/complete/",
        views.InventoryTransferPostView.as_view(),
        name="inventory_transfer_complete",
    ),
    path(
        "inventory-transfers/<int:pk>/delete/",
        views.InventoryTransferDeleteView.as_view(),
        name="inventory_transfer_delete",
    ),
    path(
        "warehouse-stock/",
        views.WarehouseStockListView.as_view(),
        name="warehouse_stock_list",
    ),
    path(
        "stock-transactions/",
        views.StockTransactionListView.as_view(),
        name="stock_transaction_list",
    ),
]
