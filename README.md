# Bike Shop - Module Odoo ERP

Module complet de gestion de vélos avec vente et location pour Odoo.

## Technologies Utilisées

- **Odoo**: 17.0 (Framework ERP)
- **Python**: 3.12
- **PostgreSQL**: 15
- **Docker**: Pour la conteneurisation
- **Docker Compose**: Pour l'orchestration des services

## Dépendances Odoo

### Modules Requis

Ce module nécessite les modules standards Odoo suivants :

- **base**: Module de base Odoo (inclus par défaut)
- **calendar**: Module de calendrier pour planifier les locations
- **contacts**: Gestion des contacts et partenaires
- **crm**: CRM pour la gestion de la relation client
- **sale_management**: Module de vente Odoo pour la gestion des commandes
- **board**: Tableaux de bord et reporting
- **account**: Module de comptabilité pour la facturation
- **website**: Site web et e-commerce
- **stock**: Module de gestion de stock/inventaire
- **link_tracker**: Suivi des liens et campagnes marketing

**Note**: Lors de l'installation du module Bike Shop, tous ces modules seront automatiquement installés s'ils ne le sont pas déjà.

### Librairies Python

Ce module utilise uniquement les librairies Python incluses dans Odoo :
- `datetime`: Gestion des dates et heures
- Odoo framework APIs: `models`, `fields`, `api`, `exceptions`

**Note**: Aucune librairie externe n'est requise au-delà de celles fournies par Odoo.

## Intégration avec les Modules Odoo

### Intégration Sales & Inventory (Ventes & Inventaire)

Le module s'intègre avec les modules Sales et Stock d'Odoo :
- Gestion automatique du stock lors des ventes
- Possibilité de lier les produits aux produits Odoo (product.template)
- Réservation automatique du stock pour les locations

### Intégration Accounting (Comptabilité)

Le module offre une intégration complète avec le module Accounting :
- **Création de factures** : Générez des factures Odoo directement depuis les contrats de location
- **Facturation automatique** : Inclut le prix de location et les frais supplémentaires
- **Frais de retard** : Calcul automatique et ajout aux factures

Pour créer une facture depuis une location :
1. Ouvrez un contrat de location (état "Ongoing" ou "Returned")
2. Cliquez sur "Create Invoice"
3. La facture sera créée automatiquement dans le module Accounting

### Intégration Calendar (Calendrier)

Le module s'intègre avec le module Calendar d'Odoo :
- **Événements calendrier** : Créez des événements pour suivre les périodes de location
- **Vue calendrier** : Visualisez toutes les locations dans une vue calendrier mensuelle
- **Synchronisation** : Les dates de début et fin sont automatiquement synchronisées

Pour ajouter une location au calendrier :
1. Ouvrez un contrat de location
2. Cliquez sur "Add to Calendar"
3. Un événement sera créé dans votre calendrier Odoo

### Intégration Contacts

Le module permet de lier les clients aux contacts Odoo (res.partner) :
- **Synchronisation bidirectionnelle** : Importez les informations depuis les contacts Odoo
- **Création automatique** : Créez un contact Odoo depuis un client Bike Shop
- **Utilisation dans factures** : Les contacts liés sont utilisés automatiquement pour la facturation

## Sources et Références

