"""Tests for tools module"""

import ast

import pytest

from ctf_expense_manager.mock_data import (
    EMPLOYEES,
    EXPENSES,
    get_or_create_user_from_email,
    set_current_user,
)
from ctf_expense_manager.tools import (
    get_tools_list,
    manage_expense_status,
    query_expense_database,
    submit_expense,
)


def call_tool(tool, *args, **kwargs):
    """Helper to call LangChain tools"""
    return tool.func(*args, **kwargs)


@pytest.fixture(autouse=True)
def setup_test_user():
    """Setup a test user for each test"""
    email = "testuser@example.com"
    user_id = get_or_create_user_from_email(email)
    set_current_user(user_id)
    yield user_id
    # Cleanup is handled by pytest


@pytest.fixture
def manager_user():
    """Create a manager user for testing"""
    email = "manager@example.com"
    user_id = get_or_create_user_from_email(email)
    EMPLOYEES[user_id]["role"] = "manager"
    return user_id


class TestQueryExpenseDatabase:
    """Test query_expense_database tool"""

    def test_my_expenses_empty(self, setup_test_user):
        """Test querying my expenses when there are none"""
        result = call_tool(query_expense_database, "my_expenses")
        data = ast.literal_eval(result)

        assert "expenses" in data
        assert data["count"] == 0
        assert len(data["expenses"]) == 0

    def test_my_expenses_with_data(self, setup_test_user):
        """Test querying my expenses when they exist"""
        expense_id = "EXP-TEST-001"
        EXPENSES[expense_id] = {
            "id": expense_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "Test meal",
            "merchant": "Test Restaurant",
        }

        result = call_tool(query_expense_database, "my_expenses")
        data = ast.literal_eval(result)

        assert data["count"] == 1
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["id"] == expense_id

        del EXPENSES[expense_id]

    def test_my_expenses_with_status_filter(self, setup_test_user):
        """Test filtering my expenses by status"""
        exp1_id = "EXP-TEST-PENDING"
        exp2_id = "EXP-TEST-APPROVED"

        EXPENSES[exp1_id] = {
            "id": exp1_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "Test",
            "merchant": "Test",
        }

        EXPENSES[exp2_id] = {
            "id": exp2_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 60.0,
            "category": "meals",
            "date": "2025-01-02",
            "status": "approved",
            "description": "Test",
            "merchant": "Test",
        }

        result = call_tool(query_expense_database, "my_expenses", {"status": "pending"})
        data = ast.literal_eval(result)

        assert data["count"] == 1
        assert data["expenses"][0]["status"] == "pending"

        del EXPENSES[exp1_id]
        del EXPENSES[exp2_id]

    def test_team_expenses(self, setup_test_user, manager_user):
        """Test querying team expenses"""
        set_current_user(manager_user)

        employee_id = get_or_create_user_from_email("employee@example.com")
        EMPLOYEES[employee_id]["manager_id"] = manager_user

        exp_id = "EXP-TEAM-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": employee_id,
            "employee_name": "Employee",
            "amount": 75.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "Team expense",
            "merchant": "Restaurant",
        }

        result = call_tool(query_expense_database, "team_expenses")
        data = ast.literal_eval(result)

        assert data["count"] == 1
        assert data["expenses"][0]["employee_id"] == employee_id

        del EXPENSES[exp_id]

    def test_team_expenses_no_direct_reports(self, setup_test_user):
        """Test team expenses with no direct reports"""
        result = call_tool(query_expense_database, "team_expenses")
        data = ast.literal_eval(result)

        assert data["count"] == 0

    def test_expense_details_own_expense(self, setup_test_user):
        """Test getting expense details for own expense"""
        exp_id = "EXP-OWN-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "My expense",
            "merchant": "Restaurant",
        }

        result = call_tool(query_expense_database, "expense_details", {"expense_id": exp_id})
        data = ast.literal_eval(result)

        assert "expense" in data
        assert data["expense"]["id"] == exp_id

        del EXPENSES[exp_id]

    def test_expense_details_not_found(self, setup_test_user):
        """Test getting expense details for non-existent expense"""
        result = call_tool(
            query_expense_database, "expense_details", {"expense_id": "EXP-NOTFOUND"}
        )
        data = ast.literal_eval(result)

        assert "error" in data
        assert "not found" in data["error"]

    def test_expense_details_no_permission(self, setup_test_user):
        """Test getting expense details without permission"""
        result = call_tool(query_expense_database, "expense_details", {"expense_id": "EXP-001"})
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Access denied" in data["error"]

    def test_expense_details_manager_can_view(self, manager_user):
        """Test that manager can view direct report's expense"""
        set_current_user(manager_user)

        employee_id = get_or_create_user_from_email("report@example.com")
        EMPLOYEES[employee_id]["manager_id"] = manager_user

        exp_id = "EXP-REPORT-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": employee_id,
            "employee_name": "Report",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "Report expense",
            "merchant": "Restaurant",
        }

        result = call_tool(query_expense_database, "expense_details", {"expense_id": exp_id})
        data = ast.literal_eval(result)

        assert "expense" in data
        assert data["expense"]["id"] == exp_id

        del EXPENSES[exp_id]

    def test_policy_info(self, setup_test_user):
        """Test getting policy information"""
        result = call_tool(query_expense_database, "policy_info", {"category": "meals"})
        data = ast.literal_eval(result)

        assert "policy" in data
        assert data["policy"]["category"] == "meals"
        assert data["policy"]["max_amount"] == 75.00

    def test_policy_info_case_insensitive(self, setup_test_user):
        """Test that policy lookup is case insensitive"""
        result = call_tool(query_expense_database, "policy_info", {"category": "MEALS"})
        data = ast.literal_eval(result)

        assert "policy" in data
        assert data["policy"]["category"] == "meals"

    def test_policy_info_unknown_category(self, setup_test_user):
        """Test getting policy info for unknown category"""
        result = call_tool(query_expense_database, "policy_info", {"category": "unknown"})
        data = ast.literal_eval(result)

        assert "error" in data

    def test_unknown_query_type(self, setup_test_user):
        """Test using an unknown query type"""
        result = call_tool(query_expense_database, "invalid_query_type")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Unknown query_type" in data["error"]


class TestSubmitExpense:
    """Test submit_expense tool"""

    def test_submit_valid_expense(self, setup_test_user):
        """Test submitting a valid expense"""
        result = call_tool(
            submit_expense,
            amount=50.0,
            category="meals",
            date="2025-01-01",
            description="Business lunch",
            merchant="Restaurant",
        )
        data = ast.literal_eval(result)

        assert data["success"] is True
        assert "expense" in data
        assert data["expense"]["amount"] == 50.0
        assert data["expense"]["category"] == "meals"
        assert data["expense"]["status"] == "pending"
        assert data["expense"]["employee_id"] == setup_test_user

        exp_id = data["expense"]["id"]
        assert exp_id in EXPENSES

        del EXPENSES[exp_id]

    def test_submit_expense_exceeds_policy(self, setup_test_user):
        """Test submitting expense that exceeds policy limit"""
        result = call_tool(
            submit_expense,
            amount=100.0,
            category="meals",
            date="2025-01-01",
            description="Too expensive",
            merchant="Restaurant",
        )
        data = ast.literal_eval(result)

        assert "error" in data
        assert "exceeds policy limit" in data["error"]

    def test_submit_expense_invalid_category(self, setup_test_user):
        """Test submitting expense with invalid category"""
        result = call_tool(
            submit_expense,
            amount=50.0,
            category="invalid_category",
            date="2025-01-01",
            description="Test",
            merchant="Test",
        )
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Invalid category" in data["error"]

    def test_submit_expense_case_insensitive_category(self, setup_test_user):
        """Test that category is case insensitive"""
        result = call_tool(
            submit_expense,
            amount=50.0,
            category="MEALS",
            date="2025-01-01",
            description="Test",
            merchant="Test",
        )
        data = ast.literal_eval(result)

        assert data["success"] is True
        assert data["expense"]["category"] == "meals"

        del EXPENSES[data["expense"]["id"]]


