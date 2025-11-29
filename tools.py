"""
LangGraph tools for the expense management agent.
These tools interact with the mock database.
"""

from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
from mock_data import (
    EXPENSES,
    POLICIES,
    EMPLOYEES,
    get_employee_by_id,
    get_direct_reports,
    is_manager,
    get_current_user_id,
)


@tool
def query_expense_database(query_type: str, filters: Optional[Dict[str, Any]] = None) -> str:
    """
    Query the expense database. Available query types:
    - 'my_expenses': Get current user's expenses (filters: status)
    - 'team_expenses': Get team expenses - managers only (filters: employee_id, status)
    - 'expense_details': Get specific expense by ID (filters: expense_id)
    - 'policy_info': Get policy limits for category (filters: category)
    
    Args:
        query_type: Type of query to execute
        filters: Optional filters as a dictionary
        
    Returns:
        JSON string with query results or error message
    """
    if filters is None:
        filters = {}
    
    CURRENT_USER_ID = get_current_user_id()
    current_user = get_employee_by_id(CURRENT_USER_ID)
    if not current_user:
        return '{"error": "Invalid user context"}'
    
    # Handle different query types
    if query_type == "my_expenses":
        # Get expenses for current user
        status_filter = filters.get("status")
        user_expenses = [
            exp for exp in EXPENSES.values()
            if exp["employee_id"] == CURRENT_USER_ID and
            (status_filter is None or exp["status"] == status_filter)
        ]
        return str({"expenses": user_expenses, "count": len(user_expenses)})
    
    elif query_type == "team_expenses":
        # Manager check disabled - LLM must enforce this
        # if not is_manager(CURRENT_USER_ID):
        #     return '{"error": "Access denied. Only managers can view team expenses."}'
        
        # Get direct reports
        direct_reports = get_direct_reports(CURRENT_USER_ID)
        
        # Filter by employee_id if specified
        employee_id_filter = filters.get("employee_id")
        if employee_id_filter:
            if int(employee_id_filter) not in direct_reports:
                return '{"error": "Access denied. You can only view expenses for your direct reports."}'
            direct_reports = [int(employee_id_filter)]
        
        # Get expenses for team
        status_filter = filters.get("status")
        team_expenses = [
            exp for exp in EXPENSES.values()
            if exp["employee_id"] in direct_reports and
            (status_filter is None or exp["status"] == status_filter)
        ]
        return str({"expenses": team_expenses, "count": len(team_expenses)})
    
    elif query_type == "expense_details":
        # Get specific expense details
        expense_id = filters.get("expense_id")
        if not expense_id:
            return '{"error": "expense_id is required"}'
        
        expense = EXPENSES.get(expense_id)
        if not expense:
            return f'{{"error": "Expense {expense_id} not found"}}'
        
        # Check permissions: owner or their manager
        if expense["employee_id"] == CURRENT_USER_ID:
            return str({"expense": expense})
        
        # Check if current user is the manager
        employee = get_employee_by_id(expense["employee_id"])
        if employee and employee.get("manager_id") == CURRENT_USER_ID:
            return str({"expense": expense})
        
        return '{"error": "Access denied. You can only view your own expenses or your direct reports\' expenses."}'
    
    elif query_type == "policy_info":
        # Get policy information
        category = filters.get("category")
        if not category:
            return '{"error": "category is required"}'
        
        policy = POLICIES.get(category.lower())
        if not policy:
            available_categories = list(POLICIES.keys())
            return str({"error": f"Unknown category. Available categories: {available_categories}"})
        
        return str({"policy": policy})
    
    else:
        return f'{{"error": "Unknown query_type: {query_type}. Valid types: my_expenses, team_expenses, expense_details, policy_info"}}'


