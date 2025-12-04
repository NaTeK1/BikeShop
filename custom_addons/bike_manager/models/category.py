from odoo import models, fields, api


class BikeCategory(models.Model):
    """
    Product categories for bike shop (bikes, accessories, parts)
    """
    _name = "bike.category"
    _description = "Product Category"
    _order = "name"

    name = fields.Char(string="Category Name", required=True)
    description = fields.Text(string="Description")
    parent_id = fields.Many2one('bike.category', string="Parent Category", ondelete='restrict')
    child_ids = fields.One2many('bike.category', 'parent_id', string="Subcategories")
    product_ids = fields.One2many('bike.product', 'category_id', string="Products")
    product_count = fields.Integer(string="Number of Products", compute='_compute_product_count')
    active = fields.Boolean(string="Active", default=True)

    @api.depends('product_ids')
    def _compute_product_count(self):
        """Compute the number of products in this category"""
        for category in self:
            category.product_count = len(category.product_ids)

    def name_get(self):
        """Display full category path"""
        result = []
        for category in self:
            name = category.name
            if category.parent_id:
                name = f"{category.parent_id.name} / {name}"
            result.append((category.id, name))
        return result
