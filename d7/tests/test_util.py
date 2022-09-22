# -*- coding: utf-8 -*-

import unittest


from d7.steps.util import normalize_where, parse_curl_to_step_config


class UtilTestCase(unittest.TestCase):
    def test_normalize_where(self):
        where_list = [
            ('a = $a and b = $b_b and c = $_c', 'a = %(a)s and b = %(b_b)s and c = %(_c)s'),
            ('a = 1 and b = 1', 'a = 1 and b = 1'),
            ('a = :a and b = 1', 'a = %(a)s and b = 1')
        ]
        for where in where_list:
            self.assertEqual(where[1], normalize_where(where[0]))

    def test_parse_curl_get(self):
        curl_command = '''
curl -X GET 'https://dp-admin.shopee.io/api/tw/order/list?categories=30102&fulfillment_status=F5&refund_status=MR0&order_status=OR5&page_size=10' 
--header 'authority: dp-admin.shopee.io' 
--header 'accept: */*' 
--header 'accept-language: zh-CN,zh;q=0.9' 
--header 'cookie: _ga_7N8T3QXGY7=GS1.1.1651216795.2.0.1651216795.0; G_AUTHUSER_H=0; _ga_QMDMFHB4T7=GS1.1.1657688613.10.0.1657688778.0; _ga_LJKSC5SW1J=GS1.1.1658808055.4.1.1658808098.0; _ga_8SBPY6GX69=GS1.1.1659103383.20.1.1659103454.0; _ga_XWL9LM2WJ1=GS1.1.1659103384.20.1.1659103454.0; _ga_3KMTQ5WCQH=GS1.1.1659103384.10.1.1659103454.0; _gid=GA1.2.1280545695.1659925699; sessionid=6ks3x8ckix369skv8g9h757mehwehg0rwml5xeoi; csrftoken=6650882970; _ga=GA1.1.1478040703.1649243438; _ga_5H3PPWG2TZ=GS1.1.1660656969.121.1.1660658664.0; _ga_N1FF831FCD=GS1.1.1660652656.30.1.1660658994.0; _ga_6VXJESRVZJ=GS1.1.1660702332.40.1.1660702405.0' 
--header 'csrftoken: 6650882970' 
--header 'sec-ch-ua: "Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"' 
--header 'sec-ch-ua-mobile: ?0' 
--header 'sec-ch-ua-platform: "macOS"' 
--header 'sec-fetch-dest: empty' 
--header 'sec-fetch-mode: cors' 
--header 'sec-fetch-site: same-origin' 
--header 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36' 
        '''
        ctx = parse_curl_to_step_config(curl_command)
        print(ctx)
