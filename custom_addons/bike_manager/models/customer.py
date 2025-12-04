from odoo import models, fields, api


class BikeCustomer(models.Model):
    """
    Customer management with sales and rental history
    """
    _name = "bike.customer"
    _description = "Customer"
    _order = "name"

    name = fields.Char(string="Customer Name", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")

    # Address
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    zip_code = fields.Char(string="Zip Code")
    country_id = fields.Many2one('res.country', string="Country")

    # Additional info
    birth_date = fields.Date(string="Birth Date")
    id_number = fields.Char(string="ID Number", help="Identity card or passport number")
    notes = fields.Text(string="Notes")

    # Integration with Odoo Contacts
    partner_id = fields.Many2one('res.partner', string="Odoo Contact",
                                  help="Link to Odoo contact for integration with Sales, Accounting, etc.")

    # Relations
    sale_order_ids = fields.One2many('bike.sale.order', 'customer_id', string="Sales Orders")
    rental_ids = fields.One2many('bike.rental', 'customer_id', string="Rentals")

    # Statistics
    sale_count = fields.Integer(string="Number of Sales", compute='_compute_statistics')
    rental_count = fields.Integer(string="Number of Rentals", compute='_compute_statistics')
    total_sales_amount = fields.Float(string="Total Sales Amount", compute='_compute_statistics')
    total_rental_amount = fields.Float(string="Total Rental Amount", compute='_compute_statistics')

    active = fields.Boolean(string="Active", default=True)

    @api.depends('sale_order_ids', 'sale_order_ids.state', 'rental_ids', 'rental_ids.state')
    def _compute_statistics(self):
        """Compute customer statistics"""
        for customer in self:
            # Sales statistics
            confirmed_sales = customer.sale_order_ids.filtered(lambda s: s.state in ['confirmed', 'done'])
            customer.sale_count = len(confirmed_sales)
            customer.total_sales_amount = sum(confirmed_sales.mapped('total_amount'))

            # Rental statistics
            confirmed_rentals = customer.rental_ids.filtered(lambda r: r.state in ['ongoing', 'returned'])
            customer.rental_count = len(confirmed_rentals)
            customer.total_rental_amount = sum(confirmed_rentals.mapped('total_price'))

    @api.depends('name', 'email')
    def name_get(self):
        """Display name with email"""
        result = []
        for customer in self:
            name = customer.name
            if customer.email:
                name = f"{name} ({customer.email})"
            result.append((customer.id, name))
        return result

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update customer info from Odoo contact"""
        if self.partner_id:
            self.name = self.partner_id.name
            self.email = self.partner_id.email
            self.phone = self.partner_id.phone
            self.mobile = self.partner_id.mobile
            self.street = self.partner_id.street
            self.street2 = self.partner_id.street2
            self.city = self.partner_id.city
            self.zip_code = self.partner_id.zip
            self.country_id = self.partner_id.country_id

    def action_create_odoo_contact(self):
        """Create an Odoo contact from this customer"""
        self.ensure_one()

        if self.partner_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Odoo Contact',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # Create new contact
        partner_vals = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'zip': self.zip_code,
            'country_id': self.country_id.id if self.country_id else False,
            'customer_rank': 1,
        }

        partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Odoo Contact',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }
