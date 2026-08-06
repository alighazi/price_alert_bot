

**Este bot admite los siguientes comandos**

**/price** o **/p**  
Obtén el precio de la moneda deseada. La moneda predeterminada es BTC y la moneda base predeterminada es USD si no se proporcionan.  

Ejemplo:  
`/price BTC`  
`/price BTC USD`  
`/price XMR BTC`  
    
**/chart** o **/ch**  
Obtén un gráfico para una moneda en un marco de tiempo. Los valores válidos de intervalo de tiempo son: 1m (1 min), 3m, 5m, 15m, 30m, 1h (1 hora), 2h, 4h, 6h, 8h, 12h, 1d (1 día), 3d, 1w (1 semana), 1M (1 mes). La moneda base predeterminada es USD y el intervalo de tiempo predeterminado es 1h si no se proporcionan.  

Ejemplo:  
`/chart` (predeterminado: BTC USD 1h)  
`/chart BTC`  
`/chart BTC USD`  
`/chart XMR BTC`  
`/chart BTC USD 1w`  
`/chart BTC USD 1M`

**/top**  
Consulta los precios actuales de las principales monedas y su capitalización de mercado.

**/lower**  
Recibe una notificación cuando el precio del símbolo deseado sea MENOR al número especificado. La moneda base predeterminada es USD si no se proporciona.  

Ejemplo:  
`/lower ETH 25` (avísame cuando el precio de ETH sea menor a 25 USD)  
`/lower BTC 1300 USD`  
`/lower XMR 0.01 BTC` (avísame cuando el precio de XMR sea menor a 0.01 BTC)  
`/lower Nano 100 SAT` (avísame cuando el precio de Nano sea menor a 100 Sats)  

**/higher**  
Recibe una notificación cuando el precio del símbolo deseado sea MAYOR al número especificado.

Ejemplo:  
`/higher ETH 25` (avísame cuando el precio de ETH sea mayor a 25 USD)  
`/higher BTC 1300 USD`  
`/higher XMR 0.01 BTC` (avísame cuando el precio de XMR sea mayor a 0.01 BTC)  
`/higher Nano 100 SAT` (avísame cuando el precio de Nano sea mayor a 100 Sats)  

**/alerts**  
Consulta las alertas actuales.

**/clear**  
Limpia las alertas actuales.

**/yesterday**
Precio de ayer para una moneda

**/history**
Precio histórico de una moneda en el pasado. Admite días, semanas, meses y años.

Ejemplo:  
`/history BTC 5 days` (precio de BTC hace 5 días)  
`/history BTC 3 days` (¿cuál era el precio de Bitcoin hace 3 días en USD?)    
`/history BTC 2 weeks`  
`/history BTC 2 months`  

**/yesterday**
Consulta el precio de ayer

Ejemplo:  
`/yesterday eth` (precio de ether ayer)

**/dropby**
Verifica si una moneda ha caído un porcentaje específico

`/dropby BTC 50% 1 month` (¿Ha caído BTC un 50% en el último mes?)


**/watch**
Comando estructurado para verificar si el precio ha subido, caído o se mantiene estable

Ejemplo:  
`/watch btc drop 50% 14 days` (Caída porcentual)  
`/watch btc rise 50% 1 month`  
`/watch btc drop 5000 2 days` (Caída de valor absoluto)  
`/watch btc drop 5000 from ath`  
`/watch btc drop 75% from ath`  

Opcionalmente, los comandos de vigilancia incluyen la palabra clave `persist` para que no se eliminen cuando se disparen,
sino que se repitan. La frecuencia mínima predeterminada es de 1 día, pero se puede configurar para que sea por hora, por semana o por minuto. Estas vigilancias deben eliminarse manualmente usando el comando `/delete` cuando ya no las necesites.

Ejemplo:  
`/watch btc drop 50% 14 days persist`  
`/watch btc drop 5000 from ath persistent daily`
  
Las comparaciones se realizan con respecto al precio actual, a menos que se indique "from ath"   


Ejemplo de configuración estable:  
`/watch btc stable 1% 1 week` Verifica que el precio diario de la última semana haya estado dentro de un 1% +/- del precio actual. Es decir, el precio es estable.

**/showwatches**
Muestra las vigilancias configuradas

**/ath**
¿Cuál es el máximo histórico (ATH) de una moneda? (solo verifica datos desde octubre de 2021)

`/ath BTC`

**/delete**
Elimina alertas o vigilancias.

Ejemplo:  
`/delete` Muestra la lista de alertas y vigilancias con sus IDs de eliminación.  
`/delete 1234` Elimina la alerta o vigilancia con el ID 1234.


**/help**  
Consulta este mensaje.

Para obtener más ayuda o discutir, utiliza el grupo de Telegram https://t.me/alertbotgang

Contribuyentes
 - https://github.com/raymondclowe
