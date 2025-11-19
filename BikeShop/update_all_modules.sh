#!/bin/bash
# ─────────────────────────────────────────────
# Colored script to update all custom Odoo modules
# ─────────────────────────────────────────────

# ─── Configuration ───────────────────────────
DB_NAME="odoo19"
ODOO_CONTAINER="ProjectOdoo_BikeShop"
CUSTOM_ADDONS_PATH="/mnt/extra-addons"

# ─── Colors ──────────────────────────────────
RED="\e[31m"
GREEN="\e[32m"
YELLOW="\e[33m"
BLUE="\e[34m"
CYAN="\e[36m"
BOLD="\e[1m"
RESET="\e[0m"

# ─── Script ──────────────────────────────────
echo -e "${CYAN}${BOLD}Searching for custom modules in${RESET} ${YELLOW}$CUSTOM_ADDONS_PATH${RESET} ..."
MODULES=$(docker exec $ODOO_CONTAINER bash -c "ls -d $CUSTOM_ADDONS_PATH/*/ | xargs -n 1 basename")

echo -e "${BLUE}-------------------------------------------------${RESET}"
echo -e "${BOLD}Modules found:${RESET}"
for MODULE in $MODULES; do
    echo -e "  - ${GREEN}$MODULE${RESET}"
done
echo -e "${BLUE}-------------------------------------------------${RESET}"

echo -e "${CYAN}${BOLD}Starting module updates...${RESET}"

for MODULE in $MODULES; do
    echo -e "${YELLOW}Updating module '${BOLD}$MODULE${RESET}${YELLOW}'...${RESET}"

    docker exec -i $ODOO_CONTAINER \
        odoo -u $MODULE -d $DB_NAME \
        --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo --no-http > /dev/null 2>&1 &

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✔ '${BOLD}$MODULE${RESET}${GREEN}' updated successfully.${RESET}"
    else
        echo -e "${RED}✖ Error while updating module '${BOLD}$MODULE${RESET}${RED}'.${RESET}"
    fi
done

echo -e "${BLUE}-------------------------------------------------${RESET}"
echo -e "${BOLD}${GREEN}All modules have been updated successfully.${RESET}"
echo -e "${BLUE}-------------------------------------------------${RESET}"
