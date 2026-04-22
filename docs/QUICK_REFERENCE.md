# Quick Reference - UI Design Components

## Overview Page Template

### Basic Structure
```html
{% extends "auth_tenants/base.html" %}
{% block title %}Module Name{% endblock %}
{% block page_title %}Module Name{% endblock %}

{% block content %}
<div class="w-full min-w-0 max-w-full space-y-5 px-1 py-2 md:px-2 md:py-3">
  <div class="inv-list-shell sm:p-1.5">
    <div class="inv-list-card">
      <!-- Header -->
      <!-- Stats Grid -->
      <!-- Quick Actions -->
      <!-- Recent Activity -->
    </div>
  </div>
</div>
{% endblock %}
```

### Header
```html
<div class="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 bg-card px-4 py-4">
  <div>
    <h2 class="text-xl font-bold text-foreground">Module Name overview</h2>
    <p class="text-sm text-muted-foreground mt-0.5">Brief description.</p>
  </div>
</div>
```

### Stats Grid (5 columns)
```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
  <div class="simple-card rounded-xl border border-border p-4">
    <p class="text-xs text-muted-foreground">Label</p>
    <p class="text-xl font-semibold">{{ value }}</p>
  </div>
  <!-- Repeat for each stat -->
</div>
```

### Quick Actions
```html
<div class="card-actions card-actions--flush">
  <a href="..." class="card-act card-act--muted card-act--lg">
    <i data-lucide="icon-name" class="h-4 w-4"></i>
    Action Label
  </a>
  <!-- Repeat for each action -->
</div>
```

### Recent Activity
```html
<div class="inv-list-shell sm:p-1.5">
  <div class="inv-list-card">
    <div class="border-b border-border/80 bg-card px-4 py-4">
      <h3 class="text-lg font-semibold text-foreground">Recent Activity</h3>
      <p class="text-sm text-muted-foreground mt-0.5">Latest updates.</p>
    </div>
    <div class="p-4 md:p-5">
      <div class="space-y-3">
        {% for item in items %}
          <div class="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/30 transition-colors">
            <div class="flex items-center gap-3">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <i data-lucide="icon" class="h-5 w-5"></i>
              </div>
              <div>
                <p class="text-sm font-medium text-foreground">{{ item.title }}</p>
                <p class="text-xs text-muted-foreground">{{ item.description }}</p>
              </div>
            </div>
            <p class="text-xs text-muted-foreground">{{ item.date }}</p>
          </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>
```

---

## Guide Page Template

### Basic Structure
```html
{% extends "auth_tenants/base.html" %}
{% block title %}Guide Title{% endblock %}
{% block page_title %}Module · বাংলা গাইড{% endblock %}

{% block content %}
<div class="w-full px-1 md:px-2 space-y-5">
  <div class="simple-card rounded-xl border border-border bg-card shadow-card overflow-hidden">
    <!-- Header -->
    <div class="p-5 space-y-6">
      <!-- Sections -->
    </div>
  </div>
</div>
{% endblock %}
```

### Header with Back Button
```html
<div class="flex items-center justify-between gap-3 border-b border-border bg-muted/20 px-5 py-4">
  <div>
    <h2 class="text-lg font-semibold text-foreground">Page Title</h2>
    <p class="text-xs text-muted-foreground mt-0.5">Brief description.</p>
  </div>
  <a href="{% url 'app:dashboard' %}" class="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent">
    <i data-lucide="arrow-left" class="h-4 w-4"></i>
    Back
  </a>
</div>
```

### Introduction Section
```html
<section class="rounded-xl border border-border bg-background p-4">
  <p class="text-xs font-semibold uppercase tracking-wide text-primary">গল্পের চরিত্র</p>
  <p class="mt-2 text-sm text-muted-foreground leading-6">
    Story introduction with <strong class="text-foreground">character names</strong>.
  </p>
</section>
```

### Checklist Section
```html
<section class="rounded-xl border border-border bg-background p-4">
  <h3 class="text-base font-semibold text-foreground">Part A: Title</h3>
  <div class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
    <div class="rounded-lg border border-border p-3">
      <p class="font-semibold text-foreground">1) Item Title</p>
      <p class="mt-1">Description text.</p>
    </div>
    <!-- Repeat for each item -->
  </div>
</section>
```

### List Section
```html
<section class="rounded-xl border border-border bg-background p-4">
  <h3 class="text-base font-semibold text-foreground">Part B: Title</h3>
  <ul class="mt-3 space-y-2 text-sm text-muted-foreground">
    <li>
      <strong class="text-foreground">Bold label</strong>: Description text.
    </li>
    <!-- Repeat for each item -->
  </ul>
</section>
```

### Ordered List Section
```html
<section class="rounded-xl border border-border bg-background p-4">
  <h3 class="text-base font-semibold text-foreground">Part C: Title</h3>
  <ol class="mt-3 space-y-3 text-sm text-muted-foreground">
    <li>
      <strong class="text-foreground">1) Step title</strong> — Description text.
    </li>
    <!-- Repeat for each step -->
  </ol>
</section>
```

