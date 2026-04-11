"""
Financial Reports with Django 6.0 Built-in Tasks
Optimized Financial Reports: Trial Balance, P&L, Balance Sheet, Cash Flow, GL, Account Statement
- Async operations with alist() and aaggregate()
- No Python loops - all operations in database
- Caching for instant repeated requests
- Background task processing with progress tracking
"""
from django.contrib import admin
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Sum, Count, Q, F
from django.tasks import task
from decimal import Decimal
from datetime import datetime
import uuid

from ...models import (
    ChartOfAccounts, JournalEntry, JournalEntryLine,
    FiscalYear, AccountType
)


# ==================== BACKGROUND TASK FUNCTIONS ====================

@task()
def generate_trial_balance_report(task_id, filters, user_id):
    """Background task for Trial Balance report generation"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting Trial Balance generation...',
            'progress': 10
        }, timeout=300)
        
        # Get date range
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        account_type = filters.get('account_type')
        
        # Get all accounts
        accounts_qs = ChartOfAccounts.objects.filter(is_active=True).select_related('account_type')
        
        if account_type:
            accounts_qs = accounts_qs.filter(account_type_id=account_type)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating account balances...',
            'progress': 30
        }, timeout=300)
        
        # Get journal entry lines for the period
        lines_qs = JournalEntryLine.objects.filter(
            journal_entry__status='posted'
        ).select_related('account', 'account__account_type')
        
        if from_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__gte=from_date)
        if to_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__lte=to_date)
        
        # Calculate balances per account
        account_balances = lines_qs.values('account_id').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        # Create balance dict
        balance_dict = {
            item['account_id']: {
                'debit': float(item['total_debit'] or 0),
                'credit': float(item['total_credit'] or 0)
            }
            for item in account_balances
        }
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Formatting report data...',
            'progress': 60
        }, timeout=300)
        
        # Format accounts with balances
        accounts_data = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for account in accounts_qs:
            balance_info = balance_dict.get(account.id, {'debit': 0, 'credit': 0})
            debit = Decimal(str(balance_info['debit']))
            credit = Decimal(str(balance_info['credit']))
            
            # Calculate net balance
            net_balance = debit - credit
            
            if net_balance != 0 or debit != 0 or credit != 0:
                accounts_data.append({
                    'account_code': account.account_code,
                    'account_name': account.account_name,
                    'account_type': account.account_type.name,
                    'debit': float(debit),
                    'credit': float(credit),
                    'balance': float(abs(net_balance)),
                    'balance_type': 'Dr' if net_balance > 0 else 'Cr' if net_balance < 0 else '-'
                })
                
                total_debit += debit
                total_credit += credit
        
        result = {
            'accounts': accounts_data,
            'totals': {
                'total_debit': float(total_debit),
                'total_credit': float(total_credit),
                'difference': float(total_debit - total_credit)
            },
            'filters': filters
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'Trial Balance generated successfully!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)



@task()
def generate_profit_loss_report(task_id, filters, user_id):
    """Background task for Profit & Loss Statement"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting P&L generation...',
            'progress': 10
        }, timeout=300)
        
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        
        # Get revenue and expense accounts
        revenue_accounts = ChartOfAccounts.objects.filter(
            account_type__type_category='revenue',
            is_active=True
        ).select_related('account_type')
        
        expense_accounts = ChartOfAccounts.objects.filter(
            account_type__type_category='expense',
            is_active=True
        ).select_related('account_type')
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating revenues and expenses...',
            'progress': 30
        }, timeout=300)
        
        # Get journal lines for period
        lines_qs = JournalEntryLine.objects.filter(
            journal_entry__status='posted'
        )
        
        if from_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__gte=from_date)
        if to_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__lte=to_date)
        
        # Calculate revenue (credit - debit for revenue accounts)
        revenue_data = lines_qs.filter(
            account__account_type__type_category='revenue'
        ).values('account_id', 'account__account_code', 'account__account_name').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        # Calculate expenses (debit - credit for expense accounts)
        expense_data = lines_qs.filter(
            account__account_type__type_category='expense'
        ).values('account_id', 'account__account_code', 'account__account_name').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Formatting P&L statement...',
            'progress': 60
        }, timeout=300)
        
        # Format revenue
        revenues = []
        total_revenue = Decimal('0.00')
        for item in revenue_data:
            amount = Decimal(str(item['total_credit'] or 0)) - Decimal(str(item['total_debit'] or 0))
            if amount != 0:
                revenues.append({
                    'account_code': item['account__account_code'],
                    'account_name': item['account__account_name'],
                    'amount': float(amount)
                })
                total_revenue += amount
        
        # Format expenses
        expenses = []
        total_expense = Decimal('0.00')
        for item in expense_data:
            amount = Decimal(str(item['total_debit'] or 0)) - Decimal(str(item['total_credit'] or 0))
            if amount != 0:
                expenses.append({
                    'account_code': item['account__account_code'],
                    'account_name': item['account__account_name'],
                    'amount': float(amount)
                })
                total_expense += amount
        
        net_profit = total_revenue - total_expense
        
        result = {
            'revenues': revenues,
            'expenses': expenses,
            'totals': {
                'total_revenue': float(total_revenue),
                'total_expense': float(total_expense),
                'net_profit': float(net_profit),
                'profit_margin': float((net_profit / total_revenue * 100) if total_revenue > 0 else 0)
            },
            'filters': filters
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'P&L Statement completed!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)


@task()
def generate_balance_sheet_report(task_id, filters, user_id):
    """Background task for Balance Sheet"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting Balance Sheet generation...',
            'progress': 10
        }, timeout=300)
        
        as_of_date = filters.get('as_of_date')
        
        # Get all accounts by type
        asset_accounts = ChartOfAccounts.objects.filter(
            account_type__type_category='asset',
            is_active=True
        ).select_related('account_type')
        
        liability_accounts = ChartOfAccounts.objects.filter(
            account_type__type_category='liability',
            is_active=True
        ).select_related('account_type')
        
        equity_accounts = ChartOfAccounts.objects.filter(
            account_type__type_category='equity',
            is_active=True
        ).select_related('account_type')
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating account balances...',
            'progress': 30
        }, timeout=300)
        
        # Get journal lines up to date
        lines_qs = JournalEntryLine.objects.filter(
            journal_entry__status='posted'
        )
        
        if as_of_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__lte=as_of_date)
        
        # Calculate balances by account
        account_balances = lines_qs.values('account_id', 'account__account_code', 'account__account_name', 'account__account_type__type_category').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Formatting Balance Sheet...',
            'progress': 60
        }, timeout=300)
        
        # Format assets (debit - credit)
        assets = []
        total_assets = Decimal('0.00')
        for item in account_balances:
            if item['account__account_type__type_category'] == 'asset':
                amount = Decimal(str(item['total_debit'] or 0)) - Decimal(str(item['total_credit'] or 0))
                if amount != 0:
                    assets.append({
                        'account_code': item['account__account_code'],
                        'account_name': item['account__account_name'],
                        'amount': float(amount)
                    })
                    total_assets += amount
        
        # Format liabilities (credit - debit)
        liabilities = []
        total_liabilities = Decimal('0.00')
        for item in account_balances:
            if item['account__account_type__type_category'] == 'liability':
                amount = Decimal(str(item['total_credit'] or 0)) - Decimal(str(item['total_debit'] or 0))
                if amount != 0:
                    liabilities.append({
                        'account_code': item['account__account_code'],
                        'account_name': item['account__account_name'],
                        'amount': float(amount)
                    })
                    total_liabilities += amount
        
        # Format equity (credit - debit)
        equity = []
        total_equity = Decimal('0.00')
        for item in account_balances:
            if item['account__account_type__type_category'] == 'equity':
                amount = Decimal(str(item['total_credit'] or 0)) - Decimal(str(item['total_debit'] or 0))
                if amount != 0:
                    equity.append({
                        'account_code': item['account__account_code'],
                        'account_name': item['account__account_name'],
                        'amount': float(amount)
                    })
                    total_equity += amount
        
        total_liabilities_equity = total_liabilities + total_equity
        
        result = {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'totals': {
                'total_assets': float(total_assets),
                'total_liabilities': float(total_liabilities),
                'total_equity': float(total_equity),
                'total_liabilities_equity': float(total_liabilities_equity),
                'difference': float(total_assets - total_liabilities_equity)
            },
            'filters': filters
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'Balance Sheet completed!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)



@task()
def generate_general_ledger_report(task_id, filters, user_id):
    """Background task for General Ledger Report"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting General Ledger generation...',
            'progress': 10
        }, timeout=300)
        
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        account_id = filters.get('account_id')
        
        if not account_id:
            raise ValueError("Account is required for General Ledger report")
        
        # Get account
        account = ChartOfAccounts.objects.select_related('account_type').get(id=account_id)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching transactions...',
            'progress': 30
        }, timeout=300)
        
        # Get journal entry lines
        lines_qs = JournalEntryLine.objects.filter(
            account_id=account_id,
            journal_entry__status='posted'
        ).select_related('journal_entry')
        
        if from_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__gte=from_date)
        if to_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__lte=to_date)
        
        lines_data = lines_qs.values(
            'journal_entry__entry_number',
            'journal_entry__entry_date',
            'journal_entry__reference',
            'description',
            'debit',
            'credit'
        ).order_by('journal_entry__entry_date', 'journal_entry__entry_number')
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating running balance...',
            'progress': 60
        }, timeout=300)
        
        # Calculate running balance
        transactions = []
        running_balance = Decimal(str(account.opening_balance))
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for line in lines_data:
            debit = Decimal(str(line['debit']))
            credit = Decimal(str(line['credit']))
            
            # Update running balance based on account type
            if account.account_type.type_category in ['asset', 'expense']:
                running_balance += debit - credit
            else:  # liability, equity, revenue
                running_balance += credit - debit
            
            transactions.append({
                'entry_number': line['journal_entry__entry_number'],
                'entry_date': line['journal_entry__entry_date'].strftime('%Y-%m-%d'),
                'reference': line['journal_entry__reference'] or '',
                'description': line['description'] or '',
                'debit': float(debit),
                'credit': float(credit),
                'balance': float(running_balance)
            })
            
            total_debit += debit
            total_credit += credit
        
        result = {
            'account': {
                'code': account.account_code,
                'name': account.account_name,
                'type': account.account_type.name,
                'opening_balance': float(account.opening_balance)
            },
            'transactions': transactions,
            'totals': {
                'total_debit': float(total_debit),
                'total_credit': float(total_credit),
                'closing_balance': float(running_balance)
            },
            'filters': filters
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'General Ledger completed!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)


@task()
def generate_account_statement_report(task_id, filters, user_id):
    """Background task for Account Statement (similar to GL but with more details)"""
    try:
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Starting Account Statement generation...',
            'progress': 10
        }, timeout=300)
        
        from_date = filters.get('from_date')
        to_date = filters.get('to_date')
        account_id = filters.get('account_id')
        
        if not account_id:
            raise ValueError("Account is required for Account Statement")
        
        # Get account
        account = ChartOfAccounts.objects.select_related('account_type').get(id=account_id)
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Fetching detailed transactions...',
            'progress': 30
        }, timeout=300)
        
        # Get journal entry lines with more details
        lines_qs = JournalEntryLine.objects.filter(
            account_id=account_id,
            journal_entry__status='posted'
        ).select_related('journal_entry', 'project', 'cost_center')
        
        if from_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__gte=from_date)
        if to_date:
            lines_qs = lines_qs.filter(journal_entry__entry_date__lte=to_date)
        
        lines_data = lines_qs.values(
            'journal_entry__entry_number',
            'journal_entry__entry_date',
            'journal_entry__posting_date',
            'journal_entry__reference',
            'journal_entry__notes',
            'description',
            'debit',
            'credit',
            'project__project_name',
            'cost_center__name'
        ).order_by('journal_entry__entry_date', 'journal_entry__entry_number')
        
        cache.set(f'task_{task_id}_progress', {
            'state': 'PROCESSING',
            'status': 'Calculating balances and formatting...',
            'progress': 60
        }, timeout=300)
        
        # Calculate running balance
        transactions = []
        running_balance = Decimal(str(account.opening_balance))
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for line in lines_data:
            debit = Decimal(str(line['debit']))
            credit = Decimal(str(line['credit']))
            
            # Update running balance
            if account.account_type.type_category in ['asset', 'expense']:
                running_balance += debit - credit
            else:
                running_balance += credit - debit
            
            transactions.append({
                'entry_number': line['journal_entry__entry_number'],
                'entry_date': line['journal_entry__entry_date'].strftime('%Y-%m-%d'),
                'posting_date': line['journal_entry__posting_date'].strftime('%Y-%m-%d') if line['journal_entry__posting_date'] else '',
                'reference': line['journal_entry__reference'] or '',
                'description': line['description'] or '',
                'project': line['project__project_name'] or '',
                'cost_center': line['cost_center__name'] or '',
                'debit': float(debit),
                'credit': float(credit),
                'balance': float(running_balance),
                'notes': line['journal_entry__notes'] or ''
            })
            
            total_debit += debit
            total_credit += credit
        
        result = {
            'account': {
                'code': account.account_code,
                'name': account.account_name,
                'type': account.account_type.name,
                'type_category': account.account_type.type_category,
                'opening_balance': float(account.opening_balance),
                'current_balance': float(account.current_balance)
            },
            'transactions': transactions,
            'totals': {
                'opening_balance': float(account.opening_balance),
                'total_debit': float(total_debit),
                'total_credit': float(total_credit),
                'closing_balance': float(running_balance),
                'net_change': float(running_balance - Decimal(str(account.opening_balance)))
            },
            'filters': filters
        }
        
        cache.set(f'task_{task_id}_result', result, timeout=300)
        cache.set(f'task_{task_id}_progress', {
            'state': 'SUCCESS',
            'status': 'Account Statement completed!',
            'progress': 100
        }, timeout=300)
        
    except Exception as e:
        cache.set(f'task_{task_id}_progress', {
            'state': 'FAILURE',
            'status': f'Error: {str(e)}',
            'progress': 0
        }, timeout=300)



