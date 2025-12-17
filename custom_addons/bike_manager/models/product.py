from odoo import models, fields, api, exceptions, _


class BikeProduct(models.Model):
    """
    Produits : vélos, accessoires et pièces
    """
    _name = "bike.product"
    _description = "Produit vélo"
    _order = "name"
    _inherit = ["image.mixin"]

    name = fields.Char(string="Nom du produit", required=True)
    reference = fields.Char(string="Référence interne", required=True, copy=False)
    description = fields.Text(string="Description")
    image_1920 = fields.Image(string="Image", max_width=1920, max_height=1920)

    # Type de produit
    product_type = fields.Selection([
        ('bike', 'Vélo'),
        ('accessory', 'Accessoire'),
        ('part', 'Pièce')
    ], string="Type de produit", required=True, default='bike')

    # Catégorie et modèle
    category_id = fields.Many2one('bike.category', string="Catégorie", required=True, ondelete='restrict')
    bike_model_id = fields.Many2one(
        'bike.model',
        string="Modèle de vélo",
        help="Lien vers le modèle (uniquement pour les vélos)"
    )

    # Prix
    sale_price = fields.Float(string="Prix de vente", required=True, default=0.0)
    cost_price = fields.Float(string="Prix de revient", default=0.0)

    # Tarifs de location
    can_be_rented = fields.Boolean(string="Peut être loué", default=False)
    rental_price_hourly = fields.Float(string="Prix de location horaire")
    rental_price_daily = fields.Float(string="Prix de location journalier")
    rental_price_weekly = fields.Float(string="Prix de location hebdomadaire")
    rental_price_monthly = fields.Float(string="Prix de location mensuel")

    # Stock
    stock_quantity = fields.Integer(string="Quantité en stock", default=0)
    reserved_quantity = fields.Integer(string="Quantité réservée", compute='_compute_reserved_quantity', store=True)
    available_quantity = fields.Integer(string="Quantité disponible", compute='_compute_available_quantity', store=True)

    # Statut
    state = fields.Selection([
        ('available', 'Disponible'),
        ('rented', 'Loué'),
        ('maintenance', 'En maintenance'),
        ('sold', 'Vendu')
    ], string="Statut", default='available', compute='_compute_state', store=True)

    active = fields.Boolean(string="Actif", default=True)

    # Relations
    rental_ids = fields.One2many('bike.rental', 'product_id', string="Historique des locations")

    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'La référence produit doit être unique !')
    ]

    @api.depends('rental_ids', 'rental_ids.state')
    def _compute_reserved_quantity(self):
        """Calcule la quantité réservée par des locations actives"""
        for product in self:
            active_rentals = product.rental_ids.filtered(lambda r: r.state in ['draft', 'ongoing'])
            product.reserved_quantity = len(active_rentals)

    @api.depends('stock_quantity', 'reserved_quantity')
    def _compute_available_quantity(self):
        """Calcule la quantité disponible (stock - réservée)"""
        for product in self:
            product.available_quantity = product.stock_quantity - product.reserved_quantity

    @api.depends('rental_ids', 'rental_ids.state', 'stock_quantity')
    def _compute_state(self):
        """Calcule l’état selon les locations et le stock"""
        for product in self:
            if product.stock_quantity == 0:
                product.state = 'sold'
            elif product.rental_ids.filtered(lambda r: r.state == 'ongoing'):
                product.state = 'rented'
            else:
                product.state = 'available'

    @api.constrains('stock_quantity')
    def _check_stock_quantity(self):
        """Empêche un stock négatif"""
        for product in self:
            if product.stock_quantity < 0:
                raise exceptions.ValidationError(_("La quantité en stock ne peut pas être négative !"))

    @api.constrains('sale_price', 'cost_price')
    def _check_prices(self):
        """Empêche des prix négatifs"""
        for product in self:
            if product.sale_price < 0 or product.cost_price < 0:
                raise exceptions.ValidationError(_("Les prix doivent être positifs !"))

    @api.constrains('image_1920')
    def _check_image_required(self):
        for product in self:
            if not product.image_1920:
                raise exceptions.ValidationError(_("Veuillez ajouter une image pour chaque produit."))
