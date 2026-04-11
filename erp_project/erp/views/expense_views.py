from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.admin import site
from django.utils import timezone
from decimal import Decimal

from ..models import ChartOfAccounts, JournalEntry, JournalEntryLine


@login_required
def simple_expense_entry(request):
    """Simple expense entry form using existing Chart of Accounts"""
    
    if request.method == 'POST':
        try:
            expense_account_id = request.POST.get('expense_account')
            amount = Decimal(request.POST.get('amount', '0'))
            description = request.POST.get('description', '')
            
            if not expense_account_id or amount <= 0 or not description:
                messages.error(request, 'Please fill in all required fields')
                return redirect('erp:simple-expense-entry')
            
            # Get accounts
            expense_account = ChartOfAccounts.objects.get(id=expense_account_id)
            
            # Get cash account
            cash_account = ChartOfAccounts.objects.filter(
                account_code__in=['1001', '1000', 'CASH'],
                is_active=True
            ).first()
            
            if not cash_account:
                cash_account = ChartOfAccounts.objects.filter(
                    account_type__type_category__in=['asset', 'assets'],
                    is_active=True
                ).first()
            
            if not cash_account:
                messages.error(request, 'No cash account found')
                return redirect('erp:simple-expense-entry')
            
            # Create journal entry
            journal_entry = JournalEntry.objects.create(
                entry_date=timezone.now().date(),
                reference="Simple Expense Entry",
                status='posted',
                notes=f"Simple expense: {description}",
            )
            
            # Create journal entry lines
            # Debit: Expense Account
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=expense_account,
                description=description,
                debit=amount,
                credit=Decimal('0.00')
            )
            
            # Credit: Cash Account
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=cash_account,
                description=f"Cash payment for {description}",
                debit=Decimal('0.00'),
                credit=amount
            )
            
            # Update totals
            journal_entry.calculate_totals()
            
            messages.success(request, f'✅ Expense entry created successfully! Journal Entry: {journal_entry.entry_number}')
            return redirect('erp:simple-expense-entry')
            
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('erp:simple-expense-entry')
    
    # GET request - show form
    # Filter only expense type accounts
    expense_accounts = ChartOfAccounts.objects.filter(
        account_type__type_category='expense',
        is_active=True
    ).order_by('account_name')
    
    # Get cash account info
    cash_account = ChartOfAccounts.objects.filter(
        account_code__in=['1001', '1000', 'CASH'],
        is_active=True
    ).first()
    
    if not cash_account:
        cash_account = ChartOfAccounts.objects.filter(
            account_type__type_category__in=['asset', 'assets'],
            is_active=True
        ).first()
    
    context = {
        'title': '💰 Simple Expense Entry',
        'expense_accounts': expense_accounts,
        'cash_account': cash_account,
    }
    
    # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
    context.update(site.each_context(request))
    
    return render(request, 'admin/erp/expense/simple_expense_entry.html', context)


@login_required
def expense_list(request):
    """List recent expense entries"""
    
    # Get recent journal entries that look like expenses
    recent_entries = JournalEntry.objects.filter(
        reference__icontains='expense'
    ).order_by('-created_at')[:20]
    
    context = {
        'title': 'Recent Expense Entries',
        'recent_entries': recent_entries,
    }
    
    # ⭐ REQUIRED: Admin context for Unfold sidebar and styling
    context.update(site.each_context(request))
    
    return render(request, 'admin/erp/expense/expense_list.html', context)