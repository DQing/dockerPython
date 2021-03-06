import scrapy


class ZhihuSpider(scrapy.Spider):
    name = "zhihu"
    start_urls = ['https://zhihu.com']
    allowed_domains = ['www.zhihu.com']

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.zhihu.com",
        "Upgrade-Insecure-Requests": "1",
    }

    cookie = {
        '_xsrf': '7b1850fb-ae0d-4ea5-8ae0-f2a8bc687940',
        '_zap': '1590e72a-e7be-494c-a8e7-2dd1f06dcf18',
        'aliyungf_tc': 'AQAAAHGhlQ5g9QYAkp1K0hC3+c1QLSQ2',
        'capsion_ticket': '"2|1:0|10:1515576838|14:capsion_ticket|44:ZDQ0YWE0ZGY0ZDllNGM4NzliNDE1OWY0MzdmNjQxZGU=|7e5c8c906950819c6b0c98827e139561382f4066d783769183cde0582fe1dd61"',
        'd_c0': '"AHBjdFHi9wyPTiNx9tGxnQNrFaZclwThJqM=|1515573647"',
        'q_c1': 'dc90fc34cb9a47888d9fc06a51a6e0c4|1515573647000|1515573647000',
        'z_c0': '"2|1:0|10:1515576840|4:z_c0|92:Mi4xN2pILUFnQUFBQUFBY0dOMFVlTDNEQ1lBQUFCZ0FsVk5DQ3hEV3dDX2NvSk1oYzg4ZXR1eDFtanBwRHl1RjIxSnd3|204224d910c36a9fd9498fb3e9847a591ba761cc945984ebf03cef88acec8e0a"'}

    #验证码定位
    capacha_index = [
        [12.79688, 32],
        [51.7969, 34],
        [64.7969, 26],
        [91.7969, 29],
        [107.7969, 26],
        [136.797, 33],
        [155.797, 31]
    ]


    # 翻页请求问题相关
    next_page = 'https://www.zhihu.com/api/v3/feed/topstory?action_feed=True&limit=10&' \
                'session_token={0}&action=down&after_id={1}&desktop=true'
    session_token = ''


    # 点击查看更多答案触发的url
    more_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.i' \
                      's_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_actio' \
                      'n%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_ed' \
                      'it%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2' \
                      'Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Crevie' \
                      'w_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2' \
                      'Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.ur' \
                      'l%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.t' \
                      'opics&offset={1}&limit={2}&sort_by=default'


    def start_requests(self):

        yield scrapy.Request('https://www.zhihu.com/', callback=self.login_zhihu)

    def login_zhihu(self, response):
        """ 获取xsrf及验证码图片 """
        xsrf = re.findall(r'name="_xsrf" value="(.*?)"/>', response.text)[0]
        self.headers['X-Xsrftoken'] = xsrf
        self.post_data['_xsrf'] = xsrf

        times = re.findall(r'<script type="text/json" class="json-inline" data-n'
                           r'ame="ga_vars">{"user_created":0,"now":(\d+),', response.text)[0]
        captcha_url = 'https://www.zhihu.com/' + 'captcha.gif?r=' + times + '&type=login&lang=cn'

        yield scrapy.Request(captcha_url, headers=self.headers, meta={'post_data': self.post_data},
                             callback=self.veri_captcha)


    def veri_captcha(self, response):
        """ 输入验证码信息进行登录 """
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)

        print('只有一个倒立文字则第二个位置为0')
        loca1 = input('input the loca 1:')
        loca2 = input('input the loca 2:')
        captcha = self.location(int(loca1), int(loca2))

        self.post_data = response.meta.get('post_data', {})
        self.post_data['captcha'] = captcha
        post_url = 'https://www.zhihu.com/login/email'

        yield scrapy.FormRequest(post_url, formdata=self.post_data, headers=self.headers,
                                 callback=self.login_success)

    def location(self, a, b):
        """ 将输入的位置转换为相应信息 """
        if b != 0:
            captcha = "{\"img_size\":[200,44],\"input_points\":[%s,%s]}" % (str(self.capacha_index[a - 1]),
                                                                            str(self.capacha_index[b - 1]))
        else:
            captcha = "{\"img_size\":[200,44],\"input_points\":[%s]}" % str(self.capacha_index[a - 1])
        return captcha

    def login_success(self, response):

        if 'err' in response.text:
            print(response.text)
            print("error!!!!!!")
        else:
            print("successful!!!!!!")
            yield scrapy.Request('https://www.zhihu.com', headers=self.headers, dont_filter=True)

    def parse(self, response):
        """ 获取首页问题 """
        question_urls = re.findall(r'https://www.zhihu.com/question/(\d+)', response.text)

        # 翻页用到的session_token 和 authorization都可在首页源代码找到
        self.session_token = re.findall(r'session_token=([0-9,a-z]{32})', response.text)[0]
        auto = re.findall(r'carCompose&quot;:&quot;(.*?)&quot', response.text)[0]
        self.headers['authorization'] = 'Bearer ' + auto

        # 首页第一页问题
        for url in question_urls:
            question_detail = 'https://www.zhihu.com/question/' + url
            yield scrapy.Request(question_detail, headers=self.headers, callback=self.parse_question)

        # 获取指定数量问题
        n = 10
        while n < self.question_count:
            yield scrapy.Request(self.next_page.format(self.session_token, n), headers=self.headers,
                                 callback=self.get_more_question)
            n += 10

    def parse_question(self, response):
        """ 解析问题详情及获取指定范围答案 """
        text = response.text
        item = ZhihuQuestionItem()

        item['question_id'] = re.match(r'https://www.zhihu.com/question/(\d+)', response.url).group(1)
        item['name'] = re.findall(r'<meta itemprop="name" content="(.*?)"', text)[0]
        item['url'] = re.findall(r'<meta itemprop="url" content="(.*?)"', text)[0]
        item['keywords'] = re.findall(r'<meta itemprop="keywords" content="(.*?)"', text)[0]
        item['answer_count'] = re.findall(r'<meta itemprop="answerCount" content="(.*?)"', text)[0]
        item['comment_count'] = re.findall(r'<meta itemprop="commentCount" content="(.*?)"', text)[0]
        item['flower_count'] = re.findall(r'<meta itemprop="zhihu:followerCount" content="(.*?)"', text)[0]
        item['date_created'] = re.findall(r'<meta itemprop="dateCreated" content="(.*?)"', text)[0]

        count_answer = int(item['answer_count'])
        yield item

        question_id = int(re.match(r'https://www.zhihu.com/question/(\d+)', response.url).group(1))

        # 从指定位置开始获取指定数量答案
        if count_answer > self.answer_count:
            count_answer = self.answer_count
        n = self.answer_offset
        while n <= count_answer:
            yield scrapy.Request(self.more_answer_url.format(question_id, n, n + 20), headers=self.headers,
                                 callback=self.parse_answer)
            n += 20

    def get_more_question(self, response):
        """ 获取更多首页问题 """
        question_url = 'https://www.zhihu.com/question/{0}'
        questions = json.loads(response.text)

        for que in questions['data']:
            question_id = re.findall(r'(\d+)', que['target']['question']['url'])[0]
            yield scrapy.Request(question_url.format(question_id), headers=self.headers,
                                 callback=self.parse_question)

    def parse_answer(self, response):
        """ 解析获取到的指定范围答案 """
        answers = json.loads(response.text)

        for ans in answers['data']:
            item = ZhihuAnswerItem()
            item['question_id'] = re.match(r'http://www.zhihu.com/api/v4/questions/(\d+)',
                                           ans['question']['url']).group(1)
            item['author'] = ans['author']['name']
            item['ans_url'] = ans['url']
            item['comment_count'] = ans['comment_count']
            item['upvote_count'] = ans['voteup_count']
            item['excerpt'] = ans['excerpt']

            yield item
