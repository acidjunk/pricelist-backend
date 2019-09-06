echo "Dropping"
dropdb pricelist
echo "Creating"
createdb pricelist
echo "Populating"
psql -d pricelist < pricelist_prod.psql
