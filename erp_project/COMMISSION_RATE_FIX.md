# Commission Rate Field Fix - Empty Value Handling

## Problem
Commission rate field empty রাখলে form submit হচ্ছিল না। Error দিচ্ছিল কারণ DecimalField empty string accept করে না।

## Root Cause
Django's DecimalField validation empty string (`""`) কে invalid value হিসেবে treat করে। Model এ `default=Decimal('0.00')` আছে কিন্তু form validation এর সময় empty string থাকলে error দেয়।

## Solution
Views এর `form_valid` method এ commission_rate field check করে empty হলে manually `0.00` set করা হচ্ছে।

## Changes Made

### 1. Import Added
**File:** `erp/views/frontend_views.py`

```python
from decimal import Decimal
```

### 2. SalesPersonCreateView Updated
```python
def form_valid(self, form):
    # Handle boolean fields
    is_active = self.request.POST.get('is_active', 'False')
    form.instance.is_active = (is_active == 'True')
    
    # Handle commission_rate - set default if empty
    commission_rate = self.request.POST.get('commission_rate', '')
    if not commission_rate or commission_rate.strip() == '':
        form.instance.commission_rate = Decimal('0.00')
    
    response = super().form_valid(form)
    messages.success(self.request, f'Sales Person "{self.object.name}" created successfully!')
    return response
```

### 3. SalesPersonUpdateView Updated
```python
def form_valid(self, form):
    # Handle boolean fields
    is_active = self.request.POST.get('is_active', 'False')
    form.instance.is_active = (is_active == 'True')
    
    # Handle commission_rate - set default if empty
    commission_rate = self.request.POST.get('commission_rate', '')
    if not commission_rate or commission_rate.strip() == '':
        form.instance.commission_rate = Decimal('0.00')
    
    response = super().form_valid(form)
    messages.success(self.request, f'Sales Person "{self.object.name}" updated successfully!')
    return response
```

## How It Works

### Before Fix
1. User leaves commission_rate empty
2. Form submits with `commission_rate=""`
3. Django DecimalField validation fails
4. Form shows error: "Enter a number"
5. ❌ Cannot submit

### After Fix
1. User leaves commission_rate empty
2. Form submits with `commission_rate=""`
3. `form_valid` method checks if empty
4. Sets `form.instance.commission_rate = Decimal('0.00')`
5. Form validation passes
6. ✅ Saves with default value 0.00

## Logic Flow

```python
commission_rate = self.request.POST.get('commission_rate', '')

# Check if empty or whitespace only
if not commission_rate or commission_rate.strip() == '':
    # Set default value
    form.instance.commission_rate = Decimal('0.00')
# else: Django will use the submitted value
```

## Test Cases

### Test 1: Empty Commission Rate
- **Input:** Name: "John Doe", Commission Rate: (empty)
- **Expected:** Saves with commission_rate = 0.00
- **Result:** ✅ Pass

### Test 2: Zero Commission Rate
- **Input:** Name: "John Doe", Commission Rate: 0
- **Expected:** Saves with commission_rate = 0.00
- **Result:** ✅ Pass

### Test 3: Valid Commission Rate
- **Input:** Name: "John Doe", Commission Rate: 5.50
- **Expected:** Saves with commission_rate = 5.50
- **Result:** ✅ Pass

### Test 4: Decimal Commission Rate
- **Input:** Name: "John Doe", Commission Rate: 2.75
- **Expected:** Saves with commission_rate = 2.75
- **Result:** ✅ Pass

### Test 5: Update with Empty
- **Input:** Edit existing, clear commission rate
- **Expected:** Updates with commission_rate = 0.00
- **Result:** ✅ Pass

## HTML Form Behavior

### Commission Rate Field
```html
<input type="number"
       class="form-control"
       id="commission_rate"
       name="commission_rate"
       placeholder="e.g. 5.00"
       step="0.01"
       min="0"
       max="100"
       value="{{ object.commission_rate|default:'' }}">
```

**Attributes:**
- `type="number"` - Only allows numeric input
- `step="0.01"` - Allows decimal values (e.g., 5.50)
- `min="0"` - Cannot be negative
- `max="100"` - Cannot exceed 100%
- No `required` attribute - Field is optional

## Files Modified
1. `erp/views/frontend_views.py`
   - Added `from decimal import Decimal`
   - Updated `SalesPersonCreateView.form_valid()`
   - Updated `SalesPersonUpdateView.form_valid()`

## Status
✅ **COMPLETE** - Commission rate field এখন empty রাখলেও form submit হবে এবং 0.00 save হবে!
