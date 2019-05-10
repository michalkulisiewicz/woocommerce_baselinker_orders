# woocommerce_baselinker_orders
Script used to fetch orders from baselinker to woocommerce shop uses both baselinker and woocmommerce api.
It checks every 15 minutes for new orders in specified status in baselinker (default is: 'Dostaw Przez Sprzedającego')
When there is an order in a status it's added to woocommers shop and changes his baselinker status for specifed (default is : 'Archiwum wysłanych')
*In order to install all dependencies use command: pip install -r requirements.txt*
