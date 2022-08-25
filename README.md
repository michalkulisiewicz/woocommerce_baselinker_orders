# woocommerce_baselinker_orders
<img src="misc/logo.png" width="400"/>

Script used to fetch orders from baselinker to woocommerce shop, uses both baselinker and woocmommerce api.
It checks every 15 minutes for new orders in specified status.
If an order appears in a baselinker it's added to woocommers store.
After creating order in woocommerce, baselinker status is changed for specifed by the user in config file.

## Installation
Use git clone to get the script:

```shell
git clone https://github.com/michalkulisiewicz/woocommerce_baselinker_orders.git
```

Install all requirements using pip:

```shell
pip install -r requirements.txt
```
## Configuration 
In order to run the script you need to edit config.json file and 
provide all necessary information

## Running script
Just run main.py file.

## Contributing

Bug reports and pull requests are welcome on GitHub at
https://github.com/michalkulisiewicz/woocommerce_baselinker_orders. This project is intended to be a safe, welcoming space for collaboration, and contributors are expected to adhere to the [code of conduct](https://github.com/michalkulisiewicz/baselinker_subiekt_integrator/blob/master/CODE_OF_CONDUCT.md).

## License

Project is available as open source under the terms of the [MIT License](https://opensource.org/licenses/MIT).

## Code of Conduct

Everyone that interacts in the project codebase, issue trackers, chat rooms and mailing lists is expected to follow the [code of conduct](https://github.com/michalkulisiewicz/woocommerce_baselinker_orders/blob/master/CODE_OF_CONDUCT.md)