### Table Section
```html
<section class="rounded-xl border border-border bg-background p-4">
  <h3 class="text-base font-semibold text-foreground">Part D: Title</h3>
  <div class="ui-table-wrap overflow-x-auto rounded-lg border border-border mt-3">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border bg-muted/40">
          <th class="px-3 py-2 text-left">Column 1</th>
          <th class="px-3 py-2 text-left">Column 2</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border">
        <tr>
          <td class="px-3 py-2">Data 1</td>
          <td class="px-3 py-2">Data 2</td>
        </tr>
      </tbody>
    </table>
  </div>
</section>
```

### Highlight Section
```html
<section class="rounded-xl border border-primary/20 bg-primary/5 p-4">
  <h3 class="text-base font-semibold text-foreground">Important Title</h3>
  <p class="mt-2 text-sm text-muted-foreground leading-6">
    Important content highlighted.
  </p>
</section>
```

### Call-to-Action Buttons
```html
<section class="flex flex-wrap gap-3 pt-1">
  <a href="..." class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90">
    Primary Action
  </a>
  <a href="..." class="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent">
    Secondary Action
  </a>
</section>
```

---

## Common Tailwind Classes

### Colors
- `text-foreground` - Main text
- `text-muted-foreground` - Secondary text
- `bg-card` - Card background
- `bg-background` - Page background
- `bg-primary` - Primary color
- `bg-primary/10` - Primary with 10% opacity
- `border-border` - Border color

### Sizing
- `text-xs` - 12px
- `text-sm` - 14px
- `text-base` - 16px
- `text-lg` - 18px
- `text-xl` - 20px

### Spacing
- `p-3` - 0.75rem padding
- `p-4` - 1rem padding
- `p-5` - 1.25rem padding
- `gap-2` - 0.5rem gap
- `gap-3` - 0.75rem gap
- `gap-4` - 1rem gap
- `mt-1`, `mt-2`, `mt-3` - Top margin
- `space-y-2`, `space-y-3` - Vertical spacing

### Layout
- `grid grid-cols-1` - 1 column
- `sm:grid-cols-2` - 2 columns on tablet
- `lg:grid-cols-5` - 5 columns on desktop
- `flex items-center` - Flex with center alignment
- `flex-wrap` - Wrap items
- `gap-3` - Gap between items

### Borders & Shadows
- `border border-border` - Border
- `rounded-lg` - Rounded corners
- `rounded-xl` - More rounded
- `shadow-card` - Card shadow
- `overflow-hidden` - Hide overflow

### Responsive
- `px-1 md:px-2` - Padding responsive
- `py-2 md:py-3` - Padding responsive
- `w-full` - Full width
- `min-w-0` - Min width 0
- `max-w-full` - Max width full

### Hover & Transitions
- `hover:opacity-90` - Hover opacity
- `hover:bg-accent` - Hover background
- `transition-colors` - Smooth color transition

---

## Icons (Lucide)

### Common Icons
```html
<i data-lucide="building-2" class="h-4 w-4"></i>      <!-- Building -->
<i data-lucide="users" class="h-4 w-4"></i>           <!-- Users -->
<i data-lucide="file-text" class="h-4 w-4"></i>       <!-- Document -->
<i data-lucide="credit-card" class="h-4 w-4"></i>     <!-- Payment -->
<i data-lucide="help-circle" class="h-4 w-4"></i>     <!-- Help -->
<i data-lucide="arrow-left" class="h-4 w-4"></i>      <!-- Back -->
<i data-lucide="check-circle" class="h-4 w-4"></i>    <!-- Success -->
<i data-lucide="calendar" class="h-4 w-4"></i>        <!-- Calendar -->
<i data-lucide="book-open" class="h-4 w-4"></i>       <!-- Book -->
<i data-lucide="user-check" class="h-4 w-4"></i>      <!-- User check -->
<i data-lucide="award" class="h-4 w-4"></i>           <!-- Award -->
<i data-lucide="sliders-horizontal" class="h-4 w-4"></i> <!-- Settings -->
<i data-lucide="arrow-up-from-line" class="h-4 w-4"></i> <!-- Up arrow -->
<i data-lucide="arrow-right-left" class="h-4 w-4"></i>   <!-- Transfer -->
<i data-lucide="boxes" class="h-4 w-4"></i>           <!-- Boxes -->
<i data-lucide="list-tree" class="h-4 w-4"></i>       <!-- List -->
```

---

## View Examples

### Dashboard View
```python
from django.shortcuts import render
from .models import Property, Tenant, Payment

def dashboard(request):
    context = {
        'total_properties': Property.objects.count(),
        'occupied_properties': Property.objects.filter(status='OCCUPIED').count(),
        'vacant_properties': Property.objects.filter(status='VACANT').count(),
        'total_tenants': Tenant.objects.count(),
        'due_amount': calculate_due_amount(),
        'recent_payments': Payment.objects.order_by('-payment_date')[:5],
    }
    return render(request, 'rental_management/dashboard.html', context)

def guide(request):
    return render(request, 'rental_management/rental_guide_bn.html')
```