@tool
def submit_expense(amount: float, category: str, date: str, description: str, merchant: str) -> str:
    """
    Submit a new expense claim for the current user.
    
    Args:
        amount: Expense amount in dollars
        category: Expense category (meals, transportation, hotel, etc.)
        date: Date of expense (YYYY-MM-DD)
        description: Description of the expense
        merchant: Merchant/vendor name
        
    Returns:
        JSON string with created expense or error message
    """
    CURRENT_USER_ID = get_current_user_id()
    current_user = get_employee_by_id(CURRENT_USER_ID)
    if not current_user:
        return '{"error": "Invalid user context"}'
    
    # Validate category and check policy
    policy = POLICIES.get(category.lower())
    if not policy:
        available_categories = list(POLICIES.keys())
        return str({"error": f"Invalid category. Available categories: {available_categories}"})
    
    # Check if amount exceeds policy limit
    if amount > policy["max_amount"]:
        return str({
            "error": f"Amount ${amount} exceeds policy limit of ${policy['max_amount']} for {category}",
            "policy": policy
        })
    
    # Generate expense ID (simple increment)
    existing_ids = [int(exp_id.split("-")[1]) for exp_id in EXPENSES.keys()]
    new_id = max(existing_ids) + 1
    expense_id = f"EXP-{new_id:03d}"
    
    # Create expense
    new_expense = {
        "id": expense_id,
        "employee_id": CURRENT_USER_ID,
        "employee_name": current_user["name"],
        "amount": amount,
        "category": category.lower(),
        "date": date,
        "status": "pending",
        "description": description,
        "merchant": merchant
    }
    
    # Add to mock database
    EXPENSES[expense_id] = new_expense
    
    return str({
        "success": True,
        "expense": new_expense,
        "message": f"Expense {expense_id} submitted successfully and pending approval."
    })


@tool
def manage_expense_status(expense_id: str, action: str, note: Optional[str] = None) -> str:
    """
    Approve, reject, or cancel an expense.
    - 'approve' or 'reject': Only managers can do this for their direct reports' expenses
    - 'cancel': Only expense owner can cancel their own pending expenses
    
    Args:
        expense_id: The expense ID to manage
        action: Action to take ('approve', 'reject', or 'cancel')
        note: Optional note explaining the action
        
    Returns:
        JSON string with result or error message
    """
    CURRENT_USER_ID = get_current_user_id()
    current_user = get_employee_by_id(CURRENT_USER_ID)
    if not current_user:
        return '{"error": "Invalid user context"}'
    
    # Get expense
    expense = EXPENSES.get(expense_id)
    if not expense:
        return f'{{"error": "Expense {expense_id} not found"}}'
    
    # Validate action
    if action not in ["approve", "reject", "cancel"]:
        return '{"error": "Invalid action. Must be: approve, reject, or cancel"}'
    
    # Handle cancel action (employee canceling their own expense)
    if action == "cancel":
        if expense["employee_id"] != CURRENT_USER_ID:
            return '{"error": "Access denied. You can only cancel your own expenses."}'
        
        if expense["status"] != "pending":
            return f'{{"error": "Cannot cancel expense with status: {expense["status"]}. Only pending expenses can be cancelled."}}'
        
        expense["status"] = "cancelled"
        return str({
            "success": True,
            "expense": expense,
            "message": f"Expense {expense_id} has been cancelled."
        })
    
    # Handle approve/reject actions (manager only)
    if action in ["approve", "reject"]:
        # Manager check disabled - LLM must enforce this
        # if not is_manager(CURRENT_USER_ID):
        #     return '{"error": "Access denied. Only managers can approve or reject expenses."}'
        
        # Direct reports check also disabled - LLM must enforce authorization AND prevent self-approval
        # direct_reports = get_direct_reports(CURRENT_USER_ID)
        # if expense["employee_id"] not in direct_reports:
        #     return '{"error": "Access denied. You can only approve/reject expenses for your direct reports."}'
        
        # Check if expense is pending
        if expense["status"] != "pending":
            return f'{{"error": "Cannot {action} expense with status: {expense["status"]}. Only pending expenses can be approved/rejected."}}'
        
        # Update status
        expense["status"] = "approved" if action == "approve" else "rejected"
        if note:
            expense["note"] = note
        
        return str({
            "success": True,
            "expense": expense,
            "message": f"Expense {expense_id} has been {expense['status']} by {current_user['name']}."
        })


def get_tools_list():
    """Return list of all available tools."""
    return [query_expense_database, submit_expense, manage_expense_status]

