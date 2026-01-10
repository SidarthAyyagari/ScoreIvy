#!/bin/bash

# ScoreIvy Database Wipe Script
# This script wipes all data from all tables in the database
# Use with caution!

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  WARNING: This will delete ALL data from the database!${NC}"
echo -e "${YELLOW}Are you sure you want to continue? (yes/no)${NC}"
read -r confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${GREEN}Cancelled. No data was deleted.${NC}"
    exit 0
fi

echo -e "${YELLOW}Wiping all tables...${NC}"

# Execute the wipe script
docker exec -i scoreivy-postgres psql -U postgres -d scoreivy < database/07_wipe_all_tables.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tables wiped successfully!${NC}"
    echo -e "${YELLOW}You may want to restart the backend to reload initial data.${NC}"
else
    echo -e "${RED}❌ Error wiping tables.${NC}"
    exit 1
fi

