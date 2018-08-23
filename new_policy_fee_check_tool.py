# -*- coding:utf-8 -*-
import urllib2
import json
from time import time, sleep
import hmac, hashlib
import ssl

global cpdax_url
global cpdax_api_prefix

def createTimeStamp(datestr, format="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, format))

class cpdax:
    def __init__(self, APIKey, Secret):
        self.APIKey = APIKey
        self.Secret = Secret

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if ('return' in after):
            if (isinstance(after['return'], list)):
                for x in xrange(0, len(after['return'])):
                    if (isinstance(after['return'][x], dict)):
                        if ('datetime' in after['return'][x] and 'timestamp' not in after['return'][x]):
                            after['return'][x]['timestamp'] = float(createTimeStamp(after['return'][x]['datetime']))

        return after


    def api_query(self, command, req={}, param={}, method="GET"):
        try:
            if (command == "getTicker"):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'tickers'))
                return json.loads(ret.read())
            elif (command == "getTickerCurrency"):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'tickers/' + str(req['currencyPair'])))
                return json.loads(ret.read())
            elif (command == "getTickerCurrencyDetailed"):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'tickers/' + str(req['currencyPair']) + "/detailed"))
                return json.loads(ret.read())
            elif (command == "getTickersDetailed"):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'tickers/detailed'))
                return json.loads(ret.read())
            elif (command == "getProducts"):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'products'))
                return json.loads(ret.read())
            elif (command == "getOrderbook"):
                ret = urllib2.urlopen(urllib2.Request(
                    cpdax_url + 'orderbook/' + str(req['currencyPair']) + "?limit=" + str(param['limit'])))
                return json.loads(ret.read())
            elif (command == "getTrades"):
                parameter = ""
                if param['start'] != "":
                    parameter += "?start=" + param['start']
                if param['end'] != "":
                    if param['start'] != "":
                        parameter += "&end=" + param['end']
                    else:
                        parameter += "?end=" + param['end']
                if param['limit'] != "":
                    if "?" in parameter:
                        parameter += "&limit=" + param['limit']
                    else:
                        parameter += "?limit=" + param['limit']
                # print cpdax_url + 'trades/' + str(req['currencyPair']) + parameter
                ret = urllib2.urlopen(
                    urllib2.Request(cpdax_url + 'trades/' + str(req['currencyPair']) + parameter))

                return json.loads(ret.read())
            else:
                cp_access_timestamp = str(int(time()))
                digest_string = self.APIKey + "" + str(cp_access_timestamp) + "" + method + "" + cpdax_api_prefix + "" + command
                if req != {}:
                    digest_string = digest_string + json.dumps(req).replace(" ", "")
                cp_access_digest = hmac.new(self.Secret, digest_string, hashlib.sha256).hexdigest()

                headers = {
                    'CP-ACCESS-KEY': self.APIKey,
                    'CP-ACCESS-TIMESTAMP': cp_access_timestamp,
                    'CP-ACCESS-DIGEST': cp_access_digest,
                    'Content-Type': 'application/json'
                }

                if "transactions" in command:
                    if param['start'] != "":
                        command += "?start=" + param['start']
                    if param['end'] != "":
                        if param['start'] != "":
                            command += "&end=" + param['end']
                        else:
                            command += "?end=" + param['end']
                    if param['page'] != "":
                        if "?" in command:
                            command += "&page=" + param['page']
                        else:
                            command += "?page=" + param['page']

                    if param['limit'] != "":
                        if "?" in command:
                            command += "&limit=" + param['limit']
                        else:
                            command += "?limit=" + param['limit']

                if method == 'POST':
                    ret = urllib2.urlopen(urllib2.Request(cpdax_url + command, json.dumps(req), headers))
                elif method == 'DELETE':
                    request = urllib2.Request(cpdax_url + command, None, headers)
                    request.get_method = lambda: 'DELETE'
                    ret = urllib2.urlopen(request)
                else:
                    if ("orders" in command) and param != {}:
                        if param['side'] != "":
                            command += "?side=" + param['side']
                        if param['page'] != "":
                            if "?" in command:
                                command += "&page=" + param['page']
                            else:
                                command += "?page=" + param['page']

                        if param['limit'] != "":
                            if "?" in command:
                                command += "&limit=" + param['limit']
                            else:
                                command += "?limit=" + param['limit']
                    ret = urllib2.urlopen(urllib2.Request(cpdax_url + command, None, headers))

                jsonRet = json.loads(ret.read())
                return self.post_process(jsonRet)
        except urllib2.HTTPError, e:
            print("HTTP Error! code : " + str(e.code) + ", message : " + str(json.loads(e.read())['message']))

    def getTicker(self):
        return self.api_query("getTicker")

    def getTickerCurrency(self, currency_pair):
        return self.api_query("getTickerCurrency", {'currencyPair': currency_pair})

    def getTickerCurrencyDetailed(self, currency_pair):
        return self.api_query("getTickerCurrencyDetailed", {'currencyPair': currency_pair})

    def getTickersDetailed(self):
        return self.api_query("getTickersDetailed")

    def getProducts(self):
        return self.api_query("getProducts")

    def getOrderbook(self, currency_pair, limit=15):
        return self.api_query("getOrderbook", {'currencyPair': currency_pair}, {'limit': limit})

    def getTrades(self, currency_pair, start, end, limit):
        return self.api_query("getTrades", {'currencyPair': currency_pair}, {'start': start, 'end': end, 'limit': limit})

    def getBalance(self):
        return self.api_query("balance")

    def getFeeRates(self):
        return self.api_query("fee-rates")

    def getTransactions(self, product_id, start=None, end=None, limit=None, page=None):
        return self.api_query("transactions/"+product_id, {}, {'start': start, 'end': end, 'limit': limit, 'page': page})

    def limitOrder(self, product_id, type, side, price, size):
        return self.api_query("orders", {"type":type,"side":side,"product_id":product_id,"size":size,"price":price},{},"POST")

    def marketOrder(self, product_id, type, side, funds=None, size=None):
        if funds == None:
            return self.api_query("orders",{"type": type, "side": side, "product_id": product_id, "size": size},{}, "POST")
        else:
            return self.api_query("orders", {"type": type, "side": side, "product_id": product_id, "funds": funds}, {},"POST")

    def getOrderList(self, product_id, side, limit, page):
        return self.api_query("orders/"+product_id,{}, {'side': side, 'limit': limit, 'page': page})

    def getOrderStatus(self, product_id, order_id):
        return self.api_query("orders/"+product_id+"/"+order_id)

    def cancelOrder(self, product_id, order_id):
        return self.api_query("orders/"+product_id+"/"+order_id, {}, {}, "DELETE")

    def cancelOrders(self, product_id):
        return self.api_query("orders/"+product_id, {}, {}, "DELETE")

