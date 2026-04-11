# POS Template Update Required

## Issue
The `erp/templates/erp/frontend/pos/quicksale_pos.html` needs to be completely replaced with the modern POS design from `erp/templates/admin/erp/pos/modern_pos.html`.

## Solution
Copy the entire content from `erp/templates/admin/erp/pos/modern_pos.html` and adapt it for the frontend by:

1. **Change the extends block:**
   ```django
   {% extends "base.html" %}
   ```

2. **Keep all the CSS styles** (already added)

3. **Copy the entire HTML structure** including:
   - Toolbar with customer selection, search, etc.
   - Payment & Shipping bar
   - Category chips
   - Product grid
   - Cart table view
   - Summary card with calculations
   - Checkout button

4. **Copy all JavaScript** including:
   - Cart management functions
   - Product search with autocomplete
   - Category filtering
   - Calculation functions
   - Complete sale function

5. **Update API endpoints** to match frontend URLs:
   - Change `/erp/api/autocomplete/customers/` (keep as is)
   - Change `{% url "erp:pos-search-product" %}` to `{% url "erp:pos_search_product" %}`
   - Change `{% url "erp:pos-create-sale" %}` to `{% url "erp:pos_create_sale" %}`

6. **Remove session-related code** (if not needed in frontend):
   - Session modals
   - Session management functions
   - Or keep them if you want session support

## Quick Fix
The easiest way is to:
1. Open `erp/templates/admin/erp/pos/modern_pos.html`
2. Copy everything after `{% block content %}`
3. Paste it into `erp/templates/erp/frontend/pos/quicksale_pos.html` after the closing `</style>` tag
4. Change `{% extends "admin/base_site.html" %}` to `{% extends "base.html" %}`
5. Remove the breadcrumbs block if not needed
6. Test and adjust as needed

## Files to Update
- `erp/templates/erp/frontend/pos/quicksale_pos.html` - Main template (REPLACE COMPLETELY)

## Current Status
- CSS styles have been added
- HTML content needs to be added
- JavaScript needs to be added
- The file is currently incomplete

## Action Required
Manually copy the content from modern_pos.html to quicksale_pos.html or use a text editor to complete the file.
