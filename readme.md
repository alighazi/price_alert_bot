**This bot supports following commands**

**/price** or **/p**  
Get the price for desired coin. The coin defaults to BTC and the base currency defaults to USD if not provided.  

Example:  
`/price BTC`  
`/price BTC USD`  
`/price XMR BTC`  
    
**/chart** or **/ch**  
Get chart for a coin at a timeframe. valid time frame values are: 1m (1 min), 3m, 5m, 15m, 30m, 1h (1 hour), 2h, 4h, 6h, 8h, 12h, 1d (1 day), 3d, 1w (1 week), 1M (1 month). The base currency defaults to USD and the time frame defaults to 1h if not provided.  

Example:  
`/chart` (defaults to BTC USD 1h)  
`/chart BTC`  
`/chart BTC USD`  
`/chart XMR BTC`  
`/chart BTC USD 1w`  
`/chart BTC USD 1M`

**/top**  
See the current prices of the top coins and market cap.

**/lower**  
Get notified when price of desired symbol goes LOWER than specified number. The base currency defaults to USD if not provided.  

Example:  
`/lower ETH 25` (notify me when ETH price goes lower than 25 USD)  
`/lower BTC 1300 USD`  
`/lower XMR 0.01 BTC` (notify me when XMR price goes lower than 0.01 BTC)  
`/lower Nano 100 SAT` (notify me when Nano price goes lower than 100 Sats)  

**/higher**  
Get notified when price of desired symbol goes HIGHER than specified number.

Example:  
`/higher ETH 25` (notify me when ETH price goes higher than 25 USD)  
`/higher BTC 1300 USD`  
`/higher XMR 0.01 BTC` (notify me when XMR price goes higher than 0.01 BTC)  
`/higher Nano 100 SAT` (notify me when Nano price goes higher than 100 Sats)  

**/alerts**  
Get the current alerts.

**/clear**  
Clear current alerts.

**/yesterday**
Price yesterday for a coin

**/history**
Historical price of a coin in the past. Supports days, weeks, months, years.

Example:  
`/history BTC 5 days` ( BTC price 5 days ago)  
`/history BTC 3 days` (what was the price of Bitcoin 3 days ago in USD)    
`/history BTC 2 weeks`  
`/history BTC 2 months`  

**/yesterday**
Check yesterday's price

Example:  
`/yesterday eth` (price of ether yesterday)

**/dropby**
Check if a coin has dropped by a percentage

`/dropby BTC 50% 1 month` (Has BTC dropped by 50% in the last 1 month)


**/watch**
Command structured for checking if the price has risen, dropped or is stable

Example:  
`/watch btc drop 50% 14 days` (Percentage drop)  
`/watch btc rise 50% 1 month`  
`/watch btc drop 5000 2 days` (absolute value drop)  
`/watch btc drop 5000 from ath`  
`/watch btc drop 75% from ath`  

Optionally watch commands have have a `persist` keywords so they don't get deleted when they fire
but will repeat. Minimum frequency is default 1 day but can be set to hourly, weekly or by the minute. Such watches have to be manually deleted using the `/delete` command when you don't want them any more.

Example:  
`/watch btc drop 50% 14 days persist`  
`/watch btc drop 5000 from ath persistent daily`
  
Comparisons are vs current price unless "from ath" is set   

Example of stable:  
`/watch btc stable 1% 1 week` Checks that the daily price for the last week have all been within 1% +/-  of the current price. e.g. the price is stable.

**/showwatches**
Show the watches

**/ath**
What is the ATH of a coin (only checks back to Oct 2021)

`/ath BTC`

**/delete**
Delete alerts or watches.

Example:  
`/delete` Show list of alerts and watches with delete IDs.  
`/delete 1234` Delete alert or watch with ID 1234.


**/help**  
See this message.

for further help or discussion please use the telegram group https://t.me/alertbotgang

Contributors
 - https://github.com/raymondclowe
