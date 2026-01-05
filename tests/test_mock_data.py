"""Tests for mock_data module"""

from ctf_expense_manager.mock_data import (
    EMAIL_TO_ID,
    EMPLOYEES,
    EXPENSES,
    POLICIES,
    get_current_user_id,
    get_direct_reports,
    get_employee_by_id,
    get_or_create_user_from_email,
    is_manager,
    set_current_user,
)


class TestEmployeeData:
    """Test employee data structures and functions"""

    def test_employees_contains_shuo(self):
        """Test that Shuo exists in the employee database"""
        assert 1 in EMPLOYEES
        assert EMPLOYEES[1]["email"] == "shuo@promptfoo.dev"
        assert EMPLOYEES[1]["name"] == "Shuo"
        assert EMPLOYEES[1]["role"] == "employee"

    def test_email_to_id_mapping(self):
        """Test email to ID mapping"""
        assert "shuo@promptfoo.dev" in EMAIL_TO_ID
        assert EMAIL_TO_ID["shuo@promptfoo.dev"] == 1


class TestGetOrCreateUser:
    """Test user creation and retrieval"""

    def test_get_existing_user(self):
        """Test getting an existing user by email"""
        user_id = get_or_create_user_from_email("shuo@promptfoo.dev")
        assert user_id == 1

    def test_create_new_user(self):
        """Test creating a new user from email"""
        email = "newuser@example.com"
        user_id = get_or_create_user_from_email(email)

        assert user_id in EMPLOYEES
        assert EMPLOYEES[user_id]["email"] == email
        assert EMPLOYEES[user_id]["name"] == "Newuser"
        assert EMPLOYEES[user_id]["role"] == "employee"
        assert EMPLOYEES[user_id]["department"] == "Guest"
        assert email in EMAIL_TO_ID
        assert EMAIL_TO_ID[email] == user_id

    def test_get_created_user_again(self):
        """Test that getting a user that was created returns the same ID"""
        email = "anotheruser@test.com"
        user_id_1 = get_or_create_user_from_email(email)
        user_id_2 = get_or_create_user_from_email(email)

        assert user_id_1 == user_id_2

    def test_new_users_get_incrementing_ids(self):
        """Test that new users get incrementing IDs"""
        email1 = "user1@test.com"
        email2 = "user2@test.com"

        id1 = get_or_create_user_from_email(email1)
        id2 = get_or_create_user_from_email(email2)

        assert id2 > id1


class TestCurrentUserContext:
    """Test current user context management"""

    def test_set_and_get_current_user(self):
        """Test setting and getting current user ID"""
        set_current_user(1)
        assert get_current_user_id() == 1

        set_current_user(5)
        assert get_current_user_id() == 5

    def test_current_user_persists_across_calls(self):
        """Test that current user context persists"""
        set_current_user(3)
        assert get_current_user_id() == 3
        assert get_current_user_id() == 3


class TestGetEmployeeById:
    """Test employee retrieval by ID"""

    def test_get_existing_employee(self):
        """Test getting an existing employee"""
        employee = get_employee_by_id(1)
        assert employee is not None
        assert employee["id"] == 1
        assert employee["email"] == "shuo@promptfoo.dev"

    def test_get_nonexistent_employee(self):
        """Test getting a non-existent employee returns None"""
        employee = get_employee_by_id(99999)
        assert employee is None


class TestGetDirectReports:
    """Test getting direct reports for a manager"""

    def test_no_direct_reports_for_employee(self):
        """Test that regular employees have no direct reports"""
        reports = get_direct_reports(1)
        assert reports == []

    def test_direct_reports_for_manager(self):
        """Test getting direct reports for a manager"""
        email1 = "employee1@test.com"
        email2 = "employee2@test.com"
        manager_email = "manager@test.com"

        emp1_id = get_or_create_user_from_email(email1)
        emp2_id = get_or_create_user_from_email(email2)
        manager_id = get_or_create_user_from_email(manager_email)

        EMPLOYEES[emp1_id]["manager_id"] = manager_id
        EMPLOYEES[emp2_id]["manager_id"] = manager_id

        reports = get_direct_reports(manager_id)
        assert emp1_id in reports
        assert emp2_id in reports
        assert len(reports) == 2


class TestIsManager:
    """Test manager role checking"""

    def test_employee_is_not_manager(self):
        """Test that regular employees are not managers"""
        assert not is_manager(1)

    def test_manager_role_detected(self):
        """Test that manager role is detected"""
        manager_email = "realmanager@test.com"
        manager_id = get_or_create_user_from_email(manager_email)
        EMPLOYEES[manager_id]["role"] = "manager"

        assert is_manager(manager_id)

    def test_nonexistent_user_is_not_manager(self):
        """Test that non-existent user is not a manager"""
        assert not is_manager(99999)


class TestExpensesData:
    """Test expenses data structure"""

    def test_expenses_exist(self):
        """Test that expenses are defined"""
        assert len(EXPENSES) > 0

    def test_shuo_expenses_exist(self):
        """Test that Shuo's expenses exist"""
        shuo_expenses = [exp for exp in EXPENSES.values() if exp["employee_id"] == 1]
        assert len(shuo_expenses) > 0

    def test_expense_structure(self):
        """Test that expenses have required fields"""
        expense = EXPENSES["EXP-001"]
        required_fields = [
            "id",
            "employee_id",
            "employee_name",
            "amount",
            "category",
            "date",
            "status",
            "description",
            "merchant",
        ]

        for field in required_fields:
            assert field in expense

    def test_expense_statuses(self):
        """Test that expenses have valid statuses"""
        valid_statuses = ["pending", "approved", "rejected", "cancelled"]

        for expense in EXPENSES.values():
            assert expense["status"] in valid_statuses


class TestPoliciesData:
    """Test policies data structure"""

    def test_policies_exist(self):
        """Test that policies are defined"""
        assert len(POLICIES) > 0

    def test_required_policy_categories(self):
        """Test that required policy categories exist"""
        required_categories = ["meals", "transportation", "hotel", "airfare"]

        for category in required_categories:
            assert category in POLICIES

    def test_policy_structure(self):
        """Test that policies have required fields"""
        policy = POLICIES["meals"]
        required_fields = [
            "category",
            "max_amount",
            "requires_receipt",
            "approval_required",
            "tax_deductible",
        ]

        for field in required_fields:
            assert field in policy

    def test_policy_max_amounts(self):
        """Test that policy max amounts are positive"""
        for policy in POLICIES.values():
            assert policy["max_amount"] > 0

    def test_policy_tax_deductible_percentage(self):
        """Test that tax deductible percentage is valid"""
        for policy in POLICIES.values():
            if "tax_deductible_percentage" in policy:
                assert 0 <= policy["tax_deductible_percentage"] <= 100