### URL Configuration
```python
from django.urls import path
from . import views

app_name = 'rental'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('guide/', views.guide, name='guide'),
    path('properties/', views.property_list, name='property_list'),
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('agreements/', views.agreement_list, name='agreement_list'),
    path('payments/', views.payment_list, name='payment_list'),
]
```

---

## Responsive Breakpoints

### Mobile First
- **Mobile**: 0px - 640px (default)
- **Tablet**: 640px+ (sm:)
- **Desktop**: 1024px+ (lg:)

### Examples
```html
<!-- 1 column on mobile, 2 on tablet, 5 on desktop -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
  <!-- Items -->
</div>

<!-- Padding responsive -->
<div class="px-1 md:px-2 py-2 md:py-3">
  <!-- Content -->
</div>

<!-- Display responsive -->
<div class="hidden sm:block">
  <!-- Show on tablet and up -->
</div>
```

---

## Dark Mode

### Automatic
- Dark mode is automatically applied based on system preference
- Users can toggle in settings
- All colors are optimized for both modes

### Testing
- Open DevTools
- Toggle dark mode in system settings
- Or use browser dark mode toggle

---

## Accessibility

### Best Practices
- Use semantic HTML (h1, h2, p, ul, ol, etc.)
- Include alt text for images
- Use proper heading hierarchy
- Ensure color contrast ratios
- Use aria-labels where needed

### Example
```html
<button aria-label="Close menu">
  <i data-lucide="x" class="h-4 w-4"></i>
</button>
```

---

## Performance Tips

1. **Use Tailwind classes** - Don't write custom CSS
2. **Minimize DOM elements** - Keep HTML clean
3. **Lazy load images** - Use loading="lazy"
4. **Optimize images** - Use WebP format
5. **Cache templates** - Use Django template caching

---

## Common Issues & Solutions

### Issue: Grid not responsive
**Solution**: Use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-5`

### Issue: Text too small on mobile
**Solution**: Use `text-xs sm:text-sm` for responsive text

### Issue: Padding too large on mobile
**Solution**: Use `px-1 md:px-2` for responsive padding

### Issue: Dark mode not working
**Solution**: Check if `.dark` class is on `<html>` element

### Issue: Icons not showing
**Solution**: Make sure Lucide script is loaded in base.html

---

## Resources

- **Tailwind CSS**: https://tailwindcss.com/docs
- **Lucide Icons**: https://lucide.dev/
- **Color System**: See `auth_tenants/templates/auth_tenants/base.html`
- **Design Guide**: See `docs/UI_DESIGN_GUIDE.md`

---

## Quick Copy-Paste Templates

### Minimal Overview Page
```html
{% extends "auth_tenants/base.html" %}
{% block title %}Module{% endblock %}
{% block page_title %}Module{% endblock %}

{% block content %}
<div class="w-full min-w-0 max-w-full space-y-5 px-1 py-2 md:px-2 md:py-3">
  <div class="inv-list-shell sm:p-1.5">
    <div class="inv-list-card">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 bg-card px-4 py-4">
        <div>
          <h2 class="text-xl font-bold text-foreground">Module overview</h2>
          <p class="text-sm text-muted-foreground mt-0.5">Description.</p>
        </div>
      </div>
      <div class="p-4 md:p-5 space-y-5">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div class="simple-card rounded-xl border border-border p-4">
            <p class="text-xs text-muted-foreground">Stat 1</p>
            <p class="text-xl font-semibold">{{ stat1 }}</p>
          </div>
        </div>
        <div class="card-actions card-actions--flush">
          <a href="..." class="card-act card-act--muted card-act--lg">Action</a>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

### Minimal Guide Page
```html
{% extends "auth_tenants/base.html" %}
{% block title %}Guide{% endblock %}
{% block page_title %}Module · Guide{% endblock %}

{% block content %}
<div class="w-full px-1 md:px-2 space-y-5">
  <div class="simple-card rounded-xl border border-border bg-card shadow-card overflow-hidden">
    <div class="flex items-center justify-between gap-3 border-b border-border bg-muted/20 px-5 py-4">
      <div>
        <h2 class="text-lg font-semibold text-foreground">Guide Title</h2>
        <p class="text-xs text-muted-foreground mt-0.5">Description.</p>
      </div>
      <a href="..." class="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent">
        <i data-lucide="arrow-left" class="h-4 w-4"></i>
        Back
      </a>
    </div>
    <div class="p-5 space-y-6">
      <section class="rounded-xl border border-border bg-background p-4">
        <h3 class="text-base font-semibold text-foreground">Section Title</h3>
        <p class="mt-2 text-sm text-muted-foreground leading-6">Content here.</p>
      </section>
    </div>
  </div>
</div>
{% endblock %}
```

---

**Last Updated**: April 2026
**Version**: 1.0
