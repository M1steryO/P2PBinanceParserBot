from requests import post
import json


def filter_tickers(data, max_limit, rate, payment_exceptions):
    result = []
    for i in range(len(data)):
        if (data[i]['limit'] <= max_limit) and (data[i]['rate'] <= rate):
            if len(set(payment_exceptions) & set(data[i]['payment_methods'])) == 0:
                result.append(data[i])
    return result


class Tickers:
    LINK = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    EXCEPTIONS = ['Payeer', 'RUBfiatbalance', 'Advcash', 'BinanceGiftCardRUB']

    def get_request_data(self, page):
        DATA = {
            "asset": "USDT",
            "countries": [],
            "fiat": "RUB",
            "page": page,
            "payTypes": [],
            "proMerchantAds": False,
            "publisherType": None,
            "rows": 20,
            "tradeType": "BUY"
        }
        result = post(self.LINK, json=DATA)
        result = json.loads(result.text)
        return result['data']

    def get_tickers_data(self, page, max_limit, rate):
        all_data = self.get_request_data(page)
        result_data = []
        for i in range(len(all_data)):
            result_data.append(dict())

            result_data[-1]['payment_methods'] = [meth['identifier'] for meth in all_data[i]['adv']['tradeMethods']]
            result_data[-1]['rate'] = float(all_data[i]['adv']['price'])
            result_data[-1]['limit'] = float(all_data[i]['adv']['minSingleTransAmount'])
            result_data[-1]['available_money'] = float(all_data[i]['adv']['surplusAmount'])

        result_data = filter_tickers(result_data, max_limit, rate, Tickers.EXCEPTIONS)
        return result_data
