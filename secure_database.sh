#!/bin/bash

# HadadaHealth Database Security Script
# This script ensures database files have secure permissions for POPIA compliance

echo "🔐 Securing HadadaHealth database files..."

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Set secure permissions on data directory (owner only access)
echo "🔒 Securing data directory permissions..."
chmod 700 data/

# Set secure permissions on database files
echo "🔒 Securing database file permissions..."

if [ -f "data/bookings.db" ]; then
    chmod 600 data/bookings.db
    echo "✅ bookings.db permissions set to 600 (owner read/write only)"
else
    echo "⚠️  bookings.db not found - will be created with secure permissions"
fi

if [ -f "data/icd10_with_pmb.db" ]; then
    chmod 600 data/icd10_with_pmb.db
    echo "✅ icd10_with_pmb.db permissions set to 600 (owner read/write only)"
else
    echo "⚠️  icd10_with_pmb.db not found"
fi

# Verify permissions
echo ""
echo "📋 Current database file permissions:"
ls -la data/ 2>/dev/null || echo "No data directory found"

echo ""
echo "🛡️  Database security applied successfully!"
echo "📝 Note: These permissions prevent other system users from accessing patient data"
echo "📝 POPIA Compliance: Patient database files are now properly secured"

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  WARNING: Running as root. Consider running as dedicated application user for better security."
fi