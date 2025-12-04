from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta


class BikeRental(models.Model):
    """
    Bike rental management with pricing and availability
    """
    _name = "bike.rental"
    _description = "Bike Rental"
    _order = "start_date desc, name desc"

    name = fields.Char(string="Rental Reference", required=True, copy=False, readonly=True, default='New')
    customer_id = fields.Many2one('bike.customer', string="Customer", required=True, ondelete='restrict')
    product_id = fields.Many2one('bike.product', string="Bike/Product", required=True, ondelete='restrict',
                                  domain="[('can_be_rented', '=', True)]")

    # Rental period
    start_date = fields.Datetime(string="Start Date", required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(string="End Date", required=True)
    actual_return_date = fields.Datetime(string="Actual Return Date")

    # Pricing
    pricing_type = fields.Selection([
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string="Pricing Type", required=True, default='daily')

    unit_price = fields.Float(string="Unit Price", required=True)
    duration = fields.Float(string="Duration", compute='_compute_duration', store=True)
    total_price = fields.Float(string="Total Price", compute='_compute_total_price', store=True)

    # Additional charges
    deposit_amount = fields.Float(string="Deposit Amount", default=0.0)
    additional_charges = fields.Float(string="Additional Charges", default=0.0,
                                       help="Late fees, damage charges, etc.")
    total_amount = fields.Float(string="Total Amount", compute='_compute_total_amount', store=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', required=True)

    # Payment
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer')
    ], string="Payment Method")

    is_paid = fields.Boolean(string="Paid", default=False)
    deposit_returned = fields.Boolean(string="Deposit Returned", default=False)

    notes = fields.Text(string="Notes")
    condition_on_pickup = fields.Text(string="Condition on Pickup")
    condition_on_return = fields.Text(string="Condition on Return")

    # Integration with Odoo modules
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True,
                                  help="Invoice generated from this rental")
    calendar_event_id = fields.Many2one('calendar.event', string="Calendar Event", readonly=True,
                                         help="Calendar event for this rental")

    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        ('check_dates', 'CHECK(end_date > start_date)', 'End date must be after start date!')
    ]

    @api.model
    def create(self, vals_list):
        """Generate rental reference on create"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.rental') or 'New'
        return super(BikeRental, self).create(vals_list)

    @api.depends('start_date', 'end_date', 'pricing_type')
    def _compute_duration(self):
        """Compute rental duration based on pricing type"""
        for rental in self:
            if rental.start_date and rental.end_date:
                delta = rental.end_date - rental.start_date
                total_hours = delta.total_seconds() / 3600

                if rental.pricing_type == 'hourly':
                    rental.duration = total_hours
                elif rental.pricing_type == 'daily':
                    rental.duration = total_hours / 24
                elif rental.pricing_type == 'weekly':
                    rental.duration = total_hours / (24 * 7)
                elif rental.pricing_type == 'monthly':
                    rental.duration = total_hours / (24 * 30)
                else:
                    rental.duration = 0
            else:
                rental.duration = 0

    @api.depends('duration', 'unit_price')
    def _compute_total_price(self):
        """Compute total rental price"""
        for rental in self:
            rental.total_price = rental.duration * rental.unit_price

    @api.depends('total_price', 'deposit_amount', 'additional_charges')
    def _compute_total_amount(self):
        """Compute total amount including deposit and additional charges"""
        for rental in self:
            rental.total_amount = rental.total_price + rental.additional_charges

    @api.onchange('product_id', 'pricing_type')
    def _onchange_product_pricing(self):
        """Update unit price when product or pricing type changes"""
        if self.product_id and self.pricing_type:
            if self.pricing_type == 'hourly':
                self.unit_price = self.product_id.rental_price_hourly
            elif self.pricing_type == 'daily':
                self.unit_price = self.product_id.rental_price_daily
            elif self.pricing_type == 'weekly':
                self.unit_price = self.product_id.rental_price_weekly
            elif self.pricing_type == 'monthly':
                self.unit_price = self.product_id.rental_price_monthly

    @api.constrains('product_id', 'start_date', 'end_date', 'state')
    def _check_availability(self):
        """Check if product is available for the rental period"""
        for rental in self:
            if rental.state in ['draft', 'ongoing']:
                # Check if product is available
                if rental.product_id.available_quantity < 1:
                    # Check for overlapping rentals
                    overlapping = self.search([
                        ('id', '!=', rental.id),
                        ('product_id', '=', rental.product_id.id),
                        ('state', 'in', ['draft', 'ongoing']),
                        '|',
                        '&', ('start_date', '<=', rental.start_date), ('end_date', '>', rental.start_date),
                        '&', ('start_date', '<', rental.end_date), ('end_date', '>=', rental.end_date)
                    ])
                    if overlapping:
                        raise exceptions.ValidationError(
                            f"Product {rental.product_id.name} is not available for the selected period!"
                        )

    def action_start_rental(self):
        """Start the rental"""
        for rental in self:
            if rental.state != 'draft':
                raise exceptions.ValidationError("Only draft rentals can be started!")

            if rental.product_id.available_quantity < 1:
                raise exceptions.ValidationError(
                    f"Product {rental.product_id.name} is not available!"
                )

            rental.state = 'ongoing'
            rental.start_date = fields.Datetime.now()

    def action_return_bike(self):
        """Return the bike"""
        for rental in self:
            if rental.state != 'ongoing':
                raise exceptions.ValidationError("Only ongoing rentals can be returned!")

            rental.actual_return_date = fields.Datetime.now()

            # Calculate late fees if applicable
            if rental.actual_return_date > rental.end_date:
                late_duration = (rental.actual_return_date - rental.end_date).total_seconds() / 3600
                if rental.pricing_type == 'daily':
                    late_days = late_duration / 24
                    rental.additional_charges += late_days * rental.unit_price * 1.5  # 150% for late returns

            rental.state = 'returned'

    def action_cancel(self):
        """Cancel the rental"""
        for rental in self:
            if rental.state == 'returned':
                raise exceptions.ValidationError("Cannot cancel a returned rental!")
            rental.state = 'cancelled'

    def action_set_draft(self):
        """Reset rental to draft"""
        for rental in self:
            if rental.state not in ['cancelled']:
                raise exceptions.ValidationError("Only cancelled rentals can be reset to draft!")
            rental.state = 'draft'

    def action_create_invoice(self):
        """Create an invoice from this rental (Odoo Accounting integration)"""
        self.ensure_one()

        if not self.env.user.has_group('base.group_user'):
            return False

        # Check if account module is installed
        if 'account.move' not in self.env:
            raise exceptions.UserError("Accounting module is not installed!")

        if self.invoice_id:
            raise exceptions.UserError("An invoice already exists for this rental!")

        # Get or create partner for the customer
        partner_id = False
        if self.customer_id.partner_id:
            partner_id = self.customer_id.partner_id.id
        else:
            # Try to create a partner from customer info
            partner_vals = {
                'name': self.customer_id.name,
                'email': self.customer_id.email,
                'phone': self.customer_id.phone,
                'mobile': self.customer_id.mobile,
                'street': self.customer_id.street,
                'city': self.customer_id.city,
                'zip': self.customer_id.zip_code,
                'country_id': self.customer_id.country_id.id if self.customer_id.country_id else False,
                'customer_rank': 1,
            }
            partner = self.env['res.partner'].create(partner_vals)
            self.customer_id.partner_id = partner.id
            partner_id = partner.id

        if not partner_id:
            raise exceptions.UserError("Could not create invoice. Please link the customer to an Odoo contact first.")

        # Create invoice
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f"Rental: {self.product_id.name} ({self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')})",
                'quantity': self.duration,
                'price_unit': self.unit_price,
            })],
        }

        # Add additional charges if any
        if self.additional_charges > 0:
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'name': 'Additional Charges (Late fees, damages, etc.)',
                'quantity': 1,
                'price_unit': self.additional_charges,
            }))

        try:
            invoice = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            # If integration fails, just show a warning
            raise exceptions.UserError(f"Could not create invoice: {str(e)}")

    def action_create_calendar_event(self):
        """Create a calendar event for this rental"""
        self.ensure_one()

        # Check if calendar module is installed
        if 'calendar.event' not in self.env:
            raise exceptions.UserError("Calendar module is not installed!")

        if self.calendar_event_id:
            raise exceptions.UserError("A calendar event already exists for this rental!")

        event_vals = {
            'name': f"Rental: {self.customer_id.name} - {self.product_id.name}",
            'start': self.start_date,
            'stop': self.end_date,
            'description': f"Rental Reference: {self.name}\nCustomer: {self.customer_id.name}\nProduct: {self.product_id.name}\nTotal Amount: {self.total_amount}",
            'allday': False,
        }

        try:
            event = self.env['calendar.event'].create(event_vals)
            self.calendar_event_id = event.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Calendar Event',
                'res_model': 'calendar.event',
                'res_id': event.id,
                'view_mode': 'form',
                'target': 'current',
            }
        except Exception as e:
            raise exceptions.UserError(f"Could not create calendar event: {str(e)}")
