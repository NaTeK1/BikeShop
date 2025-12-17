from odoo import models, fields, api


class BikeModel(models.Model):
    _name = "bike.model"
    _description = "Modèle de vélo"
    _order = "brand, name"

    name = fields.Char(string="Nom du modèle", required=True)
    brand = fields.Char(string="Marque")
    year = fields.Integer(string="Année")
    description = fields.Text(string="Description")

    category_id = fields.Many2one("bike.category", string="Catégorie", ondelete="set null")

    frame_material = fields.Selection([
        ('aluminium', 'Aluminium'),
        ('carbon', 'Carbone'),
        ('steel', 'Acier'),
        ('titanium', 'Titane'),
        ('other', 'Autre'),
    ], string="Matériau du cadre", default='aluminium')

    wheel_size = fields.Selection([
        ('26', '26"'),
        ('27_5', '27,5"'),
        ('29', '29"'),
        ('700c', '700c'),
        ('other', 'Autre'),
    ], string="Taille des roues")

    active = fields.Boolean(string="Actif", default=True)

    product_ids = fields.One2many("bike.product", "bike_model_id", string="Produits liés")
    product_count = fields.Integer(string="Nombre de produits", compute="_compute_product_count", store=True)

    @api.depends("product_ids", "product_ids.active")
    def _compute_product_count(self):
        for model in self:
            model.product_count = len(model.product_ids.filtered(lambda p: p.active))
