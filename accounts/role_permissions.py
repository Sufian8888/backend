"""
Role-based permissions for different models and actions.
This file defines what each role can do with different models.
"""

# Permissions for each role
ROLE_PERMISSIONS = {
    'admin': {
        'all': ['view', 'add', 'change', 'delete'],
    },
    'purchasing': {
        'product': ['view', 'change'],
        'supplier': ['view', 'add', 'change'],
        'purchaseorder': ['view', 'add', 'change'],
        'inventory': ['view', 'change'],
    },
    'sales': {
        'product': ['view'],
        'customer': ['view', 'add', 'change'],
        'order': ['view', 'add', 'change', 'delete'],
        'invoice': ['view', 'add', 'change'],
    },
    'customer': {
        'product': ['view'],
        'order': ['view', 'add'],
        'invoice': ['view'],
    },
}

def has_permission(role, model_name, action):
    """
    Check if a role has permission to perform an action on a model.
    
    Args:
        role (str): User role (admin, purchasing, sales, customer)
        model_name (str): Name of the model (lowercase)
        action (str): Action to check (view, add, change, delete)
        
    Returns:
        bool: True if permission is granted, False otherwise
    """
    # Admin has all permissions
    if role == 'admin':
        return True
        
    # Check if role exists in permissions
    role_perms = ROLE_PERMISSIONS.get(role, {})
    
    # Check model permissions
    model_perms = role_perms.get('all', []) + role_perms.get(model_name, [])
    
    # Check if action is allowed
    return action in model_perms
