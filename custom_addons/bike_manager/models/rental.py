from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
from datetime import timedelta


def _sel_range(start, end):
    """Helper: create selection (string) from start..end."""
    return [(str(i), str(i)) for i in range(start, end + 1)]


class BikeRental(models.Model):
    """
    Gestion des locations de vélos (tarifs + disponibilité + facturation)
    """
    _name = "bike.rental"
    _description = "Location de vélo"
    _order = "start_date desc, name desc"

    # Référence
    name = fields.Char(
        string="Référence de location",
        required=True,
        copy=False,
        readonly=True,
        default="New"
    )

    # Liens
    customer_id = fields.Many2one(
        "bike.customer",
        string="Client",
        required=True,
        ondelete="restrict"
    )
    product_id = fields.Many2one(
        "bike.product",
        string="Vélo",
        required=True,
        ondelete="restrict",
        domain="[('can_be_rented', '=', True)]"
    )

    # Période
    start_date = fields.Datetime(
        string="Date de début",
        required=True,
        default=fields.Datetime.now
    )
    end_date = fields.Datetime(
        string="Date de fin",
        required=True
    )

    # Type de location (sera affiché dans "Période")
    pricing_type = fields.Selection([
        ("hourly", "Horaire"),
        ("daily", "Journalier"),
        ("weekly", "Hebdomadaire"),
        ("monthly", "Mensuel")
    ], string="Type de location", required=True, default="daily")

    # Durées en listes déroulantes selon le type
    hours_qty = fields.Selection(_sel_range(1, 23), string="Heures", default="1")
    days_qty = fields.Selection(_sel_range(1, 6), string="Jours", default="1")
    weeks_qty = fields.Selection(_sel_range(1, 3), string="Semaines", default="1")
    months_qty = fields.Selection(_sel_range(1, 24), string="Mois", default="1")

    # Quantité "unifiée" (interne) -> utilisée pour calculer end_date
    rental_qty = fields.Float(
        string="Quantité de location",
        compute="_compute_rental_qty",
        store=True,
        readonly=True,
        help="Quantité interne calculée depuis le champ de durée (heures/jours/semaines/mois)."
    )

    # Tarification
    unit_price = fields.Float(string="Prix unitaire", required=True)

    # On garde duration en interne
    duration = fields.Float(string="Durée", compute="_compute_duration", store=True)
    total_price = fields.Float(string="Prix total", compute="_compute_total_price", store=True)

    # Frais
    deposit_amount = fields.Float(string="Montant de la caution", default=0.0)
    additional_charges = fields.Float(
        string="Frais supplémentaires (retard/dommages)",
        default=0.0,
        help="Retard, dommages, etc."
    )

    # --- Extras (sans nouveau modèle) ---
    extra_product_ids = fields.Many2many(
        "bike.product",
        "bike_rental_extra_product_rel",
        "rental_id",
        "product_id",
        string="Accessoires / pièces",
        domain=[("can_be_rented", "=", False)],
        help="Produits accessoires ajoutés pendant la location (1 unité par produit)."
    )

    extras_total = fields.Float(
        string="Total accessoires",
        compute="_compute_extras_total",
        store=True
    )

    manual_extra_amount = fields.Float(
        string="Frais supplémentaires (montant libre)",
        default=0.0,
        help="Montant libre en complément (ou si aucun produit)."
    )

    extras_grand_total = fields.Float(
        string="Frais supplémentaires (total)",
        compute="_compute_extras_grand_total",
        store=True,
        readonly=True,
    )

    total_amount = fields.Float(string="Montant total", compute="_compute_total_amount", store=True)

    # Statut
    state = fields.Selection([
        ("draft", "Brouillon"),
        ("ongoing", "En cours"),
        ("returned", "Retournée"),
        ("cancelled", "Annulée")
    ], string="Statut", default="draft", required=True)

    # Paiement
    payment_method = fields.Selection([
        ("cash", "Espèces"),
        ("card", "Carte"),
        ("transfer", "Virement bancaire")
    ], string="Mode de paiement")

    is_paid = fields.Boolean(string="Payée", default=False)
    deposit_returned = fields.Boolean(string="Caution rendue", default=False)

    # Notes / état
    notes = fields.Text(string="Notes")
    condition_on_pickup = fields.Text(string="État lors du retrait")
    condition_on_return = fields.Text(string="État lors du retour")

    active = fields.Boolean(string="Actif", default=True)

    _sql_constraints = [
        ("check_dates", "CHECK(end_date > start_date)", "La date de fin doit être après la date de début !")
    ]

    # -----------------------------
    # COMPUTE: rental_qty
    # -----------------------------
    @api.depends("pricing_type", "hours_qty", "days_qty", "weeks_qty", "months_qty")
    def _compute_rental_qty(self):
        for r in self:
            if r.pricing_type == "hourly":
                r.rental_qty = float(r.hours_qty or "0")
            elif r.pricing_type == "daily":
                r.rental_qty = float(r.days_qty or "0")
            elif r.pricing_type == "weekly":
                r.rental_qty = float(r.weeks_qty or "0")
            elif r.pricing_type == "monthly":
                r.rental_qty = float(r.months_qty or "0")
            else:
                r.rental_qty = 0.0

    # -----------------------------
    # CREATE + SEQUENCE + END_DATE
    # -----------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """
        - Génère la référence via sequence
        - Calcule end_date si manquante
        """
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("bike.rental") or "New"

            start = vals.get("start_date")
            ptype = vals.get("pricing_type")
            end = vals.get("end_date")

            # qty par défaut = 1 (utile si création hors UI)
            qty = 0.0
            if ptype == "hourly":
                qty = float(vals.get("hours_qty") or 1)
            elif ptype == "daily":
                qty = float(vals.get("days_qty") or 1)
            elif ptype == "weekly":
                qty = float(vals.get("weeks_qty") or 1)
            elif ptype == "monthly":
                qty = float(vals.get("months_qty") or 1)

            if start and ptype and qty and not end:
                start_dt = fields.Datetime.to_datetime(start)
                vals["end_date"] = self._calc_end_date(start_dt, ptype, qty)

        return super().create(vals_list)

    # -----------------------------
    # Helpers dates
    # -----------------------------
    def _calc_end_date(self, start_dt, pricing_type, qty):
        if qty <= 0:
            return False

        if pricing_type == "hourly":
            return start_dt + timedelta(hours=qty)
        if pricing_type == "daily":
            return start_dt + timedelta(days=qty)
        if pricing_type == "weekly":
            return start_dt + timedelta(weeks=qty)
        if pricing_type == "monthly":
            # simple 30j
            return start_dt + timedelta(days=30 * qty)
        return False

    # -----------------------------
    # ONCHANGE: prix + date de fin
    # -----------------------------
    @api.onchange("product_id", "pricing_type")
    def _onchange_product_pricing(self):
        """Met à jour le prix unitaire selon le vélo et le type."""
        if self.product_id and self.pricing_type:
            if self.pricing_type == "hourly":
                self.unit_price = self.product_id.rental_price_hourly
            elif self.pricing_type == "daily":
                self.unit_price = self.product_id.rental_price_daily
            elif self.pricing_type == "weekly":
                self.unit_price = self.product_id.rental_price_weekly
            elif self.pricing_type == "monthly":
                self.unit_price = self.product_id.rental_price_monthly

    @api.onchange("start_date", "pricing_type", "hours_qty", "days_qty", "weeks_qty", "months_qty")
    def _onchange_compute_end_date(self):
        """Calcule automatiquement end_date en fonction du type + durée sélectionnée."""
        if not self.start_date or not self.pricing_type:
            return

        # IMPORTANT: ne pas dépendre de rental_qty en onchange
        if self.pricing_type == "hourly":
            qty = float(self.hours_qty or "0")
        elif self.pricing_type == "daily":
            qty = float(self.days_qty or "0")
        elif self.pricing_type == "weekly":
            qty = float(self.weeks_qty or "0")
        elif self.pricing_type == "monthly":
            qty = float(self.months_qty or "0")
        else:
            qty = 0.0

        if qty <= 0:
            self.end_date = False
            return

        self.end_date = self._calc_end_date(self.start_date, self.pricing_type, qty)

    # -----------------------------
    # COMPUTES montants
    # -----------------------------
    @api.depends("start_date", "end_date", "pricing_type")
    def _compute_duration(self):
        for r in self:
            if r.start_date and r.end_date:
                if r.end_date <= r.start_date:
                    r.duration = 0.0
                    continue
                delta = r.end_date - r.start_date
                total_hours = delta.total_seconds() / 3600.0
                if r.pricing_type == "hourly":
                    r.duration = total_hours
                elif r.pricing_type == "daily":
                    r.duration = total_hours / 24.0
                elif r.pricing_type == "weekly":
                    r.duration = total_hours / (24.0 * 7.0)
                elif r.pricing_type == "monthly":
                    r.duration = total_hours / (24.0 * 30.0)
                else:
                    r.duration = 0.0
            else:
                r.duration = 0.0

    @api.depends("pricing_type", "hours_qty", "days_qty", "weeks_qty", "months_qty", "unit_price")
    def _compute_total_price(self):
        for r in self:
            if r.pricing_type == "hourly":
                qty = float(r.hours_qty or "0")
            elif r.pricing_type == "daily":
                qty = float(r.days_qty or "0")
            elif r.pricing_type == "weekly":
                qty = float(r.weeks_qty or "0")
            elif r.pricing_type == "monthly":
                qty = float(r.months_qty or "0")
            else:
                qty = 0.0

            r.total_price = max(0.0, (qty or 0.0) * (r.unit_price or 0.0))


    @api.depends("extra_product_ids")
    def _compute_extras_total(self):
        """Somme des prix des accessoires sélectionnés (1 unité par produit)."""
        for r in self:
            total = 0.0
            for p in r.extra_product_ids:
                if "list_price" in p._fields:
                    total += p.list_price or 0.0
                elif "sale_price" in p._fields:
                    total += p.sale_price or 0.0
            r.extras_total = total

    @api.depends("total_price", "deposit_amount", "additional_charges", "extras_total", "manual_extra_amount")
    def _compute_total_amount(self):
        for r in self:
            r.total_amount = (
                (r.total_price or 0.0)
                + (r.deposit_amount or 0.0)
                + (r.additional_charges or 0.0)
                + (r.extras_total or 0.0)
                + (r.manual_extra_amount or 0.0)
            )

    @api.depends("extras_total", "manual_extra_amount")
    def _compute_extras_grand_total(self):
        for r in self:
            r.extras_grand_total = (r.extras_total or 0.0) + (r.manual_extra_amount or 0.0)

    # -----------------------------
    # DISPONIBILITÉ
    # -----------------------------
    @api.constrains("product_id", "start_date", "end_date", "state")
    def _check_availability(self):
        for r in self:
            if r.state in ["draft", "ongoing"] and r.product_id and r.start_date and r.end_date:
                if r.product_id.available_quantity < 1:
                    overlapping = self.search([
                        ("id", "!=", r.id),
                        ("product_id", "=", r.product_id.id),
                        ("state", "in", ["draft", "ongoing"]),
                        "|",
                        "&", ("start_date", "<=", r.start_date), ("end_date", ">", r.start_date),
                        "&", ("start_date", "<", r.end_date), ("end_date", ">=", r.end_date),
                    ], limit=1)
                    if overlapping:
                        raise exceptions.ValidationError(_(
                            "Le produit %(product)s n’est pas disponible pour la période sélectionnée !"
                        ) % {"product": r.product_id.name})

    # -----------------------------
    # ACTIONS
    # -----------------------------
    def action_start_rental(self):
        for r in self:
            if r.state != "draft":
                raise exceptions.ValidationError(_("Seules les locations en brouillon peuvent être démarrées !"))
            if r.product_id.available_quantity < 1:
                raise exceptions.ValidationError(_(
                    "Le produit %(product)s n’est pas disponible !"
                ) % {"product": r.product_id.name})
            r.state = "ongoing"

    def action_return_bike(self):
        for r in self:
            if r.state != "ongoing":
                raise exceptions.ValidationError(_("Seules les locations en cours peuvent être retournées !"))

            now = fields.Datetime.now()

            if r.end_date and now > r.end_date:
                late_duration = (now - r.end_date).total_seconds() / 3600.0
                if r.pricing_type == "daily":
                    late_days = late_duration / 24.0
                    r.additional_charges += late_days * (r.unit_price or 0.0) * 1.5

            r.state = "returned"

    def action_cancel(self):
        for r in self:
            if r.state == "returned":
                raise exceptions.ValidationError(_("Impossible d’annuler une location retournée !"))
            r.state = "cancelled"

    def action_set_draft(self):
        for r in self:
            if r.state != "cancelled":
                raise exceptions.ValidationError(_("Seules les locations annulées peuvent repasser en brouillon !"))
            r.state = "draft"

    # -----------------------------
    # FACTURATION
    # -----------------------------
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

        if "account_type" in Account._fields:
            domain.append(("account_type", "=", "income"))
        elif "internal_group" in Account._fields:
            domain.append(("internal_group", "=", "income"))

        if "active" in Account._fields:
            domain.append(("active", "=", True))
        if "deprecated" in Account._fields:
            domain.append(("deprecated", "=", False))

        if "company_id" in Account._fields:
            domain.append(("company_id", "=", self.env.company.id))
        elif "company_ids" in Account._fields:
            domain.append(("company_ids", "in", self.env.company.id))

        acc = Account.search(domain, limit=1)
        if not acc:
            raise ValidationError(_("Aucun compte de revenu (income) trouvé."))
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

        # Accessoires (1 unité par produit)
        for p in self.extra_product_ids:
            price = 0.0
            if "list_price" in p._fields:
                price = p.list_price or 0.0
            elif "sale_price" in p._fields:
                price = p.sale_price or 0.0

            if price:
                line_vals.append({
                    "name": _("Accessoire / pièce: %s") % (p.name),
                    "quantity": 1.0,
                    "price_unit": price,
                    "account_id": income_account.id,
                    "tax_ids": [(6, 0, tax.ids)] if tax else False,
                })

        # Frais manuels
        if self.manual_extra_amount:
            line_vals.append({
                "name": _("Frais supplémentaires (manuel)"),
                "quantity": 1.0,
                "price_unit": self.manual_extra_amount,
                "account_id": income_account.id,
                "tax_ids": [(6, 0, tax.ids)] if tax else False,
            })

        # Retard / dommages
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
