from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class BikeRental(models.Model):
    """
    Gestion des locations de vélos (tarifs + disponibilité)
    """
    _name = "bike.rental"
    _description = "Location de vélo"
    _order = "start_date desc, name desc"

    name = fields.Char(string="Référence de location", required=True, copy=False, readonly=True, default='New')
    customer_id = fields.Many2one('bike.customer', string="Client", required=True, ondelete='restrict')
    product_id = fields.Many2one(
        'bike.product',
        string="Vélo / Produit",
        required=True,
        ondelete='restrict',
        domain="[('can_be_rented', '=', True)]"
    )

    # Période de location
    start_date = fields.Datetime(string="Date de début", required=True, default=fields.Datetime.now)
    end_date = fields.Datetime(string="Date de fin", required=True)
    actual_return_date = fields.Datetime(string="Date de retour réelle")

    # Tarification
    pricing_type = fields.Selection([
        ('hourly', 'Horaire'),
        ('daily', 'Journalier'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel')
    ], string="Type de tarification", required=True, default='daily')

    unit_price = fields.Float(string="Prix unitaire", required=True)
    duration = fields.Float(string="Durée", compute='_compute_duration', store=True)
    total_price = fields.Float(string="Prix total", compute='_compute_total_price', store=True)

    # Frais supplémentaires
    deposit_amount = fields.Float(string="Montant de la caution", default=0.0)
    additional_charges = fields.Float(
        string="Frais supplémentaires",
        default=0.0,
        help="Retard, dommages, etc."
    )
    total_amount = fields.Float(string="Montant total", compute='_compute_total_amount', store=True)

    # Statut
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('ongoing', 'En cours'),
        ('returned', 'Retournée'),
        ('cancelled', 'Annulée')
    ], string="Statut", default='draft', required=True)

    # Paiement
    payment_method = fields.Selection([
        ('cash', 'Espèces'),
        ('card', 'Carte'),
        ('transfer', 'Virement bancaire')
    ], string="Mode de paiement")

    is_paid = fields.Boolean(string="Payée", default=False)
    deposit_returned = fields.Boolean(string="Caution rendue", default=False)

    notes = fields.Text(string="Notes")
    condition_on_pickup = fields.Text(string="État lors du retrait")
    condition_on_return = fields.Text(string="État lors du retour")

    active = fields.Boolean(string="Actif", default=True)

    _sql_constraints = [
        ('check_dates', 'CHECK(end_date > start_date)', 'La date de fin doit être après la date de début !')
    ]

    @api.model
    def create(self, vals_list):
        """Génère la référence de location à la création"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('bike.rental') or 'New'
        return super(BikeRental, self).create(vals_list)

    @api.depends('start_date', 'end_date', 'pricing_type')
    def _compute_duration(self):
        """Calcule la durée selon le type de tarification"""
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
        """Calcule le prix total de location"""
        for rental in self:
            rental.total_price = rental.duration * rental.unit_price

    @api.depends('total_price', 'deposit_amount', 'additional_charges')
    def _compute_total_amount(self):
        """Calcule le montant total (location + frais supplémentaires)."""
        for rental in self:
            rental.total_amount = rental.total_price + rental.additional_charges

    @api.onchange('product_id', 'pricing_type')
    def _onchange_product_pricing(self):
        """Met à jour le prix unitaire selon le vélo et le type de tarification"""
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
        """Vérifie la disponibilité du produit sur la période"""
        for rental in self:
            if rental.state in ['draft', 'ongoing']:
                if rental.product_id.available_quantity < 1:
                    overlapping = self.search([
                        ('id', '!=', rental.id),
                        ('product_id', '=', rental.product_id.id),
                        ('state', 'in', ['draft', 'ongoing']),
                        '|',
                        '&', ('start_date', '<=', rental.start_date), ('end_date', '>', rental.start_date),
                        '&', ('start_date', '<', rental.end_date), ('end_date', '>=', rental.end_date)
                    ])
                    if overlapping:
                        raise exceptions.ValidationError(_(
                            "Le produit %(product)s n’est pas disponible pour la période sélectionnée !"
                        ) % {'product': rental.product_id.name})

    def action_start_rental(self):
        """Démarre la location"""
        for rental in self:
            if rental.state != 'draft':
                raise exceptions.ValidationError(_("Seules les locations en brouillon peuvent être démarrées !"))

            if rental.product_id.available_quantity < 1:
                raise exceptions.ValidationError(_(
                    "Le produit %(product)s n’est pas disponible !"
                ) % {'product': rental.product_id.name})

            rental.state = 'ongoing'
            rental.start_date = fields.Datetime.now()

    def action_return_bike(self):
        """Retour du vélo"""
        for rental in self:
            if rental.state != 'ongoing':
                raise exceptions.ValidationError(_("Seules les locations en cours peuvent être retournées !"))

            rental.actual_return_date = fields.Datetime.now()

            # Frais de retard (si applicable)
            if rental.actual_return_date > rental.end_date:
                late_duration = (rental.actual_return_date - rental.end_date).total_seconds() / 3600
                if rental.pricing_type == 'daily':
                    late_days = late_duration / 24
                    rental.additional_charges += late_days * rental.unit_price * 1.5  # 150% en cas de retard

            rental.state = 'returned'

    def action_cancel(self):
        """Annule la location"""
        for rental in self:
            if rental.state == 'returned':
                raise exceptions.ValidationError(_("Impossible d’annuler une location retournée !"))
            rental.state = 'cancelled'

    def action_set_draft(self):
        """Remet la location en brouillon"""
        for rental in self:
            if rental.state not in ['cancelled']:
                raise exceptions.ValidationError(_("Seules les locations annulées peuvent repasser en brouillon !"))
            rental.state = 'draft'

    # Facturation
    invoice_id = fields.Many2one("account.move", string="Facture", readonly=True, copy=False)
    invoice_state = fields.Selection(related="invoice_id.state", string="Statut facture", readonly=True)

    def _get_sale_journal(self):
        journal = self.env["account.journal"].search([
            ("type", "=", "sale"),
            ("company_id", "=", self.env.company.id)
        ], limit=1)
        if not journal:
            raise ValidationError(_("Aucun journal de vente trouvé (type = sale)."))
        return journal

    def _get_income_account(self):
        Account = self.env["account.account"]
        domain = []

        # Filtre "income" (selon version)
        if "account_type" in Account._fields:
            domain.append(("account_type", "=", "income"))
        elif "internal_group" in Account._fields:
            domain.append(("internal_group", "=", "income"))

        # Actif / pas déprécié (selon version)
        if "active" in Account._fields:
            domain.append(("active", "=", True))
        if "deprecated" in Account._fields:
            domain.append(("deprecated", "=", False))

        # Filtre société (selon version)
        if "company_id" in Account._fields:
            domain.append(("company_id", "=", self.env.company.id))
        elif "company_ids" in Account._fields:
            domain.append(("company_ids", "in", self.env.company.id))

        acc = Account.search(domain, limit=1)
        if not acc:
            raise ValidationError("Aucun compte de revenu (income) trouvé.")
        return acc

    def _get_sale_tax_21(self):
        Tax = self.env["account.tax"]
        domain = [("type_tax_use", "=", "sale"), ("amount", "=", 21)]

        if "company_id" in Tax._fields:
            domain.append(("company_id", "=", self.env.company.id))
        elif "company_ids" in Tax._fields:
            domain.append(("company_ids", "in", self.env.company.id))

        return Tax.search(domain, limit=1)

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return self.action_view_invoice()

        partner = self.customer_id._get_or_create_partner()
        journal = self._get_sale_journal()
        income_account = self._get_income_account()
        tax = self._get_sale_tax_21()

        line_vals = [{
            "name": _("Location vélo: %s") % (self.product_id.name),
            "quantity": 1.0,
            "price_unit": self.total_price,
            "account_id": income_account.id,
            "tax_ids": [(6, 0, tax.ids)] if tax else False,
        }]

        if self.additional_charges:
            line_vals.append({
                "name": _("Frais supplémentaires (retard/dommages)"),
                "quantity": 1.0,
                "price_unit": self.additional_charges,
                "account_id": income_account.id,
                "tax_ids": [(6, 0, tax.ids)] if tax else False,
            })

        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_date": fields.Date.context_today(self),
            "journal_id": journal.id,
            "invoice_origin": self.name,
            "ref": self.name,
            "invoice_line_ids": [(0, 0, v) for v in line_vals],
        })

        self.invoice_id = move.id
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise ValidationError(_("Aucune facture liée à cette location."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Facture"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.invoice_id.id,
        }

    def action_print_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise ValidationError(_("Aucune facture à imprimer."))
        return self.invoice_id.action_invoice_print()