dic = {}

if __name__ == "__main__":
    # cpdax_address = "https://cheetah-test.cpdax.com"   # Cheetah stage=> Changed
    cpdax_address = "https://a4b9d8f51de2.coingift.co.kr"   # Cheetah stage
    # cpdax_address = "https://sd5762e9d.cpdax.com"   # stage
    # cpdax_address = "https://api.cpdax.com"   # prod
    # cpdax_address = "https://www.coingift.co.kr"  # coingift
    # cpdax_address = "https://d2e0059e6.cpdax.com"  # dev
    cpdax_api_prefix = "/v1/"
    cpdax_url = cpdax_address + "" + cpdax_api_prefix

    # Stage rsi+9@coinplug.com
    # Stage rsi@coinplug.com
    api_key = "9574a4a2c9748c4749348eb8bab2f6edba6a74cfc1cd36cbd891a50c7c1d6e7d"    #rsi+11@coinplug.com
    secret_key = "ZjI2NDg3ZjAtZTg1Yi00MDJlLThmMTYtNzViODAzNzM0ZGY0" #rsi+11@coinplug.com

    # Stage rsi+9@coinplug.com
    #api_key = "65962eacceff0ccfc9a54c3f792b6a51fec8300eb0a7fb324412043d036b238b"
    #secret_key = "YzdkNTk0YzItZTU5Ny00NjBiLTgyNjYtMWFiNDJlZDAzODIw"
    cpdax_obj = cpdax(api_key, secret_key)

    ## order test user on "cheetah-stag.cpdax.com"
    # user 1 - level : ?, order ratio : ? (rsi+11@coinplug.com)
    user1_api_key = "9574a4a2c9748c4749348eb8bab2f6edba6a74cfc1cd36cbd891a50c7c1d6e7d"
    user1_secret_key = "ZjI2NDg3ZjAtZTg1Yi00MDJlLThmMTYtNzViODAzNzM0ZGY0"
    user1_cpdax = cpdax(user1_api_key, user1_secret_key)

    # user 2 - level : ?, order ratio : ? (rsi+12@coinplug.com)
    user2_api_key = "bfe99576d4b8eb54f472e5385df44233981548ec1698bf0f4f808edf58437949"
    user2_secret_key = "Mzk4MTU0N2EtYTQwMy00MTkyLTlkMTMtMTNhOGI2ODI5ZGEz"
    user2_cpdax = cpdax(user2_api_key, user2_secret_key)

    # user 3 - level : ?, order ratio : ? (rsi+13@coinplug.com)
    user3_api_key = "5a3ec80cb7a5a3c7c12885b9decc14c317ef650b675fa6b91d099f550a40b2f0"
    user3_secret_key = "YjlmMWJkNjUtYjNkNy00YWZlLTg3ZjYtZWFjZjY1MWZhMTVl"
    user3_cpdax = cpdax(user3_api_key, user3_secret_key)

    # user 4 - level : ?, order ratio : ? (rsi+14@coinplug.com)
    user4_api_key = "4c49b57ed56821bb368c68db8620bea1646a1b00120f9fc557dfd8480b469d27"
    user4_secret_key = "NTk0ZDdmODktODZjYy00OThmLWI2ZTItMWYyZDk2Y2M3N2Qx"
    user4_cpdax = cpdax(user4_api_key, user4_secret_key)

    # ## order test user on "cheetah-stag.cpdax.com"
    # # user 1 - level : ?, order ratio : ? (rsi+1@coinplug.com)
    # user1_api_key = "29fba522c8678aac08f3428161001367f43edc76626a8721159297d98fda1f0c"
    # user1_secret_key = "MWU5ZmFkYmEtNmYxNC00YzI1LTlkOWEtNzZjMjg3Y2M1ZDNi"
    # user1_cpdax = cpdax(user1_api_key, user1_secret_key)
    #
    # # user 2 - level : ?, order ratio : ? (rsi+2@coinplug.com)
    # user2_api_key = "80716d1aba4e262a31cdfd8e3655a33796e41aad9eed6819fb61eb407670a758"
    # user2_secret_key = "NDAzOTNkOTUtYzViYi00YTFjLTk0NTEtZWNlNDBkZGE2YWI2"
    # user2_cpdax = cpdax(user2_api_key, user2_secret_key)
    #
    # # user 3 - level : ?, order ratio : ? (rsi+3@coinplug.com)
    # user3_api_key = "a49a24b7c1de0b6fc0bc40deaf9bc65d6dcefc079bfa7b92ac9e97f7a1a6e6a2"
    # user3_secret_key = "NjdjZThlNDQtYjgyYS00NWNiLWI0MDUtZDZkNjAyMzM4NmFh"
    # user3_cpdax = cpdax(user3_api_key, user3_secret_key)
    #
    # # user 4 - level : ?, order ratio : ? (rsi+4@coinplug.com)
    # user4_api_key = "96b880ef0960d6c56aa6d95432c871efa88781928d2e7a26f0191cfef85ef8a7"
    # user4_secret_key = "MjIyYjRmMjMtZmE0Ni00Y2FkLTlmNWItOWIyZjBkN2JkZDNm"
    # user4_cpdax = cpdax(user4_api_key, user4_secret_key)

    while 1:
        print "===== CPDAX Open API Test ====="
        print "# Public API"
        print "1. ticker"
        print "2. ticker(Currency Pair)"
        print "3. ticker(Currency Pair Detailed)"
        print "4. Show Products"
        print "5. Show Orderbook"
        print "6. Show Recent Trade"
        print "# Private API"
        print "7. My balance"
        print "8. My Info"
        print "9. Limit Order"
        print "10. Market Order"
        print "11. My Order List"
        print "12. Cancel Order"
        print "13. Cancel Orders"
        print "14. My Trade Transactions"
        print "==============================="
        print "15. RateLimit Test"
        print "16. tickers Detailed"
        print "17. order information"
        print "a. Auto Trading from the files"
        print "q. exit"
        operation = raw_input("Choose operation number : ")
        if operation == "1":
            ticker = cpdax_obj.getTicker()
            print(json.dumps(ticker, indent=2))
        elif operation == "2":
            product_id = raw_input("Input productId : ")
            ticker_currency = cpdax_obj.getTickerCurrency(product_id)
            print(json.dumps(ticker_currency, indent=2))
        elif operation == "3":
            product_id = raw_input("Input productId : ")
            ticker_currency_detailed = cpdax_obj.getTickerCurrencyDetailed(product_id)
            print(json.dumps(ticker_currency_detailed, indent=2))
        elif operation == "4":
            products = cpdax_obj.getProducts()
            print(json.dumps(products, indent=2))
        elif operation == "5":
            product_id = raw_input("Input productId : ")
            orderbook = cpdax_obj.getOrderbook(product_id, 15)
            print(json.dumps(orderbook, indent=2))
        elif operation == "6":
            product_id = raw_input("Input productId : ")
            start = raw_input("start time(optional) : ")
            end = raw_input("end time(optional) : ")
            limit = ""
            if start == "" and end == "":
                limit = raw_input("limit(optional) : ")
            trades = cpdax_obj.getTrades(product_id, start, end, limit)
            print(json.dumps(trades, indent=2))
        elif operation == "7":
            balances = cpdax_obj.getBalance()
            print(json.dumps(balances, indent=2))
        elif operation == "8":
            fee_rates = cpdax_obj.getFeeRates()
            print(json.dumps(fee_rates, indent=2))
        elif operation == "9":
            product_id = raw_input("Input productId : ")
            side = raw_input("side(buy/sell) : ")
            price = raw_input("price : ")
            size = raw_input("size : ")
            order = cpdax_obj.limitOrder(product_id, "limit", side, price, size)
            print(json.dumps(order, indent=2))
        elif operation == "10":
            product_id = raw_input("Input productId : ")
            side = raw_input("side(buy/sell) : ")
            if side == "buy":
                funds = raw_input("funds : ")
                order = cpdax_obj.marketOrder(product_id, "market", side, funds, None)
            else:
                size = raw_input("size : ")
                order = cpdax_obj.marketOrder(product_id, "market", side, None, size)
            print(json.dumps(order, indent=2))
        elif operation == "11":
            product_id = raw_input("Input productId : ")
            side = raw_input("side(buy/sell)(optional) : ")
            limit = raw_input("limit(optional) : ")
            page = raw_input("page(optional) : ")
            order_list = cpdax_obj.getOrderList(product_id, side, limit, page)
            print(json.dumps(order_list, indent=2))
        elif operation == "12":
            product_id = raw_input("Input productId : ")
            order_id = raw_input("Input orderId : ")
            canceled_order = cpdax_obj.cancelOrder(product_id, order_id)
            print(json.dumps(canceled_order, indent=2))
        elif operation == "13":
            product_id = raw_input("Input productId : ")
            canceled_orders = cpdax_obj.cancelOrders(product_id)
            print(json.dumps(canceled_orders, indent=2))
        elif operation == "14":
            product_id = raw_input("Input productId : ")
            start = raw_input("start time(optional) : ")
            end = raw_input("end time(optional) : ")
            limit = raw_input("limit(optional) : ")
            page = raw_input("page(optional) : ")
            transactions = cpdax_obj.getTransactions(product_id, start, end, limit, page)
            print(json.dumps(transactions, indent=2))
        elif operation == "15":
            for x in range(0, 5):
                ret = urllib2.urlopen(urllib2.Request(cpdax_url + 'tickers'))
                print(json.dumps(json.loads(ret.read()), indent=2))
                cpdax_obj.getTickerThread()
        elif operation == "16":
            tickers = cpdax_obj.getTickersDetailed()
            print(json.dumps(tickers, indent=2))
        elif operation == "17":
            product_id = raw_input("Input productId : ")
            order_id = raw_input("Input orderId : ")
            order = cpdax_obj.getOrderStatus(product_id, order_id)
            print(json.dumps(order, indent=2))

        elif operation == "a":

            # ## KRW마켓에 각 Coin별 기준가격 설정
            TCAPI_MEDX_KRW_01A = user4_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.34", "100000")
            TCAPI_MEDX_KRW_01B = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.34", "151200")
            TCAPI_MEDX_KRW_02A = user4_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.21", "312300")
            TCAPI_MEDX_KRW_02B = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.34", "261100")
            TCAPI_MEDX_KRW_02A = user3_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.29", "823000")
            TCAPI_MEDX_KRW_02B = user2_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.82", "823000")
            TCAPI_MEDX_KRW_03A = user2_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.18", "1313000")
            TCAPI_MEDX_KRW_03B = user3_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.18", "1313000")
            TCAPI_MEDX_KRW_04A = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "4.92", "4521000")
            TCAPI_MEDX_KRW_04B = user4_cpdax.limitOrder("MT-KRW", "limit", "buy", "4.97", "4521000")
            TCAPI_MEDX_KRW_05C = user3_cpdax.limitOrder("MT-KRW", "limit", "sell", "4.97", "3345000")
            TCAPI_MEDX_KRW_05D = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.07", "3345000")
            TCAPI_MEDX_KRW_06A = user4_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.12", "3023000")
            TCAPI_MEDX_KRW_06B = user2_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.22", "3023000")
            TCAPI_MEDX_KRW_07A = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.27", "4009000")
            TCAPI_MEDX_KRW_07B = user3_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.48", "4009000")
            TCAPI_MEDX_KRW_08A = user4_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.32", "4212300")
            TCAPI_MEDX_KRW_08B = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.37", "10000")
            TCAPI_MEDX_KRW_08C = user3_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.43", "1300")
            TCAPI_MEDX_KRW_08D = user2_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.43", "4201000")
            TCAPI_MEDX_KRW_09A = user4_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.37", "123000")
            TCAPI_MEDX_KRW_09B = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.27", "323500")
            TCAPI_MEDX_KRW_10A = user4_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.48", "524000")
            TCAPI_MEDX_KRW_10B = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.21", "323500")
            TCAPI_MEDX_KRW_11A = user3_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.21", "135000")
            TCAPI_MEDX_KRW_11B = user2_cpdax.limitOrder("MT-KRW", "limit", "sell", "4.90", "135000")
            TCAPI_MEDX_KRW_12A = user2_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.00", "905000")
            TCAPI_MEDX_KRW_12B = user3_cpdax.limitOrder("MT-KRW", "limit", "sell", "4.80", "905000")
            TCAPI_MEDX_KRW_13A = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.60", "4109000")
            TCAPI_MEDX_KRW_13B = user4_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.38", "4109000")
            TCAPI_MEDX_KRW_14A = user3_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.66", "3159000")
            TCAPI_MEDX_KRW_14B = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.65", "3159000")
            TCAPI_MEDX_KRW_15A = user4_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.55", "1723900")
            TCAPI_MEDX_KRW_15B = user2_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.38", "1723900")
            TCAPI_MEDX_KRW_16A = user1_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.22", "1724000")
            TCAPI_MEDX_KRW_16B = user3_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.06", "1724000")
            TCAPI_MEDX_KRW_17A = user4_cpdax.limitOrder("MT-KRW", "limit", "buy", "5.48", "5989000")
            TCAPI_MEDX_KRW_17B = user1_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.43", "109000")
            TCAPI_MEDX_KRW_17C = user3_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.21", "113000")
            TCAPI_MEDX_KRW_17D = user2_cpdax.limitOrder("MT-KRW", "limit", "sell", "5.10", "5767000")
            sleep(2)

            ## 파일을 읽어서 실행하는 방법 (sleep() 추가와 파일이름을 변수로 읽어오도록 변경필요)
            # def efile():
            #     f = open("Trade_EthKrw.txt", 'r')
            #     while True:
            #         line = f.readline()
            #         if not line: break
            #         print line
            #         _user,_productId,_type,_side,_price,_size = line.split(",")
            #         if _user == '1':
            #             user1_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '2':
            #             user2_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '3':
            #             user3_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '4':
            #             user4_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '5':
            #             user5_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '6':
            #             user6_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '7':
            #             user7_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #         elif _user == '8':
            #             user8_cpdax.limitOrder (str(_productId),str(_type),str(_side),str(_price),str(_size)[:1])
            #     f.close()
            #     sleep(1)
            # efile()


            #실행결과를 파일로 저장
            import datetime
            now = datetime.datetime.now()
            nowTuple = now.timetuple()

            filenm = str(nowTuple.tm_year) + str(nowTuple.tm_mon) + str(nowTuple.tm_mday) + "-" + str(nowTuple.tm_hour) + str(nowTuple.tm_min)
            f = open('/Users/rsi/cpdax/api/api_rslt/' + filenm + '_result.txt', 'w')
            f.write("== user1 balance ==" + "\n" + json.dumps(user1_cpdax.getBalance(), indent=2))
            f.write("== user2 balance ==" + "\n" + json.dumps(user2_cpdax.getBalance(), indent=2))
            f.write("== user3 balance ==" + "\n" + json.dumps(user3_cpdax.getBalance(), indent=2))
            f.write("== user4 balance ==" + "\n" + json.dumps(user4_cpdax.getBalance(), indent=2))
            f.close()

        elif operation == "q":
            exit()

        else:
            print "Wrong choose!!"

    print "----- 프로그램 종료 -----"
