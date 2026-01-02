{
    "name": "Bike Shop",
    "version": "1.0.1",
    "summary": "Gestion des ventes et des locations de vélos",
    "description": """
Bike Shop
=================

Ce module permet de gérer une boutique de vélos :

- Catalogue : catégories, modèles, produits (avec images)
- Ventes : commandes, lignes de commande, paiement, mise à jour du stock
- Locations : contrats, tarification, suivi, retour, frais éventuels
- Clients : fiche client + historique ventes et locations
- Rapport PDF : contrat de location

Interface et libellés en français.
""",
    "author": "Jeremy Robalino Robles & Damian Koc",
    "website": "",
    "category": "Ventes",
    "application": True,
    "installable": True,
    "license": "LGPL-3",
    "depends": [
        "base",
        "calendar",
        "contacts",
        "crm",
        "sale_management",
        "board",
        "account",
        "website",
        "stock",
        "link_tracker",
        "website_sale"
    ],
    "data": [
        "demo/demo_data.xml",

        # Sécurité
        "security/ir.model.access.csv",

        # Séquences
        "data/sequences.xml",

        # Vues
        "views/category_views.xml",
        "views/bike_model_views.xml",
        "views/product_views.xml",
        "views/customer_views.xml",
        "views/rental_views.xml",
        "views/sale_order_views.xml",
        "views/menu.xml",

        # Rapports
        "reports/report_rental_contract.xml",
        "reports/rental_contract_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bike_manager/static/src/css/bike_kanban.css",
        ],
    },
}
