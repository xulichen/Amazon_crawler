import requests
from lxml import html
import re
from multiprocessing import Pool
from config import *


headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.36 '
}


def get_product_params(start_url):

    html_index = requests.get(start_url, headers=headers)
    parse_index = html.etree.HTML(html_index.text)
    # 各尺寸的asinlist
    asinlist = parse_index.xpath('//span[@class="a-dropdown-container"]/select/option/@value')
    # parent_asin
    # parent_asin = parse_index.xpath('//span[@id="fitRecommendationsSection"]/@data-asin')
    # 页面商品信息
    # apparel_info = parse_index.xpath('//span[@class="a-dropdown-container"]/select/option/text()')
    # 看过后也买了的商品的链接
    # also_bought = parse_index.xpath('//ul[@class="a-unordered-list"]/li/span/div/a/@href')
    immutable_params = re.findall('"immutableParams":(.*?),"mutableParams"', html_index.text)
    immutable_params_dict = eval(immutable_params[0])
    dpenvironment = re.findall('"dpEnvironment" : "(.*?)"', html_index.text)[0]
    # print(dpenvironment)
    # print(immutable_params_dict)
    immutable_params_dict['dpenvironment'] = dpenvironment

    return immutable_params_dict


def get_product_id(start_urls):
    # 轮询4个url，获取不同颜色尺码的亚马逊asin，并找到筛选出有货的颜色尺寸

    apparel_ids = []
    for url in start_urls:
        html_index = requests.get(url, headers=headers)
        parse_index = html.etree.HTML(html_index.text)
        asinlist = parse_index.xpath('//span[@class="a-dropdown-container"]/select/option/@value')
        print('crawlering ', html_index.url)
        for asin in asinlist:
            if ',' in asin:
                apparel_ids.append(asin.split(',')[1])

    return set(apparel_ids)


def get_product_detail(immutable_params, apparel_id):
    # 通过接口获取商品型号及售价
    """
    :type apparel_id: str
    :type immutable_params: dict
    """
    ajax_url = 'https://www.amazon.com/gp/twister/ajaxv2?sid=134-9067795-9709041&ptd={ptd}&sCac=1&twisterView=glance&pgid' \
               '={pgid}&rid={rid}&dStr={dStr}&auiAjax=1&json=1' \
               '&dpxAjaxFlag=1&isUDPFlag=1&ee=2&nodeID={nodeID}&parentAsin={pAsin}&enPre=1&storeID={storeID}&ppw=&ppl' \
               '=&isFlushing=2&dpEnvironment={dpenvironment}&asinList={aid}&id={aid}&mType=full&psc=1 '

    ajax_html = requests.get(url=ajax_url.format(ptd=immutable_params.get('ptd'),
                                                 pgid=immutable_params.get('pgid'),
                                                 rid=immutable_params.get('rid'),
                                                 dStr=immutable_params.get('dStr'),
                                                 nodeID=immutable_params.get('nodeID'),
                                                 storeID=immutable_params.get('storeID'),
                                                 pAsin=immutable_params.get('parentAsin'),
                                                 dpenvironment=immutable_params.get('dpenvironment'),
                                                 aid=apparel_id),
                             headers=headers)
    # print(ajax_html.text)
    category = immutable_params.get('dStr').split('%')

    items = re.findall('<\\\/span><span>(.*?)<\\\/span>', ajax_html.text.strip())[0].split(',')

    for i in range(len(category)):
        category[i] = items[i+1]
    price = re.findall('>(\$.*?)<\\\/span>', ajax_html.text.strip())[0]
    # if 'Neck' and 'Sleeve' not in category:
    #     size = size.split(' ')[1] + '&quot; Neck ' + size.split(' ')[2] + '&quot; Sleeve '
    print(items[0], '-----', category[0], '-----', category[1].replace('&quot;', '"'), '-----', price)


if __name__ == '__main__':
    immutable_para = get_product_params(START_URL)
    ids = get_product_id(START_URLS)
    pool = Pool()
    for id in ids:
        pool.apply_async(get_product_detail, (immutable_para, id))
    pool.close()
    pool.join()

