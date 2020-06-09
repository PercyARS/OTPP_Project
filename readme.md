
Software 1: Trading Server
This is server software that runs forever until terminated by Ctrl-C
Upon program start, server connects to data source and constructs a series of bitcoin prices sampled at 1-minute intervals, from all available tick data.
The data should be obtained from these two sources, and stitched appropriately. From these two sources, you are able to build consistent 1-minute price series.
< Source 1 >
Bitcoin Chart API: Tick-by-Tick Bitcoin prices from Bitfinex exchange, from 2013-03-13. This data updates once or twice per day.
http://api.bitcoincharts.com/v1/csv/bitfinexUSD.csv.gz
Look at this stackoverflow answer from Lykegenes for more info http://stackoverflow.com/a/21392068
Timestamps are in Unixtime
For each 1-minute time interval, the Bitcoin price indicated should be the last traded price as of that minute. i.e. 2016-07-26 11:37:00 should contain the last observed price as of that time. 

< Source 2 >
Bitcoin Average API: 24-hour sliding window, per minute prices. In this data, not  every minutes have a value. This indicates that there was no trade during that minute, and thus, no price update. This data updates every minute or so.
https://api.bitcoinaverage.com/history/USD/per_minute_24h_sliding_window.csv
Look at the API documentation here
https://bitcoinaverage.com/api
Use API Version 1. 
Assume UTC timestamps

While running, the server queries Bitcoin prices every minute from Source 2 and appends new prices to existing internal data structure.
The server computes a Boolean trading signal series for the entire price time series, and also updates the trading signal and profit & loss calculation the price gets updated live. See Appendix A for trading signal and profit & loss calculation.
Upon the server starts, after constructing the price series and signal series, the server should output a csv file as below. This file is only written to disk once and do not need to be updated every minute.
E.g. (values not indicative of correct result)
datetime, price, signal, pnl
…
2015-04-42-14:42, 421.04, -1, -0.02
2015-04-42-14:43, 421.09, -1, -0.05
…
The server is to be terminated by Ctrl-C. Upon catching Ctrl-C, the server exits with return code of 0.
The server must serve clients over network. Port number is to be configurable.

Software 2: Simple Client
The client is software which queries the Server in multiple ways.
The client supports the following command line arguments
--price YYYY-MM-DD-HH:MM
If specified, queries server for latest price available as of the time specified. The time queried is expected to be in UTC Time.
E.g. (Bitcoin price shown is not correct)
> client --price 2016-07-29-13:34
662.51
> client –-price 1959-05-14-01:00 
Server has no data 
> client --price 2020-05-14-01:00 
Server has no data
> client --price now
(latest bitcoin price)

--signal YYYY-MM-DD-HH:MM
If specified, queries server for latest trading signal available as of the time specified. The time queried is expected to be in UTC Time.
> client --signal 2016-07-28-15:43
(the answer here could be either 1,-1,0)
> client –-signal 1995-05-14-01:00 
Server has no data 
> client –-signal 2020-05-14-01:00 
Server has no data
> client –-signal now
(latest signal value)

--server_address XXX.XXX.XXX.XXX:YYYY
If specified, connect to server running on the IP address, and use specified port number. If this option is not specified, client assumes that the server is running on 127.0.0.1:8000
--reset
If specified, instructs the server to reset Bitcoin data. Server must re-download data and tell client that it was successful.
Client exits with return code: 0=success, 1=failure
If the server is not running, does not respond, or something went wrong with the server, the client must send an email to user. You should store username and password to a plain text configuration file, and blank out the values in configuration file before you submit.