class TestManageExpenseStatus:
    """Test manage_expense_status tool"""

    def test_cancel_own_pending_expense(self, setup_test_user):
        """Test canceling own pending expense"""
        exp_id = "EXP-CANCEL-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "To cancel",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "cancel")
        data = ast.literal_eval(result)

        assert data["success"] is True
        assert data["expense"]["status"] == "cancelled"

        del EXPENSES[exp_id]

    def test_cancel_others_expense_denied(self, setup_test_user):
        """Test that canceling someone else's expense is denied"""
        result = call_tool(manage_expense_status, "EXP-001", "cancel")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Access denied" in data["error"]

    def test_cancel_non_pending_expense(self, setup_test_user):
        """Test canceling a non-pending expense"""
        exp_id = "EXP-APPROVED-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "approved",
            "description": "Already approved",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "cancel")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Only pending expenses can be cancelled" in data["error"]

        del EXPENSES[exp_id]

    def test_approve_expense(self, manager_user):
        """Test approving an expense"""
        set_current_user(manager_user)

        exp_id = "EXP-APPROVE-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": 1,
            "employee_name": "Employee",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "To approve",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "approve")
        data = ast.literal_eval(result)

        assert data["success"] is True
        assert data["expense"]["status"] == "approved"

        del EXPENSES[exp_id]

    def test_reject_expense_with_note(self, manager_user):
        """Test rejecting an expense with a note"""
        set_current_user(manager_user)

        exp_id = "EXP-REJECT-001"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": 1,
            "employee_name": "Employee",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "To reject",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "reject", note="Not approved")
        data = ast.literal_eval(result)

        assert data["success"] is True
        assert data["expense"]["status"] == "rejected"
        assert data["expense"]["note"] == "Not approved"

        del EXPENSES[exp_id]

    def test_approve_non_pending_expense(self, manager_user):
        """Test approving a non-pending expense"""
        set_current_user(manager_user)

        exp_id = "EXP-ALREADY-APPROVED"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": 1,
            "employee_name": "Employee",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "approved",
            "description": "Already approved",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "approve")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Only pending expenses" in data["error"]

        del EXPENSES[exp_id]

    def test_invalid_action(self, setup_test_user):
        """Test using an invalid action"""
        exp_id = "EXP-INVALID-ACTION"
        EXPENSES[exp_id] = {
            "id": exp_id,
            "employee_id": setup_test_user,
            "employee_name": "Testuser",
            "amount": 50.0,
            "category": "meals",
            "date": "2025-01-01",
            "status": "pending",
            "description": "Test",
            "merchant": "Restaurant",
        }

        result = call_tool(manage_expense_status, exp_id, "invalid_action")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "Invalid action" in data["error"]

        del EXPENSES[exp_id]

    def test_nonexistent_expense(self, setup_test_user):
        """Test managing a non-existent expense"""
        result = call_tool(manage_expense_status, "EXP-NOTFOUND", "approve")
        data = ast.literal_eval(result)

        assert "error" in data
        assert "not found" in data["error"]


class TestGetToolsList:
    """Test get_tools_list function"""

    def test_get_tools_list_returns_three_tools(self):
        """Test that get_tools_list returns three tools"""
        tools = get_tools_list()
        assert len(tools) == 3

    def test_get_tools_list_contains_correct_tools(self):
        """Test that get_tools_list contains the correct tools"""
        tools = get_tools_list()
        tool_funcs = [tool.func for tool in tools]

        assert query_expense_database.func in tool_funcs
        assert submit_expense.func in tool_funcs
        assert manage_expense_status.func in tool_funcs
