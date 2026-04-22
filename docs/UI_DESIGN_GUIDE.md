# UI Design Guide - Premium Overview & Guide Pages

## Overview

এই ডকুমেন্টে সব apps এর overview page এবং guide page এর জন্য একটি unified, premium design pattern দেওয়া হয়েছে। এটি Finance, POS, Inventory, Rental Management এবং School Management এ একই ডিজাইন ব্যবহার করে।

---

## Design Philosophy

### 1. **Consistency Across All Apps**
- সব apps এ একই color scheme, typography, spacing ব্যবহার করা হয়
- একই component patterns (cards, buttons, sections) ব্যবহার করা হয়
- একই responsive behavior সব devices এ

### 2. **Premium & Professional Look**
- Clean, minimal design
- Proper whitespace এবং padding
- Subtle shadows এবং borders
- Smooth transitions এবং hover effects

### 3. **User-Friendly Navigation**
- Clear hierarchy এবং visual structure
- Easy-to-scan layouts
- Quick action buttons
- Contextual help এবং guides

---

## Overview Page Structure

### Header Section
```html
<div class="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 bg-card px-4 py-4">
  <div>
    <h2 class="text-xl font-bold text-foreground">Module Name overview</h2>
    <p class="text-sm text-muted-foreground mt-0.5">Brief description of what this module does.</p>
  </div>
</div>
```

**Features:**
- Bold title (text-xl font-bold)
- Subtle description (text-sm text-muted-foreground)
- Border-bottom for visual separation
- Responsive padding (px-4 py-4)

### Stats Grid
```html
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
  <div class="simple-card rounded-xl border border-border p-4">
    <p class="text-xs text-muted-foreground">Label</p>
    <p class="text-xl font-semibold">{{ value }}</p>
  </div>
  <!-- More cards... -->
</div>
```

**Features:**
- Responsive grid (1 col mobile, 2 cols tablet, 5 cols desktop)
- Simple cards with subtle borders
- Small label text (text-xs)
- Large value text (text-xl font-semibold)
- Consistent padding (p-4)

### Quick Actions
```html
<div class="card-actions card-actions--flush">
  <a href="..." class="card-act card-act--muted card-act--lg">
    <i data-lucide="icon-name" class="h-4 w-4"></i>
    Action Label
  </a>
  <!-- More actions... -->
</div>
```

**Features:**
- Horizontal scrollable on mobile
- Icon + text combination
- Muted styling (not too prominent)
- Large padding for easy clicking

### Recent Activity Section
```html
<div class="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/30 transition-colors">
  <div class="flex items-center gap-3">
    <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
      <i data-lucide="icon" class="h-5 w-5"></i>
    </div>
    <div>
      <p class="text-sm font-medium text-foreground">Title</p>
      <p class="text-xs text-muted-foreground">Description</p>
    </div>
  </div>
  <p class="text-xs text-muted-foreground">Date</p>
</div>
```

**Features:**
- Icon with colored background
- Title + description
- Date on the right
- Hover effect for interactivity

---

## Guide Page Structure

### Header with Back Button
```html
<div class="flex items-center justify-between gap-3 border-b border-border bg-muted/20 px-5 py-4">
  <div>
    <h2 class="text-lg font-semibold text-foreground">Page Title</h2>
    <p class="text-xs text-muted-foreground mt-0.5">Brief description.</p>
  </div>
  <a href="..." class="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent">
    <i data-lucide="arrow-left" class="h-4 w-4"></i>
    Back
  </a>
</div>
```

### Content Sections
```html
<section class="rounded-xl border border-border bg-background p-4">
  <p class="text-xs font-semibold uppercase tracking-wide text-primary">Section Label</p>
  <p class="mt-2 text-sm text-muted-foreground leading-6">
    Content text with <strong class="text-foreground">bold highlights</strong>.
  </p>
</section>
```

**Features:**
- Rounded corners (rounded-xl)
- Subtle border
- Uppercase label (text-xs font-semibold uppercase)
- Primary color for labels
- Proper line-height for readability (leading-6)

### Lists & Tables
```html
<ul class="mt-3 space-y-2 text-sm text-muted-foreground">
  <li>- <strong class="text-foreground">Bold label</strong>: Description text</li>
</ul>
```

**Features:**
- Consistent spacing (space-y-2)
- Bold labels for emphasis
- Muted text for descriptions
- Bullet points for clarity

### Grid Sections
```html
<div class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-muted-foreground">
  <div class="rounded-lg border border-border p-3">
    <p class="font-semibold text-foreground">Title</p>
    <p class="mt-1">Description</p>
  </div>
</div>
```

**Features:**
- Responsive grid (1 col mobile, 2 cols desktop)
- Consistent gap (gap-4)
- Bordered boxes
- Bold titles

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

**Features:**
- Primary button (filled background)
- Secondary buttons (bordered)
- Consistent sizing
- Hover effects
- Flex wrap for responsive layout

### Highlight Section
```html
<section class="rounded-xl border border-primary/20 bg-primary/5 p-4">
  <h3 class="text-base font-semibold text-foreground">Important Title</h3>
  <p class="mt-2 text-sm text-muted-foreground leading-6">
    Important content highlighted with primary color.
  </p>
</section>
```

**Features:**
- Primary color border (border-primary/20)
- Primary color background (bg-primary/5)
- Subtle but noticeable
- Good for important information

