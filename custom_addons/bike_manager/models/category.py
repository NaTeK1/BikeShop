from odoo import models, fields, api
import base64
import os


class BikeCategory(models.Model):
    """
    Catégories de produits (ex: VTT, Route, Urbain, Accessoires, Pièces, etc.)
    """
    _name = "bike.category"
    _description = "Catégorie"
    _order = "name"
    _inherit = ["image.mixin"]

    name = fields.Char(string="Nom de la catégorie", required=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)

    product_ids = fields.One2many("bike.product", "category_id", string="Produits")
    product_count = fields.Integer(string="Nombre de produits", compute="_compute_product_count", store=True)

    @api.depends("product_ids", "product_ids.active")
    def _compute_product_count(self):
        for cat in self:
            cat.product_count = len(cat.product_ids.filtered(lambda p: p.active))

    def action_view_products(self):
        """Ouvre la vue des vélos de cette catégorie"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'bike.product',
            'view_mode': 'kanban,list,form',
            'domain': [('category_id', '=', self.id), ('product_type', '=', 'bike')],
            'context': {'default_category_id': self.id},
        }

    @api.model
    def _load_category_images(self):
        """Charge les images des catégories depuis le dossier static"""
        module_path = os.path.dirname(os.path.dirname(__file__))
        img_path = os.path.join(module_path, 'static', 'src', 'img')

        # Mapping des catégories et leurs images
        category_images = {
            'VTT': 'VTT.jpg',
            'Vélos de route': 'VELOROUTE.jpg',
            'Vélos électriques': 'VELOELECTRIQUE.jpg',
        }

        for category_name, image_file in category_images.items():
            category = self.search([('name', '=', category_name)], limit=1)
            if category and not category.image_1920:
                image_path = os.path.join(img_path, image_file)
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                        category.write({'image_1920': image_data})
