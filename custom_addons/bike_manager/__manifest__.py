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
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/bike_model_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
