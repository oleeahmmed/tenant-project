/**
 * Form Autocomplete Helper - Uses existing Select2 + Autocomplete APIs
 * Pattern from: erp/templates/admin/erp/reports/sales_order_detail.html
 */

// Initialize Select2 autocomplete for a select element
function initAutocomplete(selector, apiUrl, placeholder) {
    $(selector).select2({
        ajax: {
            url: apiUrl,
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    page: params.page || 1
                };
            },
            processResults: function (data) {
                return {
                    results: data.results,
                    pagination: {
                        more: data.pagination.more
                    }
                };
            },
            cache: true
        },
        placeholder: placeholder || 'Select...',
        allowClear: true,
        minimumInputLength: 0,
        width: '100%'
    });
}

// Auto-fill product price when product is selected
function initProductPriceAutofill(productSelectSelector, priceInputSelector) {
    $(productSelectSelector).on('change', function() {
        const productId = $(this).val();
        
        if (productId) {
            $.ajax({
                url: `/erp/api/product/${productId}/price/`,
                success: function(data) {
                    if (data.success) {
                        $(priceInputSelector).val(data.selling_price);
                    }
                }
            });
        }
    });
}

// Initialize autocomplete for formset rows (dynamic forms)
function initFormsetAutocomplete(containerSelector, options) {
    const container = $(containerSelector);
    
    // Initialize existing rows
    container.find('.formset-row').each(function() {
        initRowAutocomplete($(this), options);
    });
    
    // Watch for new rows
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if ($(node).hasClass('formset-row')) {
                    initRowAutocomplete($(node), options);
                }
            });
        });
    });
    
    observer.observe(container[0], { childList: true });
}

// Initialize autocomplete for a single formset row
function initRowAutocomplete(row, options) {
    const productSelect = row.find('select[name*="product"]');
    
    if (productSelect.length && !productSelect.data('autocomplete-init')) {
        productSelect.data('autocomplete-init', true);
        
        // Initialize Select2
        productSelect.select2({
            ajax: {
                url: '/erp/api/autocomplete/products/',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        q: params.term,
                        page: params.page || 1
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results,
                        pagination: {
                            more: data.pagination.more
                        }
                    };
                },
                cache: true
            },
            placeholder: 'Select Product',
            allowClear: true,
            minimumInputLength: 0,
            width: '100%',
            dropdownParent: row
        });
        
        // Auto-fill price if enabled
        if (options && options.autoFillPrice) {
            productSelect.on('change', function() {
                const productId = $(this).val();
                const priceInput = row.find('input[name*="unit_price"]');
                
                if (productId && priceInput.length) {
                    $.ajax({
                        url: `/erp/api/product/${productId}/price/`,
                        success: function(data) {
                            if (data.success) {
                                // Use selling_price for sales, purchase_price for purchases
                                const price = options.usePurchasePrice ? 
                                    data.purchase_price : data.selling_price;
                                priceInput.val(price);
                            }
                        }
                    });
                }
            });
        }
    }
}

// Quick initialization functions for common use cases
window.ERPFormAutocomplete = {
    // Initialize customer autocomplete
    initCustomer: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/customers/', 'Select Customer');
    },
    
    // Initialize supplier autocomplete
    initSupplier: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/suppliers/', 'Select Supplier');
    },
    
    // Initialize salesperson autocomplete
    initSalesperson: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/salespersons/', 'Select Salesperson');
    },
    
    // Initialize product autocomplete
    initProduct: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/products/', 'Select Product');
    },
    
    // Initialize warehouse autocomplete
    initWarehouse: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/warehouses/', 'Select Warehouse');
    },
    
    // Initialize category autocomplete
    initCategory: function(selector) {
        initAutocomplete(selector, '/erp/api/autocomplete/categories/', 'Select Category');
    },
    
    // Initialize product with price auto-fill
    initProductWithPrice: function(productSelector, priceSelector) {
        initAutocomplete(productSelector, '/erp/api/autocomplete/products/', 'Select Product');
        initProductPriceAutofill(productSelector, priceSelector);
    },
    
    // Initialize formset with product autocomplete and price auto-fill
    initFormset: function(containerSelector, options) {
        initFormsetAutocomplete(containerSelector, options || { autoFillPrice: true });
    }
};
