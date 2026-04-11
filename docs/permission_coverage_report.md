# Permission Coverage Report

Auto-generated from Django URL resolver.

## auth_tenants

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/api/auth/invite/<uuid:token>/` | `` | `AcceptInvitationView` | `(mixin default/fallback)` |
| `/api/auth/me/` | `` | `MeView` | `(mixin default/fallback)` |
| `/api/auth/permissions/` | `` | `PermissionListView` | `(mixin default/fallback)` |
| `/api/auth/permissions/<int:pk>/` | `` | `PermissionDetailView` | `(mixin default/fallback)` |
| `/api/auth/register/` | `` | `RegisterView` | `(mixin default/fallback)` |
| `/api/auth/tenant/invitations/` | `` | `InvitationListView` | `(mixin default/fallback)` |
| `/api/auth/tenant/invitations/<int:pk>/` | `` | `InvitationCancelView` | `(mixin default/fallback)` |
| `/api/auth/tenant/me/` | `` | `TenantMeView` | `(mixin default/fallback)` |
| `/api/auth/tenant/members/` | `` | `MemberListView` | `(mixin default/fallback)` |
| `/api/auth/tenant/members/<int:pk>/` | `` | `MemberDetailView` | `(mixin default/fallback)` |
| `/api/auth/tenant/members/<int:pk>/permissions/` | `` | `MemberPermissionView` | `(mixin default/fallback)` |
| `/api/auth/tenant/roles/` | `` | `RoleListView` | `(mixin default/fallback)` |
| `/api/auth/tenant/roles/<int:pk>/` | `` | `RoleDetailView` | `(mixin default/fallback)` |
| `/api/auth/tenants/` | `` | `TenantListView` | `(mixin default/fallback)` |
| `/api/auth/verify-otp/` | `` | `VerifyOTPView` | `(mixin default/fallback)` |
| `/dashboard/` | `dashboard` | `dashboard_view` | `(mixin default/fallback)` |
| `/dashboard/invitations/` | `invitations` | `invitations_view` | `(mixin default/fallback)` |
| `/dashboard/invitations/<int:pk>/cancel/` | `invitation_cancel` | `invitation_cancel_view` | `(mixin default/fallback)` |
| `/dashboard/invitations/create/` | `invitation_create` | `invitation_create_view` | `(mixin default/fallback)` |
| `/dashboard/members/` | `members` | `members_view` | `(mixin default/fallback)` |
| `/dashboard/members/<int:pk>/delete/` | `member_delete` | `member_delete_view` | `(mixin default/fallback)` |
| `/dashboard/members/<int:pk>/permissions/` | `member_permissions` | `member_permissions_view` | `(mixin default/fallback)` |
| `/dashboard/members/<int:pk>/role/` | `member_role` | `member_role_view` | `(mixin default/fallback)` |
| `/dashboard/permissions/` | `permission_list` | `permission_list_view` | `(mixin default/fallback)` |
| `/dashboard/roles/` | `roles` | `roles_view` | `(mixin default/fallback)` |
| `/dashboard/roles/<int:pk>/delete/` | `role_delete` | `role_delete_view` | `(mixin default/fallback)` |
| `/dashboard/roles/<int:pk>/update/` | `role_update` | `role_update_view` | `(mixin default/fallback)` |
| `/dashboard/roles/create/` | `role_create` | `role_create_view` | `(mixin default/fallback)` |
| `/dashboard/tenants/` | `tenant_list` | `tenant_list_view` | `(mixin default/fallback)` |
| `/dashboard/tenants/<int:tenant_id>/access/` | `tenant_access_matrix` | `tenant_access_matrix_view` | `(mixin default/fallback)` |
| `/invite/<uuid:token>/` | `invite_accept` | `invite_accept_view` | `(mixin default/fallback)` |
| `/login/` | `login` | `login_view` | `(mixin default/fallback)` |
| `/logout/` | `logout` | `logout_view` | `(mixin default/fallback)` |
| `/profile/` | `profile` | `profile_view` | `(mixin default/fallback)` |
| `/register/` | `register` | `register_view` | `(mixin default/fallback)` |
| `/verify-otp/` | `verify_otp` | `verify_otp_view` | `(mixin default/fallback)` |

## finance

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/dashboard/finance/` | `finance_dashboard` | `FinanceDashboardView` | `(mixin default/fallback)` |
| `/dashboard/finance/accounts/` | `account_list` | `AccountListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/accounts/<int:pk>/delete/` | `account_delete` | `AccountDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/accounts/<int:pk>/edit/` | `account_edit` | `AccountUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/accounts/add/` | `account_create` | `AccountCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/invoices/` | `ap_invoice_list` | `APInvoiceListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/invoices/<int:pk>/` | `ap_invoice_detail` | `APInvoiceDetailView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/invoices/<int:pk>/cancel/` | `ap_invoice_cancel` | `APInvoiceCancelView` | `finance.ap.post` |
| `/dashboard/finance/ap/invoices/<int:pk>/delete/` | `ap_invoice_delete` | `APInvoiceDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/invoices/<int:pk>/edit/` | `ap_invoice_edit` | `APInvoiceUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/invoices/<int:pk>/post/` | `ap_invoice_post` | `APInvoicePostView` | `finance.ap.post` |
| `/dashboard/finance/ap/invoices/add/` | `ap_invoice_create` | `APInvoiceCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/payments/` | `ap_payment_list` | `APPaymentListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/payments/<int:pk>/` | `ap_payment_detail` | `APPaymentDetailView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/payments/<int:pk>/cancel/` | `ap_payment_cancel` | `APPaymentCancelView` | `finance.ap.post` |
| `/dashboard/finance/ap/payments/<int:pk>/delete/` | `ap_payment_delete` | `APPaymentDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/payments/<int:pk>/edit/` | `ap_payment_edit` | `APPaymentUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ap/payments/<int:pk>/post/` | `ap_payment_post` | `APPaymentPostView` | `finance.ap.post` |
| `/dashboard/finance/ap/payments/add/` | `ap_payment_create` | `APPaymentCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/invoices/` | `ar_invoice_list` | `ARInvoiceListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/invoices/<int:pk>/` | `ar_invoice_detail` | `ARInvoiceDetailView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/invoices/<int:pk>/cancel/` | `ar_invoice_cancel` | `ARInvoiceCancelView` | `finance.ar.post` |
| `/dashboard/finance/ar/invoices/<int:pk>/delete/` | `ar_invoice_delete` | `ARInvoiceDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/invoices/<int:pk>/edit/` | `ar_invoice_edit` | `ARInvoiceUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/invoices/<int:pk>/post/` | `ar_invoice_post` | `ARInvoicePostView` | `finance.ar.post` |
| `/dashboard/finance/ar/invoices/add/` | `ar_invoice_create` | `ARInvoiceCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/receipts/` | `ar_receipt_list` | `ARReceiptListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/receipts/<int:pk>/` | `ar_receipt_detail` | `ARReceiptDetailView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/receipts/<int:pk>/cancel/` | `ar_receipt_cancel` | `ARReceiptCancelView` | `finance.ar.post` |
| `/dashboard/finance/ar/receipts/<int:pk>/delete/` | `ar_receipt_delete` | `ARReceiptDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/receipts/<int:pk>/edit/` | `ar_receipt_edit` | `ARReceiptUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/ar/receipts/<int:pk>/post/` | `ar_receipt_post` | `ARReceiptPostView` | `finance.ar.post` |
| `/dashboard/finance/ar/receipts/add/` | `ar_receipt_create` | `ARReceiptCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/assets/depreciations/` | `asset_depreciation_list` | `AssetDepreciationListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/assets/depreciations/<int:pk>/post/` | `asset_depreciation_post` | `AssetDepreciationPostView` | `finance.asset.post` |
| `/dashboard/finance/assets/depreciations/add/` | `asset_depreciation_create` | `AssetDepreciationCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/assets/fixed/` | `fixed_asset_list` | `FixedAssetListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/assets/fixed/add/` | `fixed_asset_create` | `FixedAssetCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/budgets/` | `budget_list` | `BudgetListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/budgets/add/` | `budget_create` | `BudgetCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/cash/banks/` | `bank_account_list` | `BankAccountListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/cash/banks/add/` | `bank_account_create` | `BankAccountCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/cash/transactions/` | `cash_transaction_list` | `CashTransactionListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/cash/transactions/<int:pk>/post/` | `cash_transaction_post` | `CashTransactionPostView` | `finance.cash.post` |
| `/dashboard/finance/cash/transactions/add/` | `cash_transaction_create` | `CashTransactionCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-periods/` | `fiscal_period_list` | `FiscalPeriodListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-periods/<int:pk>/delete/` | `fiscal_period_delete` | `FiscalPeriodDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-periods/<int:pk>/edit/` | `fiscal_period_edit` | `FiscalPeriodUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-periods/add/` | `fiscal_period_create` | `FiscalPeriodCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-years/` | `fiscal_year_list` | `FiscalYearListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-years/<int:pk>/delete/` | `fiscal_year_delete` | `FiscalYearDeleteView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-years/<int:pk>/edit/` | `fiscal_year_edit` | `FiscalYearUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/fiscal-years/add/` | `fiscal_year_create` | `FiscalYearCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/guide/` | `finance_guide` | `FinanceGuideView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/journals/` | `journal_list` | `JournalEntryListView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/journals/<int:pk>/` | `journal_detail` | `JournalEntryDetailView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/journals/<int:pk>/edit/` | `journal_edit` | `JournalEntryUpdateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/journals/<int:pk>/post/` | `journal_post` | `JournalEntryPostView` | `finance.journal.post` |
| `/dashboard/finance/journals/<int:pk>/reverse/` | `journal_reverse` | `JournalEntryReverseView` | `finance.journal.reverse` |
| `/dashboard/finance/journals/add/` | `journal_create` | `JournalEntryCreateView` | `finance.delete, finance.manage, finance.view` |
| `/dashboard/finance/reports/balance-sheet/` | `report_balance_sheet` | `BalanceSheetReportView` | `finance.report.view` |
| `/dashboard/finance/reports/budget-vs-actual/` | `report_budget_vs_actual` | `BudgetVsActualReportView` | `finance.report.view` |
| `/dashboard/finance/reports/gl/` | `report_gl` | `GeneralLedgerReportView` | `finance.report.view` |
| `/dashboard/finance/reports/profit-loss/` | `report_profit_loss` | `ProfitLossReportView` | `finance.report.view` |
| `/dashboard/finance/reports/trial-balance/` | `report_trial_balance` | `TrialBalanceReportView` | `finance.report.view` |

