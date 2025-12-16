from odoo import models, fields, api, exceptions


class BikeProduct(models.Model):
    """
    Products: individual bikes, accessories, and parts
    """
    _name = "bike.product"
    _description = "Bike Product"
    _order = "name"
    _inherit = ["image.mixin"]

    name = fields.Char(string="Product Name", required=True)
    reference = fields.Char(string="Internal Reference", required=True, copy=False)
    description = fields.Text(string="Description")
    image_1920 = fields.Image(string="Image", max_width=1920, max_height=1920)

    # Product type
    product_type = fields.Selection([
        ('bike', 'Bike'),
        ('accessory', 'Accessory'),
        ('part', 'Part')
    ], string="Product Type", required=True, default='bike')

    # Category and model
    category_id = fields.Many2one('bike.category', string="Category", required=True, ondelete='restrict')
    bike_model_id = fields.Many2one('bike.model', string="Bike Model",
                                     help="Link to bike model (for bikes only)")

    # Pricing
    sale_price = fields.Float(string="Sale Price", required=True, default=0.0)
    cost_price = fields.Float(string="Cost Price", default=0.0)

    # Rental pricing
    can_be_rented = fields.Boolean(string="Can be Rented", default=False)
    rental_price_hourly = fields.Float(string="Hourly Rental Price")
    rental_price_daily = fields.Float(string="Daily Rental Price")
    rental_price_weekly = fields.Float(string="Weekly Rental Price")
    rental_price_monthly = fields.Float(string="Monthly Rental Price")

    # Stock management
    stock_quantity = fields.Integer(string="Stock Quantity", default=0)
    reserved_quantity = fields.Integer(string="Reserved Quantity", compute='_compute_reserved_quantity', store=True)
    available_quantity = fields.Integer(string="Available Quantity", compute='_compute_available_quantity', store=True)

    # Status
    state = fields.Selection([
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'In Maintenance'),
        ('sold', 'Sold')
    ], string="Status", default='available', compute='_compute_state', store=True)

    active = fields.Boolean(string="Active", default=True)

    # Integration with Odoo Stock (optional)
    # Uncomment after installing stock/product module
    # product_tmpl_id = fields.Many2one('product.template', string="Odoo Product Template",
    #                                    help="Link to Odoo product for integration with Stock, Sales, etc.")

    # Relations
    rental_ids = fields.One2many('bike.rental', 'product_id', string="Rental History")

    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'Product reference must be unique!')
    ]

    @api.depends('rental_ids', 'rental_ids.state')
    def _compute_reserved_quantity(self):
        """Compute quantity reserved by active rentals"""
        for product in self:
            active_rentals = product.rental_ids.filtered(lambda r: r.state in ['draft', 'ongoing'])
            product.reserved_quantity = len(active_rentals)

    @api.depends('stock_quantity', 'reserved_quantity')
    def _compute_available_quantity(self):
        """Compute available quantity (stock - reserved)"""
        for product in self:
            product.available_quantity = product.stock_quantity - product.reserved_quantity

    @api.depends('rental_ids', 'rental_ids.state', 'stock_quantity')
    def _compute_state(self):
        """Compute product state based on rentals and stock"""
        for product in self:
            if product.stock_quantity == 0:
                product.state = 'sold'
            elif product.rental_ids.filtered(lambda r: r.state == 'ongoing'):
                product.state = 'rented'
            else:
                product.state = 'available'

    @api.constrains('stock_quantity')
    def _check_stock_quantity(self):
        """Ensure stock quantity is not negative"""
        for product in self:
            if product.stock_quantity < 0:
                raise exceptions.ValidationError("Stock quantity cannot be negative!")

    @api.constrains('sale_price', 'cost_price')
    def _check_prices(self):
        """Ensure prices are positive"""
        for product in self:
            if product.sale_price < 0 or product.cost_price < 0:
                raise exceptions.ValidationError("Prices must be positive!")

    @api.constrains('image_1920')
    def _check_image_required(self):
        for product in self:
            if not product.image_1920:
                raise exceptions.ValidationError("Please add an image for each product.")