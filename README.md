# Bike Shop Management System (Odoo) — Bike Manager

Module Odoo pour gérer un magasin de vélos : **catalogue**, **stock**, **vente**, **location**, **clients** et **reporting**.

> Note : si ton projet mentionne plusieurs versions (ex. Odoo 17 vs 19), utilise la version correspondant à ton image Docker / `docker-compose.yml`.

---

## Fonctionnalités

### Catalogue & Stock
- Catégories hiérarchiques (catégories / sous-catégories)
- Modèles de vélos (templates)
- Produits : vélos, accessoires, pièces détachées
- Stock : quantités disponibles / réservées

### Vente
- Commandes clients + workflow (Brouillon → Confirmé → Terminé/Annulé)
- Calcul automatique (TVA 21% si configurée) + méthodes de paiement (Cash, Carte, Virement)

### Location
- Contrats de location complets + états
- Tarification flexible (heure/jour/semaine/mois)
- Vérification de disponibilité (chevauchements)
- Caution + frais de retard (150% si configuré)
- Historique de location + suivi état au retrait/retour

### Clients & Reporting
- Fiches clients + historique ventes/locations
- Reporting : ventes par produit, taux d’occupation, revenus location, stats clients

### UI
- Vues : liste, formulaire, kanban (produits), calendrier, filtres/groupements, messages d’aide

---

## Modèles de données

7 modèles :
1. `bike.category`
2. `bike.model`
3. `bike.product`
4. `bike.customer`
5. `bike.sale.order`
6. `bike.sale.order.line`
7. `bike.rental`

Relations principales :
- Category (1) → (N) Product
- BikeModel (1) → (N) Product
- Customer (1) → (N) SaleOrder / Rental
- SaleOrder (1) → (N) SaleOrderLine
- Product (1) → (N) Rental / SaleOrderLine

---

## Dépendances Odoo

Modules Odoo requis (installation auto si nécessaire) :

- `base`
- `calendar`
- `contacts`
- `crm`
- `sale_management`
- `board`
- `account`
- `website`
- `stock`
- `link_tracker`

Aucune librairie Python externe : uniquement APIs Odoo + `datetime`.

---

## Installation & Lancement (Docker)

### Démarrer
```bash
docker-compose start
```

### Redémarrer
```bash
docker-compose restart
```

### Logs
```bash
docker-compose logs -f odoo
```

### Stop / Down
```bash
docker-compose stop
docker-compose down
docker-compose down -v   # supprime aussi les données
```

---

## Première configuration

### 1) Créer la base de données
Accès : `http://localhost:8069`

Exemple :
- DB : `bike_shop`
- user : `odoo`
- password : `odoo`

### 2) Installer le module
1. Apps → enlever le filtre “Apps”
2. Rechercher “Bike Shop” / “Bike Manager”
3. Install

---

## Données de démonstration

Si “Demo data” est activé : produits, clients, commandes de vente, locations (exemples).

---

## Structure du projet

```txt
BikeShop/
├── custom_addons/bike_manager/
│   ├── models/
│   ├── views/
│   ├── security/
│   ├── data/
│   ├── demo/
│   └── static/
├── docker-compose.yml
└── README.md
```

---

## Dépannage

### Le module n’apparaît pas
1. `docker-compose restart`
2. Dans Odoo : Apps → **Update Apps List**

### Erreur DB
Vérifier les services :
```bash
docker-compose ps
```

### Permissions (Linux)
```bash
chmod -R 777 custom_addons
```

---

## Améliorations possibles
- Emails automatiques
- Portail client
- Code-barres
- Maintenance
- Dashboards
- Paiements en ligne
- Multi-magasins
- Fidélité
- Tests & monitoring
- API REST