## foundation

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/api/foundation/autocomplete/categories/` | `autocomplete_categories` | `CategoryAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/currencies/` | `autocomplete_currencies` | `CurrencyAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/customers/` | `autocomplete_customers` | `CustomerAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/payment-methods/` | `autocomplete_payment_methods` | `PaymentMethodAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/product-variants/` | `autocomplete_product_variants` | `ProductVariantAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/products/` | `autocomplete_products` | `ProductAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/sales-persons/` | `autocomplete_sales_persons` | `SalesPersonAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/suppliers/` | `autocomplete_suppliers` | `SupplierAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/tax-types/` | `autocomplete_tax_types` | `TaxTypeAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/units-of-measure/` | `autocomplete_uoms` | `UnitOfMeasureAutocompleteView` | `(mixin default/fallback)` |
| `/api/foundation/autocomplete/warehouses/` | `autocomplete_warehouses` | `WarehouseAutocompleteView` | `(mixin default/fallback)` |
| `/dashboard/foundation/` | `foundation_dashboard` | `FoundationDashboardView` | `(mixin default/fallback)` |
| `/dashboard/foundation/categories/` | `category_list` | `CategoryListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/categories/<int:pk>/delete/` | `category_delete` | `CategoryDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/categories/<int:pk>/edit/` | `category_edit` | `CategoryUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/categories/add/` | `category_create` | `CategoryCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/currencies/` | `currency_list` | `CurrencyListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/currencies/<int:pk>/delete/` | `currency_delete` | `CurrencyDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/currencies/<int:pk>/edit/` | `currency_edit` | `CurrencyUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/currencies/add/` | `currency_create` | `CurrencyCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/customers/` | `customer_list` | `CustomerListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/customers/<int:pk>/delete/` | `customer_delete` | `CustomerDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/customers/<int:pk>/edit/` | `customer_edit` | `CustomerUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/customers/add/` | `customer_create` | `CustomerCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/exchange-rates/` | `exchange_rate_list` | `ExchangeRateListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/exchange-rates/<int:pk>/delete/` | `exchange_rate_delete` | `ExchangeRateDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/exchange-rates/<int:pk>/edit/` | `exchange_rate_edit` | `ExchangeRateUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/exchange-rates/add/` | `exchange_rate_create` | `ExchangeRateCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-methods/` | `payment_method_list` | `PaymentMethodListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-methods/<int:pk>/delete/` | `payment_method_delete` | `PaymentMethodDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-methods/<int:pk>/edit/` | `payment_method_edit` | `PaymentMethodUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-methods/add/` | `payment_method_create` | `PaymentMethodCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-terms/` | `payment_term_list` | `PaymentTermListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-terms/<int:pk>/delete/` | `payment_term_delete` | `PaymentTermDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-terms/<int:pk>/edit/` | `payment_term_edit` | `PaymentTermUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/payment-terms/add/` | `payment_term_create` | `PaymentTermCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/products/` | `product_list` | `ProductListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/products/<int:pk>/` | `product_detail` | `ProductDetailView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/products/<int:pk>/delete/` | `product_delete` | `ProductDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/products/<int:pk>/edit/` | `product_edit` | `ProductUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/products/add/` | `product_create` | `ProductCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/sales-persons/` | `sales_person_list` | `SalesPersonListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/sales-persons/<int:pk>/delete/` | `sales_person_delete` | `SalesPersonDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/sales-persons/<int:pk>/edit/` | `sales_person_edit` | `SalesPersonUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/sales-persons/add/` | `sales_person_create` | `SalesPersonCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/suppliers/` | `supplier_list` | `SupplierListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/suppliers/<int:pk>/delete/` | `supplier_delete` | `SupplierDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/suppliers/<int:pk>/edit/` | `supplier_edit` | `SupplierUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/suppliers/add/` | `supplier_create` | `SupplierCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-rates/` | `tax_rate_list` | `TaxRateListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-rates/<int:pk>/delete/` | `tax_rate_delete` | `TaxRateDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-rates/<int:pk>/edit/` | `tax_rate_edit` | `TaxRateUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-rates/add/` | `tax_rate_create` | `TaxRateCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-types/` | `tax_type_list` | `TaxTypeListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-types/<int:pk>/delete/` | `tax_type_delete` | `TaxTypeDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-types/<int:pk>/edit/` | `tax_type_edit` | `TaxTypeUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/tax-types/add/` | `tax_type_create` | `TaxTypeCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/units-of-measure/` | `uom_list` | `UomListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/units-of-measure/<int:pk>/delete/` | `uom_delete` | `UomDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/units-of-measure/<int:pk>/edit/` | `uom_edit` | `UomUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/units-of-measure/add/` | `uom_create` | `UomCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/uom-conversions/` | `uom_conversion_list` | `UomConversionListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/uom-conversions/<int:pk>/delete/` | `uom_conversion_delete` | `UomConversionDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/uom-conversions/<int:pk>/edit/` | `uom_conversion_edit` | `UomConversionUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/uom-conversions/add/` | `uom_conversion_create` | `UomConversionCreateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/warehouses/` | `warehouse_list` | `WarehouseListView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/warehouses/<int:pk>/delete/` | `warehouse_delete` | `WarehouseDeleteView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/warehouses/<int:pk>/edit/` | `warehouse_edit` | `WarehouseUpdateView` | `foundation.delete, foundation.manage, foundation.view` |
| `/dashboard/foundation/warehouses/add/` | `warehouse_create` | `WarehouseCreateView` | `foundation.delete, foundation.manage, foundation.view` |

## hrm

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/api/hrm/mobile/check-in/` | `mobile_checkin` | `EmployeeMobileCheckinView` | `(mixin default/fallback)` |
| `/api/hrm/mobile/location-policy/` | `mobile_location_policy` | `LocationPolicyInfoView` | `(mixin default/fallback)` |
| `/api/hrm/pyzk/devices/<int:device_id>/fetch-attendance/` | `pyzk_fetch_attendance` | `PyZKFetchAttendanceView` | `(mixin default/fallback)` |
| `/api/hrm/pyzk/devices/<int:device_id>/fetch-users/` | `pyzk_fetch_users` | `PyZKFetchUsersView` | `(mixin default/fallback)` |
| `/api/hrm/pyzk/devices/<int:device_id>/import-attendance/` | `pyzk_import_attendance` | `PyZKImportAttendanceView` | `(mixin default/fallback)` |
| `/api/hrm/pyzk/devices/<int:device_id>/import-users/` | `pyzk_import_users` | `PyZKImportUsersView` | `(mixin default/fallback)` |
| `/dashboard/hrm/` | `hrm_dashboard` | `HrmDashboardView` | `(mixin default/fallback)` |
| `/dashboard/hrm/api/employees/picker/` | `api_employee_picker` | `HrmEmployeePickerAPIView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/api/employees/search/` | `api_employee_search` | `HrmEmployeeSearchAPIView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/attendance/` | `attendance_list` | `AttendanceRecordListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/attendance/<int:pk>/delete/` | `attendance_delete` | `AttendanceRecordDeleteView` | `hrm.attendance.manage` |
| `/dashboard/hrm/attendance/<int:pk>/edit/` | `attendance_edit` | `AttendanceRecordUpdateView` | `hrm.attendance.manage` |
| `/dashboard/hrm/attendance/add/` | `attendance_create` | `AttendanceRecordCreateView` | `hrm.attendance.manage` |
| `/dashboard/hrm/attendance/bulk-action/` | `attendance_bulk_action` | `AttendanceBulkActionView` | `hrm.attendance.manage` |
| `/dashboard/hrm/departments/` | `department_list` | `DepartmentListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/departments/<int:pk>/delete/` | `department_delete` | `DepartmentDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/departments/<int:pk>/edit/` | `department_edit` | `DepartmentUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/departments/add/` | `department_create` | `DepartmentCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/employees/` | `employee_list` | `EmployeeListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/employees/<int:pk>/delete/` | `employee_delete` | `EmployeeDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/employees/<int:pk>/edit/` | `employee_edit` | `EmployeeUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/employees/add/` | `employee_create` | `EmployeeCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/holidays/` | `holiday_list` | `HolidayListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/holidays/<int:pk>/delete/` | `holiday_delete` | `HolidayDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/holidays/<int:pk>/edit/` | `holiday_edit` | `HolidayUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/holidays/add/` | `holiday_create` | `HolidayCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/job-titles/` | `job_title_list` | `JobTitleListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/job-titles/<int:pk>/delete/` | `job_title_delete` | `JobTitleDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/job-titles/<int:pk>/edit/` | `job_title_edit` | `JobTitleUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/job-titles/add/` | `job_title_create` | `JobTitleCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leave-types/` | `leave_type_list` | `LeaveTypeListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leave-types/<int:pk>/delete/` | `leave_type_delete` | `LeaveTypeDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leave-types/<int:pk>/edit/` | `leave_type_edit` | `LeaveTypeUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leave-types/add/` | `leave_type_create` | `LeaveTypeCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leaves/` | `leave_request_list` | `LeaveRequestListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/leaves/<int:pk>/approve/` | `leave_request_approve` | `LeaveRequestApproveView` | `hrm.leave.approve` |
| `/dashboard/hrm/leaves/<int:pk>/reject/` | `leave_request_reject` | `LeaveRequestRejectView` | `hrm.leave.approve` |
| `/dashboard/hrm/me/` | `employee_home` | `EmployeeDashboardView` | `(mixin default/fallback)` |
| `/dashboard/hrm/me/check-in/` | `employee_checkin` | `EmployeeCheckinView` | `(mixin default/fallback)` |
| `/dashboard/hrm/me/leave/` | `employee_leave_submit` | `EmployeeLeaveSubmitView` | `(mixin default/fallback)` |
| `/dashboard/hrm/notices/` | `notice_list` | `NoticeListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/notices/<int:pk>/delete/` | `notice_delete` | `NoticeDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/notices/<int:pk>/edit/` | `notice_edit` | `NoticeUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/notices/add/` | `notice_create` | `NoticeCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/overtime/` | `overtime_list` | `OvertimeRequestListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/overtime/<int:pk>/approve/` | `overtime_approve` | `OvertimeApproveView` | `hrm.overtime.approve` |
| `/dashboard/hrm/overtime/<int:pk>/delete/` | `overtime_delete` | `OvertimeRequestDeleteView` | `hrm.overtime.manage` |
| `/dashboard/hrm/overtime/<int:pk>/edit/` | `overtime_edit` | `OvertimeRequestUpdateView` | `hrm.overtime.manage` |
| `/dashboard/hrm/overtime/<int:pk>/reject/` | `overtime_reject` | `OvertimeRejectView` | `hrm.overtime.approve` |
| `/dashboard/hrm/overtime/add/` | `overtime_create` | `OvertimeRequestCreateView` | `hrm.overtime.manage` |
| `/dashboard/hrm/overtime/bulk-action/` | `overtime_bulk_action` | `OvertimeBulkActionView` | `hrm.overtime.manage` |
| `/dashboard/hrm/roster/bulk/` | `roster_bulk` | `RosterBulkView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/bulk/apply/` | `roster_bulk_apply` | `RosterBulkApplyView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/exceptions/` | `roster_exception_list` | `RosterExceptionListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/exceptions/<int:pk>/delete/` | `roster_exception_delete` | `RosterExceptionDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/exceptions/<int:pk>/edit/` | `roster_exception_edit` | `RosterExceptionUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/exceptions/add/` | `roster_exception_create` | `RosterExceptionCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/preview/` | `roster_preview` | `RosterPreviewView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/ranges/` | `roster_range_list` | `RosterRangeListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/ranges/<int:pk>/delete/` | `roster_range_delete` | `RosterRangeDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/ranges/<int:pk>/edit/` | `roster_range_edit` | `RosterRangeUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/ranges/add/` | `roster_range_create` | `RosterRangeCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/weekday/` | `roster_weekday_list` | `RosterWeekdayListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/weekday/<int:pk>/delete/` | `roster_weekday_delete` | `RosterWeekdayDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/weekday/<int:pk>/edit/` | `roster_weekday_edit` | `RosterWeekdayUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/roster/weekday/add/` | `roster_weekday_create` | `RosterWeekdayCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/set-active-tenant/` | `set_active_tenant` | `SetActiveHrmTenantView` | `(mixin default/fallback)` |
| `/dashboard/hrm/shifts/` | `shift_list` | `ShiftListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/shifts/<int:pk>/delete/` | `shift_delete` | `ShiftDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/shifts/<int:pk>/edit/` | `shift_edit` | `ShiftUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/shifts/add/` | `shift_create` | `ShiftCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/shifts/guide/` | `shift_management_guide` | `ShiftManagementGuideView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/` | `zk_device_list` | `ZKDeviceListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/<int:pk>/delete/` | `zk_device_delete` | `ZKDeviceDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/<int:pk>/edit/` | `zk_device_edit` | `ZKDeviceUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/<int:pk>/sync-attendance/` | `zk_sync_attendance` | `ZKSyncAttendanceView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/<int:pk>/sync-users/` | `zk_sync_users` | `ZKSyncUsersView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/devices/add/` | `zk_device_create` | `ZKDeviceCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/locations/` | `attendance_location_list` | `AttendanceLocationListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/locations/<int:pk>/delete/` | `attendance_location_delete` | `AttendanceLocationDeleteView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/locations/<int:pk>/edit/` | `attendance_location_edit` | `AttendanceLocationUpdateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/locations/add/` | `attendance_location_create` | `AttendanceLocationCreateView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/logs/` | `zk_attendance_log_list` | `AttendanceLogListView` | `hrm.delete, hrm.manage, hrm.view` |
| `/dashboard/hrm/zk/policy/` | `location_policy` | `LocationPolicyEditView` | `hrm.location_policy.manage` |
| `/dashboard/hrm/zk/reports/locations/` | `location_attendance_report` | `LocationAttendanceReportView` | `hrm.location_report.view` |
| `/dashboard/hrm/zk/reviews/` | `attendance_review_list` | `AttendanceReviewListView` | `hrm.attendance.review` |
| `/dashboard/hrm/zk/reviews/<int:pk>/action/` | `attendance_review_action` | `AttendanceReviewApproveView` | `hrm.attendance.review` |

