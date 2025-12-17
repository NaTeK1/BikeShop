from odoo import models, fields, api


class BikeCategory(models.Model):
    """
    Catégories de produits (ex: VTT, Route, Urbain, Accessoires, Pièces, etc.)
    """
    _name = "bike.category"
    _description = "Catégorie"
    _order = "name"

    name = fields.Char(string="Nom de la catégorie", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    product_ids = fields.One2many("bike.product", "category_id", string="Produits")
    product_count = fields.Integer(string="Nombre de produits", compute="_compute_product_count", store=True)

    @api.depends("product_ids", "product_ids.active")
    def _compute_product_count(self):
        for cat in self:
            cat.product_count = len(cat.product_ids.filtered(lambda p: p.active))
