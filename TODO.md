# TODO.md - Planned enhancements.

## Persistent watches and alerts

Ability to mark a watch or an alert as "persistent" so that it doesn't get deleted.

* DONE Way to delete watches and alerts as they won't disappear naturally now
* Modification to the list and show commands that mentions if they are persistent and gives the details of expiry date
* Way to mark a watch or alert as persistent, by assing a parameter to the command such as "persistent" or "persist" or "persist 1 month" or "persist forever". Thereby having an end date which will default to 1 year.
* An automated way to clean up expired persistents, with a notification so that the user knows the persistent expired. Preferablly with a warnings to that they can elect to extend it. 
* This means it needs a way to edit alerts, but I don't want to do that. Too much work.
* Way to store that watches or alerts are persistent, including when the last triggered. This is going to have to be a new separate data structure because watches and alerts are so different. It will be a dictionary tree structure with chatID at the top level, then watch/alert hash as the key at the next level, then a dictionary with persistence information:.
Example: {chatID: 123456789: {watchHash1: {persistent: True, last_triggered: 1234567890, expires: 1234567890}, watchHash2: {persistent: False, last_triggered: 1234567890, expires: 1234567890}}}
* Way to prevent persistent alerts triggering too often, such as by making a minimum period between notifications, either static (one day), definable ("persistant 1 day") or dynamic based on the scale of the watch or alert
* The persistent data will be a separate data structure but in the same object, so at the same level as the existing alerts and watches structures.
* No separate commands will be added appart from the delete which is already done, everything else is an addon to existing commands such as creating commands now having a "persistant" qualifier, and list and show commands displaying that info about persistance of each line item.
* The cleanup of expirary should happen once per day, and the user should be notified of the expirary of each persistent alert.
* Command syntax for persistant will just be an additional word on the end of the existing line, I'll leave differing periods to a future update and just consider the default to be 1 daily notification and expirary of one year.
* Warnings and options on expirary will be left to a later version.

## "Bullish" watch

A watch for a bullish period of the market, when the price goes up and stays up for a period y.


## "Bearish

## "Boring" watch

A watch for a "boring" period of the market, otherwise known as crabbing, when the price stays within a narrow range x% for a period y.


## "Bullish" watch

A watch for a bullish period of the market, when the price goes up and stays up for a period y.


## "Bearish" watch

A watch for a bearish period of the market, when the price consistently goes down and stays down for a period y.


## "Bullish" alert

An alert for a bullish period of the market, when the price goes up and stays up for a period y.


## "Bearish" alert

An alert for a bearish period of the market, when the price consistently goes down and stays down for a period y.

## Trailing stop loss alert

An alert that happens when the price falls x% below the recent ATH for a certain period or averaged or smoothed. It is an indication of time to sell.