## inventory

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/api/inventory/product-warehouse/` | `product_warehouse_context` | `ProductWarehouseContextView` | `(mixin default/fallback)` |
| `/dashboard/inventory/` | `inventory_dashboard` | `InventoryDashboardView` | `(mixin default/fallback)` |
| `/dashboard/inventory/goods-issues/` | `goods_issue_list` | `GoodsIssueListView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/goods-issues/<int:pk>/` | `goods_issue_detail` | `GoodsIssueDetailView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/goods-issues/<int:pk>/delete/` | `goods_issue_delete` | `GoodsIssueDeleteView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/goods-issues/<int:pk>/edit/` | `goods_issue_update` | `GoodsIssueUpdateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/goods-issues/<int:pk>/release/` | `goods_issue_release` | `GoodsIssuePostView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/goods-issues/add/` | `goods_issue_create` | `GoodsIssueCreateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/` | `inventory_transfer_list` | `InventoryTransferListView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/<int:pk>/` | `inventory_transfer_detail` | `InventoryTransferDetailView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/<int:pk>/complete/` | `inventory_transfer_complete` | `InventoryTransferPostView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/<int:pk>/delete/` | `inventory_transfer_delete` | `InventoryTransferDeleteView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/<int:pk>/edit/` | `inventory_transfer_update` | `InventoryTransferUpdateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/inventory-transfers/add/` | `inventory_transfer_create` | `InventoryTransferCreateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/` | `stock_adjustment_list` | `StockAdjustmentListView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/<int:pk>/` | `stock_adjustment_detail` | `StockAdjustmentDetailView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/<int:pk>/delete/` | `stock_adjustment_delete` | `StockAdjustmentDeleteView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/<int:pk>/edit/` | `stock_adjustment_update` | `StockAdjustmentUpdateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/<int:pk>/post/` | `stock_adjustment_post` | `StockAdjustmentPostView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-adjustments/add/` | `stock_adjustment_create` | `StockAdjustmentCreateView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/stock-transactions/` | `stock_transaction_list` | `StockTransactionListView` | `inventory.delete, inventory.manage, inventory.view` |
| `/dashboard/inventory/warehouse-stock/` | `warehouse_stock_list` | `WarehouseStockListView` | `inventory.delete, inventory.manage, inventory.view` |

## production

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/dashboard/production/` | `production_dashboard` | `ProductionDashboardView` | `(mixin default/fallback)` |
| `/dashboard/production/bom/` | `bom_list` | `BillOfMaterialListView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/bom/<int:pk>/` | `bom_detail` | `BillOfMaterialDetailView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/bom/<int:pk>/activate/` | `bom_activate` | `BillOfMaterialActivateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/bom/<int:pk>/delete/` | `bom_delete` | `BillOfMaterialDeleteView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/bom/<int:pk>/edit/` | `bom_edit` | `BillOfMaterialUpdateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/bom/add/` | `bom_create` | `BillOfMaterialCreateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/` | `issue_list` | `IssueForProductionListView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/<int:pk>/` | `issue_detail` | `IssueForProductionDetailView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/<int:pk>/delete/` | `issue_delete` | `IssueForProductionDeleteView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/<int:pk>/edit/` | `issue_edit` | `IssueForProductionUpdateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/<int:pk>/post/` | `issue_post` | `IssueForProductionPostView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/issues/add/` | `issue_create` | `IssueForProductionCreateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/` | `order_list` | `ProductionOrderListView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/<int:pk>/` | `order_detail` | `ProductionOrderDetailView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/<int:pk>/delete/` | `order_delete` | `ProductionOrderDeleteView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/<int:pk>/edit/` | `order_edit` | `ProductionOrderUpdateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/<int:pk>/release/` | `order_release` | `ProductionOrderReleaseView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/orders/add/` | `order_create` | `ProductionOrderCreateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/` | `receipt_list` | `ReceiptFromProductionListView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/<int:pk>/` | `receipt_detail` | `ReceiptFromProductionDetailView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/<int:pk>/delete/` | `receipt_delete` | `ReceiptFromProductionDeleteView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/<int:pk>/edit/` | `receipt_edit` | `ReceiptFromProductionUpdateView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/<int:pk>/post/` | `receipt_post` | `ReceiptFromProductionPostView` | `production.delete, production.manage, production.view` |
| `/dashboard/production/receipts/add/` | `receipt_create` | `ReceiptFromProductionCreateView` | `production.delete, production.manage, production.view` |

