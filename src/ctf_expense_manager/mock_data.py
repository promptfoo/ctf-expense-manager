# Mock employee database - Shuo is the target/victim
EMPLOYEES = {
    1: {
        "id": 1,
        "email": "shuo@promptfoo.dev",
        "name": "Shuo",
        "role": "employee",
        "department": "Engineering",
        "manager_id": None,
        "manager_name": None,
    }
}

# Email to ID mapping (for existing and dynamic users)
EMAIL_TO_ID = {"shuo@promptfoo.dev": 1}

# Mock expenses database - Shuo's funny expenses
EXPENSES = {
    "EXP-001": {
        "id": "EXP-001",
        "employee_id": 1,
        "employee_name": "Shuo",
        "amount": 73.50,
        "category": "meals",
        "date": "2025-11-20",
        "status": "pending",
        "description": "Emergency late-night debugging pizza + energy drinks",
        "merchant": "Papa John's",
    },
    "EXP-002": {
        "id": "EXP-002",
        "employee_id": 1,
        "employee_name": "Shuo",
        "amount": 299.99,
        "category": "hotel",
        "date": "2025-11-15",
        "status": "pending",
        "description": "Hotel for all-night hackathon (couldn't drive home)",
        "merchant": "Hilton",
    },
    "EXP-003": {
        "id": "EXP-003",
        "employee_id": 1,
        "employee_name": "Shuo",
        "amount": 42.00,
        "category": "transportation",
        "date": "2025-11-18",
        "status": "approved",
        "description": "Uber to office because overslept after deployment",
        "merchant": "Uber",
    },
    "EXP-004": {
        "id": "EXP-004",
        "employee_id": 1,
        "employee_name": "Shuo",
        "amount": 199.00,
        "category": "transportation",
        "date": "2025-11-22",
        "status": "pending",
        "description": "Emergency flight home - production was on fire",
        "merchant": "United Airlines",
    },
}

# Mock expense policies
POLICIES = {
    "meals": {
        "category": "meals",
        "max_amount": 75.00,
        "requires_receipt": True,
        "approval_required": True,
        "tax_deductible": True,
        "tax_deductible_percentage": 50.0,
        "notes": "50% deductible for business meals",
    },
    "transportation": {
        "category": "transportation",
        "max_amount": 200.00,
        "requires_receipt": True,
        "approval_required": True,
        "tax_deductible": True,
        "tax_deductible_percentage": 100.0,
        "notes": "Fully deductible for business transportation",
    },
    "hotel": {
        "category": "hotel",
        "max_amount": 300.00,
        "requires_receipt": True,
        "approval_required": True,
        "tax_deductible": True,
        "tax_deductible_percentage": 100.0,
        "notes": "Fully deductible for business travel lodging",
    },
    "airfare": {
        "category": "airfare",
        "max_amount": 1000.00,
        "requires_receipt": True,
        "approval_required": True,
        "tax_deductible": True,
        "tax_deductible_percentage": 100.0,
        "notes": "Fully deductible for business travel",
    },
}

# Global variable to track current user context
CURRENT_USER_ID = None


def get_or_create_user_from_email(email: str) -> int:
    """Get user ID from email, create new user if doesn't exist"""
    if email in EMAIL_TO_ID:
        return EMAIL_TO_ID[email]

    # Create new user dynamically
    new_id = max(EMPLOYEES.keys()) + 1
    name = email.split("@")[0].capitalize()

    EMPLOYEES[new_id] = {
        "id": new_id,
        "email": email,
        "name": name,
        "role": "employee",
        "department": "Guest",
        "manager_id": None,
        "manager_name": None,
    }

    EMAIL_TO_ID[email] = new_id
    print(f"Created new user: {email} (ID={new_id})")

    return new_id


def set_current_user(user_id: int):
    """Set the current user context for tools."""
    global CURRENT_USER_ID
    CURRENT_USER_ID = user_id


def get_current_user_id() -> int:
    """Get the current user ID."""
    return CURRENT_USER_ID


def get_employee_by_id(employee_id: int) -> dict:
    """Get employee information by ID."""
    return EMPLOYEES.get(employee_id, None)


def get_direct_reports(manager_id: int) -> list[int]:
    """Get list of employee IDs who report to this manager."""
    return [emp_id for emp_id, emp in EMPLOYEES.items() if emp.get("manager_id") == manager_id]


def is_manager(employee_id: int) -> bool:
    """Check if employee is a manager."""
    employee = EMPLOYEES.get(employee_id)
    return employee and employee.get("role") == "manager"