Ce module a été développé en utilisant :
- [Documentation officielle Odoo](https://www.odoo.com/documentation/17.0/)
- [Odoo Technical Documentation](https://www.odoo.com/documentation/17.0/developer.html)
- Framework Odoo ORM pour la gestion des modèles et vues

**Aucun code tiers** n'a été utilisé. Tout le code est original et développé spécifiquement pour ce projet.

---

### URL d'accès

```
http://localhost:8069
```

## Première Configuration

### Étape 1: Créer la Base de Données

1. Ouvrez votre navigateur et allez sur `http://localhost:8069`
2. Cliquez sur "Create Database"
3. Remplissez le formulaire :
   - **Master Password**: `admin` (à changer en production)
   - **Database Name**: `bike_shop`
   - **Email**: `odoo`
   - **Password**: `odoo`
   - **Language**: English
   - **Country**: Belgium
   - **Demo data**: Cochez cette case pour charger les données de démonstration

4. Cliquez sur "Continue" et attendez (peut prendre 2-3 minutes)

### Étape 2: Installer le Module Bike Shop

Une fois connecté :

1. Allez dans le menu **Apps** (Applications)
2. Supprimez le filtre "Apps" dans la barre de recherche
3. Recherchez "Bike Shop"
4. Cliquez sur **Install** (Installer)
5. Attendez la fin de l'installation

### Étape 3: Vérification

Après l'installation, vous devriez voir un menu "Bike Shop" dans la barre de navigation avec :

- **Catalog** : Catégories, Modèles de vélos, Produits
- **Sales** : Commandes de vente
- **Rentals** : Contrats de location
- **Customers** : Clients
- **Reporting** : Rapports

## Données de Démonstration

Si vous avez activé les données de démonstration, vous aurez :

### Produits
- 4 vélos (City, Mountain, Electric)
- 3 accessoires (Casque, Cadenas, Lumières)
- 2 pièces détachées (Pneus, Plaquettes de frein)

### Clients
- John Doe
- Jane Smith
- Bob Johnson

### Commandes de Vente
- 2 commandes avec différents états

### Locations
- 3 contrats de location (en cours, terminés, brouillon)

## Gestion du Système

### Arrêter Odoo

```bash
docker-compose stop
```

### Démarrer Odoo

```bash
docker-compose start
```

### Redémarrer Odoo

```bash
docker-compose restart
```

### Voir les logs

```bash
docker-compose logs -f odoo
```

### Arrêter et supprimer tout

```bash
docker-compose down
# Pour supprimer aussi les données :
docker-compose down -v
```

## Fonctionnalités Principales

### 1. Gestion des Locations

- **Tarification flexible** : Tarifs horaires, journaliers, hebdomadaires, mensuels
- **Suivi complet** : États (Brouillon, En cours, Retourné, Annulé)
- **Frais de retard** : Calcul automatique (150% du tarif normal)
- **Vérification disponibilité** : Contrôle automatique des chevauchements
- **Filtres avancés** : Filtrez par état (en cours, brouillon, retourné), client, produit
- **Vue calendrier** : Visualisez toutes les locations dans un calendrier mensuel

### 2. Intégration Comptabilité

- Génération de factures depuis les contrats de location
- Inclusion automatique des frais supplémentaires
- Lien avec les contacts Odoo pour la facturation

### 3. Gestion du Stock

- Gestion des quantités en stock
- Calcul automatique des quantités disponibles
- Réservation automatique pour les locations actives

## Cas d'Usage Typiques

### Créer une Vente

1. **Sales → Sale Orders → Create**
2. Sélectionnez un client
3. Ajoutez des lignes de commande (produits)
4. Cliquez sur **Confirm Order**
5. Le stock sera automatiquement mis à jour

### Créer une Location avec Facture

1. **Rentals → Rental Contracts → Create**
2. Sélectionnez un client
3. Choisissez un vélo (seuls les produits disponibles à la location sont affichés)
4. Définissez les dates de début et fin (par défaut : aujourd'hui)
5. Choisissez le type de tarification (heure/jour/semaine/mois)
6. Cliquez sur **Start Rental** au moment du retrait
7. *Optionnel* : Cliquez sur **Create Invoice** pour générer une facture
8. *Optionnel* : Cliquez sur **Add to Calendar** pour ajouter au calendrier
9. Cliquez sur **Return Bike** au retour

### Filtrer les Locations en Cours

1. **Rentals → Rental Contracts**
2. Dans la barre de recherche, cliquez sur les filtres
3. Sélectionnez **"Ongoing"** pour voir uniquement les locations en cours
4. Autres filtres disponibles : Draft, Returned, Unpaid

### Gérer le Stock

1. **Catalog → Products**
2. Sélectionnez un produit
3. Modifiez le champ "Stock Quantity"
4. Le système calcule automatiquement la quantité disponible (stock - réservations)

## Dépannage

### Le module n'apparaît pas

```bash
docker-compose restart odoo
```

Puis dans Odoo : **Apps → Update Apps List**

### Erreur de connexion à la base de données

Vérifiez que PostgreSQL est en cours d'exécution :

```bash
docker-compose ps
```

### Problème de permissions

Vérifiez les permissions du dossier :

```bash
chmod -R 777 custom_addons
```

## Structure du Projet

```
BikeShop/
├── custom_addons/
│   └── bike_manager/          # Module Odoo
│       ├── models/            # Logique métier
│       ├── views/             # Interface utilisateur
│       ├── security/          # Droits d'accès
│       ├── data/              # Données maître
│       └── demo/              # Données de démonstration
├── docker-compose.yml         # Configuration Docker
└── README.md                  # Documentation complète

```