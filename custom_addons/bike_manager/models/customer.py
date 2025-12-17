from odoo import models, fields, api


class BikeCustomer(models.Model):
    """
    Gestion des clients avec historique ventes et locations
    """
    _name = "bike.customer"
    _description = "Client"
    _order = "name"

    # Identité / contact
    name = fields.Char(string="Nom du client", required=True)
    email = fields.Char(string="E-mail")
    phone = fields.Char(string="Téléphone")
    mobile = fields.Char(string="GSM")

    # Adresse
    street = fields.Char(string="Rue")
    street2 = fields.Char(string="Complément d’adresse")
    zip = fields.Char(string="Code postal")
    city = fields.Char(string="Ville")
    country_id = fields.Many2one("res.country", string="Pays")

    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Actif", default=True)

    # Historique
    sale_order_ids = fields.One2many("bike.sale.order", "customer_id", string="Commandes de vente")
    rental_ids = fields.One2many("bike.rental", "customer_id", string="Locations")

    # Statistiques
    sale_count = fields.Integer(string="Nombre de ventes", compute="_compute_stats", store=True)
    rental_count = fields.Integer(string="Nombre de locations", compute="_compute_stats", store=True)
    total_sales_amount = fields.Float(string="Total ventes", compute="_compute_stats", store=True)
    total_rental_amount = fields.Float(string="Total locations", compute="_compute_stats", store=True)

    @api.depends(
        "sale_order_ids", "sale_order_ids.state", "sale_order_ids.total_amount",
        "rental_ids", "rental_ids.state", "rental_ids.total_amount"
    )
    def _compute_stats(self):
        for customer in self:
            confirmed_sales = customer.sale_order_ids.filtered(lambda s: s.state in ["confirmed", "done"])
            confirmed_rentals = customer.rental_ids.filtered(lambda r: r.state in ["ongoing", "returned"])

            customer.sale_count = len(confirmed_sales)
            customer.rental_count = len(confirmed_rentals)

            customer.total_sales_amount = sum(confirmed_sales.mapped("total_amount"))
            customer.total_rental_amount = sum(confirmed_rentals.mapped("total_amount"))

    def name_get(self):
        """Nom affiché: Nom (email) si dispo"""
        res = []
        for customer in self:
            display = customer.name
            if customer.email:
                display = f"{display} ({customer.email})"
            res.append((customer.id, display))
        return res

    # Facturation
    partner_id = fields.Many2one("res.partner", string="Contact Odoo", readonly=True, copy=False)

    def _prepare_partner_vals(self):
        self.ensure_one()
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone or self.mobile,
            "street": self.street,
            "street2": self.street2,
            "zip": self.zip,
            "city": self.city,
            "country_id": self.country_id.id if self.country_id else False,
            "company_type": "person",
        }

    def _get_or_create_partner(self):
        self.ensure_one()
        if self.partner_id:
            # optionnel: resync des infos
            self.partner_id.write(self._prepare_partner_vals())
            return self.partner_id
        partner = self.env["res.partner"].create(self._prepare_partner_vals())
        self.partner_id = partner.id
        return partner