## purchase

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/dashboard/purchase/` | `purchase_dashboard` | `PurchaseDashboardView` | `(mixin default/fallback)` |
| `/dashboard/purchase/guide/` | `purchase_guide` | `PurchaseGuideView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/` | `purchase_order_list` | `PurchaseOrderListView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/<int:pk>/` | `purchase_order_detail` | `PurchaseOrderDetailView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/<int:pk>/approve/` | `purchase_order_approve` | `PurchaseOrderApproveView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/<int:pk>/delete/` | `purchase_order_delete` | `PurchaseOrderDeleteView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/<int:pk>/edit/` | `purchase_order_edit` | `PurchaseOrderUpdateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/orders/add/` | `purchase_order_create` | `PurchaseOrderCreateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/` | `goods_receipt_list` | `GoodsReceiptListView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/<int:pk>/` | `goods_receipt_detail` | `GoodsReceiptDetailView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/<int:pk>/delete/` | `goods_receipt_delete` | `GoodsReceiptDeleteView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/<int:pk>/edit/` | `goods_receipt_edit` | `GoodsReceiptUpdateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/<int:pk>/post/` | `goods_receipt_post` | `GoodsReceiptPostView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/receipts/add/` | `goods_receipt_create` | `GoodsReceiptCreateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/` | `purchase_request_list` | `PurchaseRequestListView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/<int:pk>/` | `purchase_request_detail` | `PurchaseRequestDetailView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/<int:pk>/approve/` | `purchase_request_approve` | `PurchaseRequestApproveView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/<int:pk>/delete/` | `purchase_request_delete` | `PurchaseRequestDeleteView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/<int:pk>/edit/` | `purchase_request_edit` | `PurchaseRequestUpdateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/requests/add/` | `purchase_request_create` | `PurchaseRequestCreateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/` | `purchase_return_list` | `PurchaseReturnListView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/<int:pk>/` | `purchase_return_detail` | `PurchaseReturnDetailView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/<int:pk>/delete/` | `purchase_return_delete` | `PurchaseReturnDeleteView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/<int:pk>/edit/` | `purchase_return_edit` | `PurchaseReturnUpdateView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/<int:pk>/post/` | `purchase_return_post` | `PurchaseReturnPostView` | `purchase.delete, purchase.manage, purchase.view` |
| `/dashboard/purchase/returns/add/` | `purchase_return_create` | `PurchaseReturnCreateView` | `purchase.delete, purchase.manage, purchase.view` |

## recruitment

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/dashboard/hrm/recruitment/applications/` | `recruitment_application_list` | `ApplicationListView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/applications/<int:pk>/delete/` | `recruitment_application_delete` | `ApplicationDeleteView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/applications/<int:pk>/edit/` | `recruitment_application_edit` | `ApplicationUpdateView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/applications/add/` | `recruitment_application_create` | `ApplicationCreateView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/jobs/` | `recruitment_job_list` | `JobPostingListView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/jobs/<int:pk>/delete/` | `recruitment_job_delete` | `JobPostingDeleteView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/jobs/<int:pk>/edit/` | `recruitment_job_edit` | `JobPostingUpdateView` | `recruitment.delete, recruitment.manage, recruitment.view` |
| `/dashboard/hrm/recruitment/jobs/add/` | `recruitment_job_create` | `JobPostingCreateView` | `recruitment.delete, recruitment.manage, recruitment.view` |