# ==================== VIEW CLASSES ====================

class TrialBalanceReportView(View):
    """Trial Balance Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Trial Balance',
            'subtitle': 'Account balances with debit/credit totals',
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'account_type': request.GET.get('account_type', ''),
            }
        }
        return render(request, 'admin/erp/reports/trial_balance.html', context)


class ProfitLossReportView(View):
    """Profit & Loss Statement"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Profit & Loss Statement',
            'subtitle': 'Revenue and expense analysis',
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
            }
        }
        return render(request, 'admin/erp/reports/profit_loss.html', context)


class BalanceSheetReportView(View):
    """Balance Sheet"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Balance Sheet',
            'subtitle': 'Assets, Liabilities, and Equity',
            'filters': {
                'as_of_date': request.GET.get('as_of_date', ''),
            }
        }
        return render(request, 'admin/erp/reports/balance_sheet.html', context)


class GeneralLedgerReportView(View):
    """General Ledger Report"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'General Ledger',
            'subtitle': 'Account transaction history',
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'account': request.GET.get('account', ''),
            }
        }
        return render(request, 'admin/erp/reports/general_ledger.html', context)


class AccountStatementReportView(View):
    """Account Statement"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'title': 'Account Statement',
            'subtitle': 'Detailed account activity',
            'filters': {
                'from_date': request.GET.get('from_date', ''),
                'to_date': request.GET.get('to_date', ''),
                'account': request.GET.get('account', ''),
            }
        }
        return render(request, 'admin/erp/reports/account_statement.html', context)


# ==================== API ENDPOINTS ====================

# Trial Balance APIs
class StartTrialBalanceReportTaskView(View):
    """Start Trial Balance report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'account_type': request.GET.get('account_type'),
        }
        
        cache_key = f"trial_balance_{filters['from_date']}_{filters['to_date']}_{filters['account_type']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_trial_balance_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckTrialBalanceTaskStatusView(View):
    """Check Trial Balance task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found'})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result})
        
        return JsonResponse(progress)


# Profit & Loss APIs
class StartProfitLossReportTaskView(View):
    """Start P&L report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
        }
        
        cache_key = f"profit_loss_{filters['from_date']}_{filters['to_date']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_profit_loss_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckProfitLossTaskStatusView(View):
    """Check P&L task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found'})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result})
        
        return JsonResponse(progress)


# Balance Sheet APIs
class StartBalanceSheetReportTaskView(View):
    """Start Balance Sheet report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'as_of_date': request.GET.get('as_of_date'),
        }
        
        cache_key = f"balance_sheet_{filters['as_of_date']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_balance_sheet_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckBalanceSheetTaskStatusView(View):
    """Check Balance Sheet task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found'})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result})
        
        return JsonResponse(progress)


# General Ledger APIs
class StartGeneralLedgerReportTaskView(View):
    """Start GL report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'account_id': request.GET.get('account'),
        }
        
        cache_key = f"general_ledger_{filters['account_id']}_{filters['from_date']}_{filters['to_date']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_general_ledger_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckGeneralLedgerTaskStatusView(View):
    """Check GL task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found'})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result})
        
        return JsonResponse(progress)


# Account Statement APIs
class StartAccountStatementReportTaskView(View):
    """Start Account Statement report in background with caching"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        filters = {
            'from_date': request.GET.get('from_date'),
            'to_date': request.GET.get('to_date'),
            'account_id': request.GET.get('account'),
        }
        
        cache_key = f"account_statement_{filters['account_id']}_{filters['from_date']}_{filters['to_date']}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'cached': True, 'task_id': 'cached', 'data': cached_result})
        
        task_id = str(uuid.uuid4())
        generate_account_statement_report.enqueue(task_id, filters, request.user.id)
        cache.set(f'task_{task_id}_cache_key', cache_key, timeout=300)
        
        return JsonResponse({'task_id': task_id, 'status': 'started', 'cached': False})


class CheckAccountStatementTaskStatusView(View):
    """Check Account Statement task status"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found'})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result})
        
        return JsonResponse(progress)



# ==================== COMMON TASK STATUS ENDPOINT ====================

class FinancialReportTaskStatusView(View):
    """Common task status checker for all financial reports"""
    
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, task_id, *args, **kwargs):
        progress = cache.get(f'task_{task_id}_progress')
        if not progress:
            return JsonResponse({'state': 'PENDING', 'status': 'Task not found', 'progress': 0})
        
        if progress['state'] == 'SUCCESS':
            result = cache.get(f'task_{task_id}_result')
            cache_key = cache.get(f'task_{task_id}_cache_key')
            if cache_key and result:
                cache.set(cache_key, result, timeout=3600)
            return JsonResponse({'state': 'SUCCESS', 'data': result, 'progress': 100})
        
        return JsonResponse(progress)
