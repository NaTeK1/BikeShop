from odoo import models, fields, api, exceptions, _


class BikeItem(models.Model):
    """
    Représente un vélo individuel avec numéro de série unique.
    Ce modèle permet de suivre chaque vélo spécifique (comme dans un vrai magasin).
    """
    _name = "bike.item"
    _description = "Vélo individuel"
    _order = "serial_number"
    _inherit = ["image.mixin", "mail.thread", "mail.activity.mixin"]

    # Identification unique
    name = fields.Char(
        string="Nom",
        compute="_compute_name",
        store=True,
        readonly=True
    )
    serial_number = fields.Char(
        string="Numéro de série",
        required=True,
        copy=False,
        help="Numéro de série unique du vélo (comme sur le cadre)"
    )

    # Lien vers le modèle de produit (template)
    product_id = fields.Many2one(
        "bike.product",
        string="Modèle de vélo",
        required=True,
        ondelete="restrict",
        domain="[('product_type', '=', 'bike')]",
        help="Le modèle de vélo (ex: VTT Giant Talon 2024)"
    )

    # Héritage d'infos depuis le produit
    bike_model_id = fields.Many2one(
        related="product_id.bike_model_id",
        string="Modèle",
        store=True,
        readonly=True
    )
    category_id = fields.Many2one(
        related="product_id.category_id",
        string="Catégorie",
        store=True,
        readonly=True
    )

    # Image spécifique (sinon hérite du produit)
    image_1920 = fields.Image(
        string="Image du vélo",
        max_width=1920,
        max_height=1920,
        help="Photo de ce vélo spécifique (optionnel, sinon utilise l'image du modèle)"
    )

    # Usage du vélo
    usage_type = fields.Selection([
        ('sale', 'Vente uniquement'),
        ('rental', 'Location uniquement'),
        ('both', 'Vente et location'),
    ], string="Usage", required=True, default='rental',
        help="Définit si ce vélo est destiné à la vente, à la location, ou les deux")

    # État physique du vélo
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Bon'),
        ('fair', 'Usure normale'),
        ('poor', 'Réparation nécessaire'),
    ], string="État physique", default='excellent', required=True,
        help="État général du vélo")

    # Statut opérationnel
    status = fields.Selection([
        ('available', 'Disponible'),
        ('rented', 'Loué'),
        ('reserved', 'Réservé'),
        ('maintenance', 'En maintenance'),
        ('sold', 'Vendu'),
    ], string="Statut", default='available', required=True,
        compute="_compute_status", store=True, readonly=False, tracking=True,
        help="Statut actuel du vélo dans le système")

    # Prix et dates
    purchase_price = fields.Float(
        string="Prix d'achat",
        help="Prix auquel le vélo a été acheté par le magasin"
    )
    purchase_date = fields.Date(
        string="Date d'acquisition",
        default=fields.Date.context_today,
        help="Date à laquelle le vélo a été acquis"
    )

    # Prix de vente (peut différer du produit template)
    sale_price = fields.Float(
        string="Prix de vente",
        compute="_compute_sale_price",
        store=True,
        readonly=False,
        help="Prix de vente de ce vélo spécifique (par défaut = prix du modèle)"
    )

    # Localisation dans le magasin
    location = fields.Char(
        string="Emplacement",
        help="Emplacement physique dans le magasin (ex: Rayon A, Étagère 3)"
    )

    # Notes et maintenance
    notes = fields.Text(string="Notes")
    maintenance_notes = fields.Text(
        string="Historique de maintenance",
        help="Notes sur les réparations et entretiens effectués"
    )
    last_maintenance_date = fields.Date(string="Dernière maintenance")
    next_maintenance_date = fields.Date(
        string="Prochaine maintenance prévue",
        help="Date recommandée pour la prochaine révision"
    )

    # Relations
    rental_ids = fields.One2many(
        'bike.rental',
        'bike_item_id',
        string="Historique des locations",
        help="Liste de toutes les locations de ce vélo"
    )
    current_rental_id = fields.Many2one(
        'bike.rental',
        string="Location en cours",
        compute="_compute_current_rental",
        help="Location active de ce vélo"
    )

    # Statistiques
    rental_count = fields.Integer(
        string="Nombre de locations",
        compute="_compute_rental_count",
        store=True,
        help="Nombre total de fois que ce vélo a été loué"
    )
    total_rental_revenue = fields.Float(
        string="Revenu total (location)",
        compute="_compute_total_rental_revenue",
        help="Revenu total généré par la location de ce vélo"
    )

    active = fields.Boolean(string="Actif", default=True)

    _sql_constraints = [
        ('serial_number_unique', 'unique(serial_number)',
         'Le numéro de série doit être unique !')
    ]

    @api.depends('product_id', 'serial_number')
    def _compute_name(self):
        """Génère un nom lisible pour le vélo"""
        for item in self:
            if item.product_id and item.serial_number:
                item.name = f"{item.product_id.name} - {item.serial_number}"
            elif item.serial_number:
                item.name = item.serial_number
            else:
                item.name = "Nouveau vélo"

    @api.depends('product_id', 'product_id.sale_price')
    def _compute_sale_price(self):
        """Initialise le prix de vente depuis le produit"""
        for item in self:
            if not item.sale_price and item.product_id:
                item.sale_price = item.product_id.sale_price

    @api.depends('rental_ids', 'rental_ids.state', 'usage_type', 'condition')
    def _compute_status(self):
        """Calcule le statut en fonction des locations actives et de l'état physique"""
        for item in self:
            # Si vendu, toujours vendu
            if item.status == 'sold':
                continue

            # Vérifie s'il y a une location active
            active_rental = item.rental_ids.filtered(
                lambda r: r.state == 'ongoing'
            )
            reserved_rental = item.rental_ids.filtered(
                lambda r: r.state == 'draft'
            )

            if active_rental:
                item.status = 'rented'
            elif reserved_rental:
                item.status = 'reserved'
            elif item.condition == 'poor':
                item.status = 'maintenance'
            else:
                # Si aucune location active et condition OK, remettre en disponible
                item.status = 'available'

    @api.depends('rental_ids')
    def _compute_current_rental(self):
        """Trouve la location en cours"""
        for item in self:
            current = item.rental_ids.filtered(
                lambda r: r.state == 'ongoing'
            )
            item.current_rental_id = current[0] if current else False

    @api.depends('rental_ids', 'rental_ids.state')
    def _compute_rental_count(self):
        """Compte le nombre de locations terminées"""
        for item in self:
            item.rental_count = len(item.rental_ids.filtered(
                lambda r: r.state == 'returned'
            ))

    @api.depends('rental_ids', 'rental_ids.total_price', 'rental_ids.state')
    def _compute_total_rental_revenue(self):
        """Calcule le revenu total de location"""
        for item in self:
            completed = item.rental_ids.filtered(
                lambda r: r.state == 'returned'
            )
            item.total_rental_revenue = sum(completed.mapped('total_price'))

    @api.constrains('usage_type', 'status')
    def _check_usage_status(self):
        """Vérifie la cohérence entre usage et statut"""
        for item in self:
            if item.usage_type == 'sale' and item.status in ['rented', 'reserved']:
                raise exceptions.ValidationError(_(
                    "Un vélo destiné uniquement à la vente ne peut pas être loué !"
                ))

    def action_mark_as_sold(self):
        """Marque le vélo comme vendu"""
        for item in self:
            if item.status == 'rented':
                raise exceptions.ValidationError(_(
                    "Impossible de vendre un vélo actuellement loué !"
                ))
            item.status = 'sold'
            item.active = False

    def action_send_to_maintenance(self):
        """Envoie le vélo en maintenance"""
        for item in self:
            if item.status == 'rented':
                raise exceptions.ValidationError(_(
                    "Impossible d'envoyer en maintenance un vélo loué !"
                ))
            item.status = 'maintenance'
            item.condition = 'poor'

    def action_return_from_maintenance(self):
        """Retour de maintenance"""
        for item in self:
            if item.status != 'maintenance':
                raise exceptions.ValidationError(_(
                    "Ce vélo n'est pas en maintenance !"
                ))
            item.status = 'available'
            item.condition = 'good'
            item.last_maintenance_date = fields.Date.context_today(self)

    def action_view_rentals(self):
        """Ouvre la liste des locations de ce vélo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Locations - %s') % self.name,
            'res_model': 'bike.rental',
            'view_mode': 'tree,form',
            'domain': [('bike_item_id', '=', self.id)],
            'context': {'default_bike_item_id': self.id},
        }