---

## Color System

### Light Mode
```css
--background: 0 0% 100%;           /* White */
--foreground: 222.2 84% 4.9%;      /* Dark blue-gray */
--card: 0 0% 100%;                 /* White */
--primary: 222.2 47.4% 11.2%;      /* Dark blue */
--muted: 210 40% 96.1%;            /* Light gray */
--border: 214.3 31.8% 91.4%;       /* Light border */
```

### Dark Mode
```css
--background: 240 6% 3.9%;         /* Almost black */
--foreground: 0 0% 98%;            /* Almost white */
--card: 240 5.9% 10%;              /* Dark gray */
--primary: 0 0% 98%;               /* White */
--muted: 240 4.8% 12%;             /* Medium gray */
--border: 240 5.3% 15.9%;          /* Dark border */
```

---

## Typography

### Font Family
- **Font**: Inter (system-ui, sans-serif fallback)
- **Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

### Font Sizes
- **Headings**: text-xl (20px), text-lg (18px), text-base (16px)
- **Body**: text-sm (14px)
- **Small**: text-xs (12px)

### Line Heights
- **Normal**: leading-6 (1.5rem) for body text
- **Tight**: default for headings

---

## Spacing System

### Padding
- **Small**: p-3 (0.75rem)
- **Medium**: p-4 (1rem)
- **Large**: p-5 (1.25rem)

### Gaps
- **Small**: gap-2 (0.5rem)
- **Medium**: gap-3 (0.75rem)
- **Large**: gap-4 (1rem)

### Margins
- **Top**: mt-1, mt-2, mt-3, mt-4, mt-5
- **Bottom**: mb-1, mb-2, mb-3, mb-4, mb-5

---

## Responsive Breakpoints

### Mobile First
- **Mobile**: 0px - 640px (default)
- **Tablet**: 640px+ (sm:)
- **Desktop**: 1024px+ (lg:)

### Grid Patterns
- **1 Column**: Mobile
- **2 Columns**: Tablet (sm:grid-cols-2)
- **3-5 Columns**: Desktop (lg:grid-cols-3, lg:grid-cols-5)

---

## Component Patterns

### Card Component
```html
<div class="simple-card rounded-xl border border-border p-4">
  <!-- Content -->
</div>
```

### Button Component
```html
<!-- Primary -->
<a class="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90">
  Action
</a>

<!-- Secondary -->
<a class="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent">
  Action
</a>
```

### Icon Component
```html
<i data-lucide="icon-name" class="h-4 w-4"></i>
```

### Badge Component
```html
<span class="inline-flex items-center rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
  Badge
</span>
```

---

## Implementation Checklist

### For Overview Pages
- [ ] Header with title and description
- [ ] Stats grid (responsive)
- [ ] Quick action buttons
- [ ] Recent activity section
- [ ] Consistent styling with other apps
- [ ] Mobile responsive
- [ ] Dark mode support

### For Guide Pages
- [ ] Header with back button
- [ ] Story/character introduction
- [ ] Multiple sections with clear hierarchy
- [ ] Lists and tables
- [ ] Grid layouts for related items
- [ ] Highlight sections for important info
- [ ] Call-to-action buttons at the end
- [ ] Mobile responsive
- [ ] Dark mode support

---

## Best Practices

### 1. **Consistency**
- Use the same component patterns across all pages
- Maintain consistent spacing and padding
- Use the same color palette

### 2. **Readability**
- Use proper contrast ratios
- Maintain good line-height (leading-6)
- Use bold for emphasis, not color alone

### 3. **Accessibility**
- Use semantic HTML
- Include alt text for images
- Use proper heading hierarchy
- Ensure keyboard navigation works

### 4. **Performance**
- Use Tailwind CSS classes (no custom CSS)
- Minimize DOM elements
- Use lazy loading for images
- Optimize for mobile first

### 5. **User Experience**
- Clear visual hierarchy
- Obvious call-to-action buttons
- Helpful error messages
- Smooth transitions and animations

---

## Examples

### Finance Overview Page
- Stats: Accounts, Journals, Ledger rows, AP posted, AR posted
- Actions: Chart of accounts, Journal entries, Trial balance, P&L, Balance sheet

### Inventory Overview Page
- Actions: Stock adjustments, Goods issues, Inventory transfers, Warehouse stock, Stock transactions
- Each action has icon, title, and description

### Rental Management Overview Page
- Stats: Total properties, Occupied, Vacant, Total tenants, Due amount
- Actions: Properties, Tenants, Agreements, Payments, Guide
- Recent activity: Latest payments

### School Management Overview Page
- Stats: Total students, Total teachers, Total classes, Due fees, Avg attendance
- Actions: Students, Teachers, Attendance, Exams, Guide
- Recent activity: Fee payments and exam results

---

## Future Enhancements

1. **Charts & Graphs**: Add visual data representation
2. **Filters**: Add filtering options for recent activity
3. **Export**: Add export to PDF/Excel functionality
4. **Notifications**: Add notification badges
5. **Customization**: Allow users to customize dashboard widgets

---

## Support

For questions or suggestions about the UI design, please refer to:
- `ui/index.html` - Premium design reference
- `auth_tenants/templates/auth_tenants/base.html` - Base template
- Individual app guide pages for specific examples
