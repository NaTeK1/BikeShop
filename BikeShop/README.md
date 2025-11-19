# Project BikeShop

This project implements an **Odoo 19.0 Community** application for the **sale and rental of bicycles**.

## Objectives

- Sale of bicycles and accessories  
- Short- or long-term rentals  
- Customer and contract management  
- Basic reporting on sales and rentals  

## Prerequisites

Make sure you have installed:
- **Docker Desktop**
- **GitHub Desktop**

## Installation

1) **Launch** : Once installed, unzip the .zip file.
```bash
docker compose up -d
```

2) Open **http://localhost:8069** and create the database `odoo19`
3) Activate the modules  **Sales**, **Inventory**, **Contacts**, **Accounting** and **bike_shop** (dans Apps)

> If you do not see the module, click *Update Apps List*

## Commandes utiles

```bash
# Restart Odoo
docker compose restart odoo

# View logs
docker compose logs -f odoo

# Stop all containers
docker compose down

# Remove containers + database volume
docker compose down -v

# update from module
./odoo-bin -d odoo19 -u bike_shop

# Script update module (Can close after update CTRL+C)
bash ./update_all_modules.sh

```