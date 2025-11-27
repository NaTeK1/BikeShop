from odoo import models, fields

class BikeModel(models.Model):
    _name = "bike.model"
    _description = "Bike Model"

    name = fields.Char(string="Nom du modèle", required=True)
    brand = fields.Char(string="Marque")
    reference = fields.Char(string="Référence")
    category = fields.Selection([
        ('city', 'Vélo de ville'),
        ('road', 'Vélo de route'),
        ('mountain', 'VTT'),
        ('electric', 'Vélo électrique'),
        ('kids', 'Vélo enfant'),
    ], string="Catégorie")
    price = fields.Float(string="Prix de vente")
    available_qty = fields.Integer(string="Quantité disponible", default=0)
    active = fields.Boolean(string="Actif", default=True)
