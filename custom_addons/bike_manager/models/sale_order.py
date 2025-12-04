from odoo import models, fields, api, exceptions
from datetime import datetime


class BikeSaleOrder(models.Model):
    """
    Sales order management with invoicing and stock management
    """
    _name = "bike.sale.order"
    _description = "Sale Order"
    _order = "date desc, name desc"

    name = fields.Char(string="Order Reference", required=True, copy=False, readonly=True, default='New')
    customer_id = fields.Many2one('bike.customer', string="Customer", required=True, ondelete='restrict')
    date = fields.Datetime(string="Order Date", required=True, default=fields.Datetime.now)

    # Order lines
    order_line_ids = fields.One2many('bike.sale.order.line', 'order_id', string="Order Lines")

    # Amounts
    subtotal = fields.Float(string="Subtotal", compute='_compute_amounts', store=True)
    tax_amount = fields.Float(string="Tax Amount", compute='_compute_amounts', store=True)
    total_amount = fields.Float(string="Total Amount", compute='_compute_amounts', store=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', required=True)

    # Payment
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer')
    ], string="Payment Method")

    is_paid = fields.Boolean(string="Paid", default=False)
    payment_date = fields.Date(string="Payment Date")

    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals_list):
        """Generate order reference on create"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.sale.order') or 'New'
        return super(BikeSaleOrder, self).create(vals_list)

    @api.depends('order_line_ids', 'order_line_ids.subtotal')
    def _compute_amounts(self):
        """Compute order amounts"""
        for order in self:
            order.subtotal = sum(order.order_line_ids.mapped('subtotal'))
            order.tax_amount = order.subtotal * 0.21  # 21% VAT
            order.total_amount = order.subtotal + order.tax_amount

    def action_confirm(self):
        """Confirm the order and update stock"""
        for order in self:
            if not order.order_line_ids:
                raise exceptions.ValidationError("Cannot confirm an order without lines!")

            # Check stock availability
            for line in order.order_line_ids:
                if line.product_id.stock_quantity < line.quantity:
                    raise exceptions.ValidationError(
                        f"Insufficient stock for product {line.product_id.name}. "
                        f"Available: {line.product_id.stock_quantity}, Requested: {line.quantity}"
                    )

            # Update stock
            for line in order.order_line_ids:
                line.product_id.stock_quantity -= line.quantity

            order.state = 'confirmed'

    def action_done(self):
        """Mark order as done"""
        for order in self:
            if order.state != 'confirmed':
                raise exceptions.ValidationError("Only confirmed orders can be marked as done!")
            order.state = 'done'

    def action_cancel(self):
        """Cancel the order and restore stock"""
        for order in self:
            if order.state == 'done':
                raise exceptions.ValidationError("Cannot cancel a done order!")

            # Restore stock if order was confirmed
            if order.state == 'confirmed':
                for line in order.order_line_ids:
                    line.product_id.stock_quantity += line.quantity

            order.state = 'cancelled'

    def action_set_draft(self):
        """Reset order to draft"""
        for order in self:
            if order.state not in ['cancelled']:
                raise exceptions.ValidationError("Only cancelled orders can be reset to draft!")
            order.state = 'draft'


class BikeSaleOrderLine(models.Model):
    """
    Sale order lines
    """
    _name = "bike.sale.order.line"
    _description = "Sale Order Line"
    _order = "order_id, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    order_id = fields.Many2one('bike.sale.order', string="Order", required=True, ondelete='cascade')
    product_id = fields.Many2one('bike.product', string="Product", required=True, ondelete='restrict')

    description = fields.Text(string="Description")
    quantity = fields.Integer(string="Quantity", required=True, default=1)
    unit_price = fields.Float(string="Unit Price", required=True)
    discount = fields.Float(string="Discount (%)", default=0.0)
    subtotal = fields.Float(string="Subtotal", compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price', 'discount')
    def _compute_subtotal(self):
        """Compute line subtotal"""
        for line in self:
            price = line.unit_price * (1 - (line.discount / 100))
            line.subtotal = line.quantity * price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update unit price when product changes"""
        if self.product_id:
            self.unit_price = self.product_id.sale_price
            self.description = self.product_id.description