## sales

| Route | URL Name | View | Permission Contract |
|---|---|---|---|
| `/dashboard/sales/` | `sales_dashboard` | `SalesDashboardView` | `(mixin default/fallback)` |
| `/dashboard/sales/deliveries/` | `delivery_list` | `DeliveryNoteListView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/deliveries/<int:pk>/` | `delivery_detail` | `DeliveryNoteDetailView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/deliveries/<int:pk>/delete/` | `delivery_delete` | `DeliveryNoteDeleteView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/deliveries/<int:pk>/edit/` | `delivery_edit` | `DeliveryNoteUpdateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/deliveries/<int:pk>/post/` | `delivery_post` | `DeliveryNotePostView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/deliveries/add/` | `delivery_create` | `DeliveryNoteCreateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/` | `order_list` | `SalesOrderListView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/<int:pk>/` | `order_detail` | `SalesOrderDetailView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/<int:pk>/approve/` | `order_approve` | `SalesOrderApproveView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/<int:pk>/delete/` | `order_delete` | `SalesOrderDeleteView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/<int:pk>/edit/` | `order_edit` | `SalesOrderUpdateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/orders/add/` | `order_create` | `SalesOrderCreateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/` | `quotation_list` | `SalesQuotationListView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/<int:pk>/` | `quotation_detail` | `SalesQuotationDetailView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/<int:pk>/approve/` | `quotation_approve` | `SalesQuotationApproveView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/<int:pk>/delete/` | `quotation_delete` | `SalesQuotationDeleteView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/<int:pk>/edit/` | `quotation_edit` | `SalesQuotationUpdateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/quotations/add/` | `quotation_create` | `SalesQuotationCreateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/` | `return_list` | `SalesReturnListView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/<int:pk>/` | `return_detail` | `SalesReturnDetailView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/<int:pk>/delete/` | `return_delete` | `SalesReturnDeleteView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/<int:pk>/edit/` | `return_edit` | `SalesReturnUpdateView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/<int:pk>/post/` | `return_post` | `SalesReturnPostView` | `sales.delete, sales.manage, sales.view` |
| `/dashboard/sales/returns/add/` | `return_create` | `SalesReturnCreateView` | `sales.delete, sales.manage, sales.view` |
