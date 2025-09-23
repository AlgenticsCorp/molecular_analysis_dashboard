#!/bin/bash

# Grid v2 Migration Fix Script
# This script fixes MUI Grid v2 deprecation warnings by removing deprecated props

echo "Fixing MUI Grid v2 deprecation warnings..."

# Fix TaskLibrary.tsx Grid usage
if [ -f "src/pages/TaskLibrary.tsx" ]; then
    echo "Fixing src/pages/TaskLibrary.tsx..."

    # Replace Grid props that are deprecated in MUI v7
    sed -i.bak 's/<Grid container spacing={3}>/<Box sx={{ display: "flex", flexWrap: "wrap", gap: 3 }}>/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<Grid item xs={12} md={6}>/<Box sx={{ flex: "1 1 500px", minWidth: { xs: "100%", md: "50%" } }}>/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<Grid item xs={12} md={3}>/<Box sx={{ flex: "1 1 250px", minWidth: { xs: "100%", md: "25%" } }}>/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<Grid item xs={12} md={6} lg={4}/<Box sx={{ flex: "1 1 300px", minWidth: { xs: "100%", md: "50%", lg: "33.33%" } }}/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<Grid item xs={6}>/<Box sx={{ flex: "1 1 50%" }}>/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<Grid item xs={4}>/<Box sx={{ flex: "1 1 33.33%" }}>/g' src/pages/TaskLibrary.tsx
    sed -i.bak 's/<\/Grid>/<\/Box>/g' src/pages/TaskLibrary.tsx

    echo "Grid fixes applied to TaskLibrary.tsx"
    echo "Backup saved as TaskLibrary.tsx.bak"
else
    echo "TaskLibrary.tsx not found!"
fi

echo "Done! You may need to restart your dev server."
echo "To revert changes, run: mv src/pages/TaskLibrary.tsx.bak src/pages/TaskLibrary.tsx"
