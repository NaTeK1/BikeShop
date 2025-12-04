{
    'name': 'Bike Shop',
    'version': '1.0',
    'summary': 'Bike sales and rentals management',
    'author': 'Jeremy Robalino Robles & Damian Koc',
    'website': '',
    'description': """
Bike Shop
=========
Module de base pour la gestion de modèles de vélos.
""",
    'category': 'Sales',
    'application': True,
    'depends': [
        'base',
        'calendar',      # Calendar
        'contacts',      # Contacts
        'crm',           # CRM
        'sale_management',  # Sales
        'board',         # Dashboards
        'account',       # Invoicing/Accounting
        'website',       # Website
        'stock',         # Inventory
        'link_tracker',  # Link Tracker
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data
        'data/sequences.xml',

        # Views
        'views/category_views.xml',
        'views/bike_model_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/rental_views.xml',
        'views/customer_views.xml',
        'views/menu.xml',

        # Demo data
        'demo/demo_data.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
