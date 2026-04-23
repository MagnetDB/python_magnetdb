#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
CONTAINER_NAME="magnetdb-postgres"
DB_NAME="${POSTGRES_DB:-magnetdb}"
DB_USER="${POSTGRES_USER:-magnetuser}"

# Function to print usage
usage() {
    echo "Usage: $0 <username> <new_role>"
    echo ""
    echo "Change the role of a user in the database"
    echo ""
    echo "Arguments:"
    echo "  username   - The username to modify"
    echo "  new_role   - The new role to assign (e.g., admin, user, readonly)"
    echo ""
    echo "Examples:"
    echo "  $0 john.doe admin"
    echo "  $0 jane.smith user"
    exit 1
}

# Check arguments
if [ $# -ne 2 ]; then
    usage
fi

USERNAME="$1"
NEW_ROLE="$2"

echo -e "${YELLOW}Changing role for user '$USERNAME' to '$NEW_ROLE'...${NC}"

# Check if running in Docker
if command -v docker &> /dev/null && docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Using Docker container: $CONTAINER_NAME"
    
    # First, show current user info
    echo -e "\n${YELLOW}Current user information:${NC}"
    docker exec -it "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT id, username, email, role FROM users WHERE username = '$USERNAME';"
    
    # Update the role
    echo -e "\n${YELLOW}Updating role...${NC}"
    docker exec -it "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c \
        "UPDATE users SET role = '$NEW_ROLE' WHERE username = '$USERNAME';"
    
    # Show updated user info
    echo -e "\n${GREEN}Updated user information:${NC}"
    docker exec -it "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT id, username, email, role FROM users WHERE username = '$USERNAME';"
    
    echo -e "\n${GREEN}✓ Role updated successfully!${NC}"
else
    # Running directly on host
    echo "Using local PostgreSQL installation"
    
    # First, show current user info
    echo -e "\n${YELLOW}Current user information:${NC}"
    psql -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT id, username, email, role FROM users WHERE username = '$USERNAME';"
    
    # Update the role
    echo -e "\n${YELLOW}Updating role...${NC}"
    psql -U "$DB_USER" -d "$DB_NAME" -c \
        "UPDATE users SET role = '$NEW_ROLE' WHERE username = '$USERNAME';"
    
    # Show updated user info
    echo -e "\n${GREEN}Updated user information:${NC}"
    psql -U "$DB_USER" -d "$DB_NAME" -c \
        "SELECT id, username, email, role FROM users WHERE username = '$USERNAME';"
    
    echo -e "\n${GREEN}✓ Role updated successfully!${NC}"
fi
