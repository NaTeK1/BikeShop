from odoo import models, fields, api, exceptions, _
from datetime import datetime


class BikeSaleOrder(models.Model):
    """
    Gestion des commandes de vente avec mise à jour du stock
    """
    _name = "bike.sale.order"
    _description = "Commande de vente"
    _order = "date desc, name desc"

    name = fields.Char(string="Référence de commande", required=True, copy=False, readonly=True, default='New')
    customer_id = fields.Many2one('bike.customer', string="Client", required=True, ondelete='restrict')
    date = fields.Datetime(string="Date de commande", required=True, default=fields.Datetime.now)

    # Lignes de commande
    order_line_ids = fields.One2many('bike.sale.order.line', 'order_id', string="Lignes de commande")

    # Montants
    subtotal = fields.Float(string="Sous-total", compute='_compute_amounts', store=True)
    tax_amount = fields.Float(string="TVA", compute='_compute_amounts', store=True)
    total_amount = fields.Float(string="Total", compute='_compute_amounts', store=True)

    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmée'),
        ('done', 'Terminée'),
        ('cancelled', 'Annulée')
    ], string="Statut", default='draft', required=True)

    # Paiement
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('card', 'Carte'),
        ('transfer', 'Virement bancaire')
    ], string="Mode de paiement")

    is_paid = fields.Boolean(string="Payée", default=False)
    payment_date = fields.Date(string="Date de paiement")

    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Actif", default=True)

    @api.model
    def create(self, vals_list):
        """Génère la référence de commande à la création"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.sale.order') or 'New'
        return super(BikeSaleOrder, self).create(vals_list)

    @api.depends('order_line_ids', 'order_line_ids.subtotal')
    def _compute_amounts(self):
        """Calcule les montants de la commande"""
        for order in self:
            order.subtotal = sum(order.order_line_ids.mapped('subtotal'))
            order.tax_amount = order.subtotal * 0.21  # TVA 21%
            order.total_amount = order.subtotal + order.tax_amount

    def action_confirm(self):
        """Confirme la commande et met à jour le stock"""
        for order in self:
            if not order.order_line_ids:
                raise exceptions.ValidationError(_("Impossible de confirmer une commande sans lignes !"))

            # Vérifier la disponibilité du stock
            for line in order.order_line_ids:
                if line.product_id.stock_quantity < line.quantity:
                    raise exceptions.ValidationError(_(
                        "Stock insuffisant pour le produit %(product)s. "
                        "Disponible : %(available)s, Demandé : %(requested)s"
                    ) % {
                        'product': line.product_id.name,
                        'available': line.product_id.stock_quantity,
                        'requested': line.quantity,
                    })

            # Mise à jour du stock
            for line in order.order_line_ids:
                line.product_id.stock_quantity -= line.quantity

            order.state = 'confirmed'

    def action_done(self):
        """Marque la commande comme terminée"""
        for order in self:
            if order.state != 'confirmed':
                raise exceptions.ValidationError(_("Seules les commandes confirmées peuvent être terminées !"))
            order.state = 'done'

    def action_cancel(self):
        """Annule la commande et restaure le stock si nécessaire"""
        for order in self:
            if order.state == 'done':
                raise exceptions.ValidationError(_("Impossible d’annuler une commande terminée !"))

            # Restaurer le stock si la commande était confirmée
            if order.state == 'confirmed':
                for line in order.order_line_ids:
                    line.product_id.stock_quantity += line.quantity

            order.state = 'cancelled'

    def action_set_draft(self):
        """Remet la commande en brouillon"""
        for order in self:
            if order.state not in ['cancelled']:
                raise exceptions.ValidationError(_("Seules les commandes annulées peuvent repasser en brouillon !"))
            order.state = 'draft'


class BikeSaleOrderLine(models.Model):
    """
    Lignes de commande de vente
    """
    _name = "bike.sale.order.line"
    _description = "Ligne de commande"
    _order = "order_id, sequence, id"

    sequence = fields.Integer(string="Séquence", default=10)
    order_id = fields.Many2one('bike.sale.order', string="Commande", required=True, ondelete='cascade')
    product_id = fields.Many2one('bike.product', string="Produit", required=True, ondelete='restrict')

    description = fields.Text(string="Description")
    quantity = fields.Integer(string="Quantité", required=True, default=1)
    unit_price = fields.Float(string="Prix unitaire", required=True)
    discount = fields.Float(string="Remise (%)", default=0.0)
    subtotal = fields.Float(string="Sous-total", compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price', 'discount')
    def _compute_subtotal(self):
        """Calcule le sous-total de la ligne"""
        for line in self:
            price = line.unit_price * (1 - (line.discount / 100))
            line.subtotal = line.quantity * price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Met à jour le prix unitaire quand le produit change"""
        if self.product_id:
            self.unit_price = self.product_id.sale_price
            self.description = self.product_id.description
