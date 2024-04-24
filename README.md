# WoningBot
A simple yet effective web scraper Discord bot that checks for available rental properties in the netherlands every 4 minutes.
Subscribers of the discord bot will be notified when a new property is available, if it meets the set filters.

Currently, the following websites are being scraped:
- [BurgersDijk](https://burgersdijk.com/)
- [Funda](https://www.funda.nl/)
- [IkWilHuren](https://ikwilhuren.nu/)
- [Pararius](https://www.pararius.nl/)
- [Rebo](https://www.rebohuurwoning.nl/)
- [Nijland](https://www.nijland.nl/)
- [Boon](https://www.boonmakelaars.nl/)
- [HouseHunting](https://househunting.nl/)
- [Domica](https://www.domica.nl/)

## Setup
To subscribe to the discord bot, invite it to a channel using the following link: https://discord.com/oauth2/authorize?client_id=1213808680869437460


Once the bot has been added to a channel, you can use the following command to get notified when a new property is available:

```
/subscribe min_price 0 max_price 2000 city amsterdam radius 5
```

You can also use some of the other commands to interact with the bot:

- `/help`: Get a list of all commands
- `/websites`: Get a list of all websites that are visited by the bot
- `/subscribe`: Subscribe to get updates from the bot when a house is found.
  - `min_price`: minimum price of the house
  - `max_price`: maximum price of the house
  - `min_rooms`: minimum amount of rooms
  - `max_rooms`: maximum amount of rooms
  - `min_sqm`: minimum square meters
  - `max_sqm`: maximum square meters
  - `city`: city where the house should be located
  - `radius`: radius in KM around the city where the house should be located
- `/unsubscribe`: Unsubscribe from the updates from the bot

## Contributions
This repository heavily relies on contributions from the community. If you think you can improve the bot, or you would like to add a website to be scraped, please do not hesitate to create a pull request.

In the case you would like to add additional websites to be scraped, simply create a new `BaseSite` child class in the `app/sites` folder, and add it to the `sites` list in the `app/sites/__init__.py` file.
The scraper will automatically pick up the new website and start scraping it once the changes are pushed to main.

## Donations
If you would like to support the development of this bot and the servers it is running on, you can do so by donating here:  

<a href="https://www.paypal.com/donate/?hosted_button_id=ZXGUR3NKBZEEN"><img src="https://github.com/andreostrovsky/donate-with-paypal/blob/925c5a9e397363c6f7a477973fdeed485df5fdd9/PNG/blue.png" height="72"></a>

Even the smallest donation is greatly appreciated!