# Migration Guide: Directory Structure Changes

This guide helps you migrate existing quickpage installations to the new directory structure.

## Overview of Changes

The quickpage application has been updated to organize output files more logically:

- **Neuron pages** moved from `output/` to `output/types/`
- **Eyemap images** moved from `output/static/images/` to `output/eyemaps/`
- **Main pages** remain in `output/` (index.html, types.html, help.html)

## Migration Steps

### For Development/Local Installations

1. **Backup your existing output directory**:
   ```bash
   cp -r output output_backup
   ```

2. **Move neuron pages to types/ subdirectory**:
   ```bash
   # Create the types directory
   mkdir -p output/types
   
   # Move all neuron HTML files (excluding main pages)
   find output -maxdepth 1 -name "*.html" \
     ! -name "index.html" \
     ! -name "types.html" \
     ! -name "help.html" \
     -exec mv {} output/types/ \;
   ```

3. **Move eyemap images to eyemaps/ subdirectory**:
   ```bash
   # Create the eyemaps directory
   mkdir -p output/eyemaps
   
   # Move images from static/images to eyemaps
   if [ -d "output/static/images" ]; then
     mv output/static/images/* output/eyemaps/ 2>/dev/null || true
     rmdir output/static/images 2>/dev/null || true
   fi
   ```

4. **Regenerate the index and search files**:
   ```bash
   # Regenerate the types list with new structure
   python -m quickpage create-list
   ```

### For Production/Server Deployments

1. **Plan for brief downtime** during migration

2. **Create deployment script**:
   ```bash
   #!/bin/bash
   # migration_script.sh
   
   BACKUP_DIR="output_backup_$(date +%Y%m%d_%H%M%S)"
   
   echo "Creating backup..."
   cp -r output "$BACKUP_DIR"
   
   echo "Creating new directory structure..."
   mkdir -p output/types
   mkdir -p output/eyemaps
   
   echo "Moving neuron pages..."
   find output -maxdepth 1 -name "*.html" \
     ! -name "index.html" \
     ! -name "types.html" \
     ! -name "help.html" \
     -exec mv {} output/types/ \;
   
   echo "Moving eyemap images..."
   if [ -d "output/static/images" ]; then
     mv output/static/images/* output/eyemaps/ 2>/dev/null || true
     rmdir output/static/images 2>/dev/null || true
   fi
   
   echo "Regenerating index files..."
   python -m quickpage create-list
   
   echo "Migration complete. Backup saved as: $BACKUP_DIR"
   ```

3. **Update web server configuration** (if needed):
   
   **Apache (.htaccess)**:
   ```apache
   # Redirect old neuron page URLs to new location
   RewriteEngine On
   
   # Redirect neuron pages (excluding main pages) to types/ subdirectory
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteRule ^([^/]+\.html)$ types/$1 [R=301,L]
   RewriteCond %{REQUEST_URI} !^/(index|types|help)\.html$
   
   # Redirect old image paths to new eyemaps location
   RewriteRule ^static/images/(.+)$ eyemaps/$1 [R=301,L]
   ```
   
   **Nginx**:
   ```nginx
   # Redirect old neuron page URLs to new location
   location ~ ^/([^/]+\.html)$ {
       if ($uri !~ ^/(index|types|help)\.html$) {
           return 301 /types$uri;
       }
   }
   
   # Redirect old image paths to new eyemaps location
   location ~ ^/static/images/(.+)$ {
       return 301 /eyemaps/$1;
   }
   ```

## Verification Steps

After migration, verify that everything works correctly:

1. **Check directory structure**:
   ```bash
   ls -la output/
   # Should show: index.html, types.html, help.html, types/, eyemaps/, static/
   
   ls -la output/types/
   # Should show: all neuron HTML files
   
   ls -la output/eyemaps/
   # Should show: all eyemap images (.svg, .png files)
   ```

2. **Test main page navigation**:
   - Open `output/index.html` in browser
   - Verify links to types.html and help.html work
   - Test search functionality
   - Verify links to neuron pages work (should go to types/ subdirectory)

3. **Test neuron page navigation**:
   - Open any neuron page in `output/types/`
   - Verify navigation links back to main pages work
   - Check that eyemap images display correctly
   - Test soma side navigation between neuron variants

4. **Check for broken links**:
   ```bash
   # Simple link checker (requires lynx or similar)
   find output -name "*.html" -exec echo "Checking {}" \; \
     -exec lynx -dump {} \; | grep -i "not found\|404\|error"
   ```

## Rollback Plan

If issues occur, you can rollback using your backup:

```bash
# Stop web server (if applicable)
sudo systemctl stop apache2  # or nginx

# Restore from backup
rm -rf output
mv output_backup output

# Restart web server
sudo systemctl start apache2  # or nginx
```

## Common Issues and Solutions

### Issue: Links to neuron pages return 404

**Cause**: Web server not configured for new directory structure  
**Solution**: Update web server config or add URL redirects

### Issue: Images not displaying on neuron pages

**Cause**: Eyemap images not moved correctly  
**Solution**: Verify images are in `output/eyemaps/` and paths in HTML are correct

### Issue: Search functionality not working

**Cause**: neuron-search.js not updated with new paths  
**Solution**: Regenerate the site with `python -m quickpage create-list`

### Issue: Broken navigation between neuron pages

**Cause**: Relative links not updated  
**Solution**: Regenerate neuron pages with updated quickpage version

## Testing Checklist

- [ ] Main pages (index, types, help) accessible
- [ ] Search functionality works
- [ ] Links from main pages to neuron pages work
- [ ] Links from neuron pages back to main pages work
- [ ] Eyemap images display correctly
- [ ] Soma side navigation works
- [ ] External links (neuPrint, GitHub) work
- [ ] Mobile navigation works
- [ ] Browser back/forward navigation works

## Support

If you encounter issues during migration:

1. Check the backup was created successfully
2. Verify file permissions are correct
3. Check web server error logs
4. Test with a simple HTTP server: `python -m http.server 8000`
5. Compare your structure with the expected layout

## Post-Migration Benefits

After successful migration, you'll have:

- **Cleaner URLs**: Neuron pages organized under `/types/`
- **Better organization**: Logical separation of content types
- **Easier maintenance**: Simplified file management
- **Improved SEO**: Better URL structure for search engines
- **Future-proof structure**: Ready for additional content organization