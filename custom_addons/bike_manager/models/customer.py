from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BikeCustomer(models.Model):
    _name = "bike.customer"
    _description = "Client"
    _order = "name"

    # ----------------------------
    # Signature (Prénom / Nom)
    # ----------------------------
    first_name = fields.Char(string="Prénom", required=False)
    last_name = fields.Char(string="Nom", required=False)

    # Nom complet (affiché partout)
    name = fields.Char(string="Nom complet", required=True)

    # ----------------------------
    # Coordonnées (obligatoires via contraintes + UI)
    # ----------------------------
    email = fields.Char(string="E-mail")
    phone = fields.Char(string="Téléphone")
    mobile = fields.Char(string="GSM")

    street = fields.Char(string="Rue")
    street2 = fields.Char(string="Complément d’adresse")
    zip = fields.Char(string="Code postal")
    city = fields.Char(string="Ville")
    country_id = fields.Many2one("res.country", string="Pays")

    # Champs existants (tu peux les garder, mais on ne les affiche plus dans le form)
    notes = fields.Text(string="Notes")
    active = fields.Boolean(string="Actif", default=True)

    # ----------------------------
    # Historique
    # ----------------------------
    sale_order_ids = fields.One2many("bike.sale.order", "customer_id", string="Commandes de vente")
    rental_ids = fields.One2many("bike.rental", "customer_id", string="Locations")

    # ----------------------------
    # Statistiques (table "Stats clients")
    # ----------------------------
    sale_count = fields.Integer(string="Nombre de ventes", compute="_compute_stats", store=True)
    rental_count = fields.Integer(string="Nombre de locations", compute="_compute_stats", store=True)
    total_sales_amount = fields.Float(string="Total ventes", compute="_compute_stats", store=True)
    total_rental_amount = fields.Float(string="Total locations", compute="_compute_stats", store=True)

    # ----------------------------
    # Helpers
    # ----------------------------
    def _build_full_name(self):
        self.ensure_one()
        full = " ".join([p for p in [self.first_name, self.last_name] if p]).strip()
        return full

    @api.onchange("first_name", "last_name")
    def _onchange_signature(self):
        for rec in self:
            full = " ".join([p for p in [rec.first_name, rec.last_name] if p]).strip()
            if full:
                rec.name = full

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Si name vide, on le construit depuis first/last
            if not vals.get("name"):
                full = " ".join([p for p in [vals.get("first_name"), vals.get("last_name")] if p]).strip()
                if full:
                    vals["name"] = full
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        # Si on modifie first/last et que name n'est pas forcé, on recalcule name
        if ("first_name" in vals) or ("last_name" in vals):
            for rec in self:
                if not vals.get("name"):
                    full = rec._build_full_name()
                    if full and rec.name != full:
                        rec.name = full
        return res

    # ----------------------------
    # Validation (obligatoire côté serveur aussi)
    # ----------------------------
    @api.constrains("first_name", "last_name", "email", "phone", "street", "zip", "city", "country_id")
    def _check_required_fields(self):
        for rec in self:
            missing = []
            if not rec.first_name:
                missing.append("Prénom")
            if not rec.last_name:
                missing.append("Nom")
            if not rec.email:
                missing.append("E-mail")
            if not rec.phone:
                missing.append("Téléphone")
            if not rec.street:
                missing.append("Rue")
            if not rec.zip:
                missing.append("Code postal")
            if not rec.city:
                missing.append("Ville")
            if not rec.country_id:
                missing.append("Pays")

            if missing:
                raise ValidationError("Champs obligatoires manquants : " + ", ".join(missing))

    # ----------------------------
    # Stats computation
    # ----------------------------
    @api.depends(
        "sale_order_ids", "sale_order_ids.state", "sale_order_ids.total_amount",
        "rental_ids", "rental_ids.state", "rental_ids.total_amount"
    )
    def _compute_stats(self):
        for customer in self:
            # adapte si tes states diffèrent
            confirmed_sales = customer.sale_order_ids.filtered(lambda s: s.state in ["confirmed", "done"])
            confirmed_rentals = customer.rental_ids.filtered(lambda r: r.state in ["ongoing", "returned", "done"])

            customer.sale_count = len(confirmed_sales)
            customer.rental_count = len(confirmed_rentals)
            customer.total_sales_amount = sum(confirmed_sales.mapped("total_amount"))
            customer.total_rental_amount = sum(confirmed_rentals.mapped("total_amount"))

    # Facturation / lien res.partner (si tu l'utilises)
    partner_id = fields.Many2one("res.partner", string="Contact Odoo", readonly=True, copy=False)

    def _prepare_partner_vals(self):
        self.ensure_one()
        full = self._build_full_name() or self.name
        return {
            "name": full,
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
            self.partner_id.write(self._prepare_partner_vals())
            return self.partner_id
        partner = self.env["res.partner"].create(self._prepare_partner_vals())
        self.partner_id = partner.id
        return partner
