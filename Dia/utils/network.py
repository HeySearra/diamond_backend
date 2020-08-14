import random
import smtplib
from datetime import datetime, timedelta
from email.header import Header
from email.mime.text import MIMEText
from string import digits

import requests
from bs4 import BeautifulSoup
from django.template.defaultfilters import striptags

from meta_config import HELL_WORDS


def req():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}
    url = r'https://www.lz13.cn/lizhimingyan/5942.html'
    html = requests.get(url=url, headers=headers, timeout=20)
    html.encoding = html.apparent_encoding
    soup = BeautifulSoup(html.text, "html.parser")
    ps = soup.find('div', attrs={'class': 'PostContent'})
    ps = [striptags(p).strip() for p in ps.find_all('p')]
    print(r'TEXT = """')
    for p in ps:
        if p[0].isdigit():
            print(p.strip(digits).strip('、') + r"\n")
    print(r'"""')


TEXT = """
用爱心来做事，用感恩的心做人。
人永远在追求快乐，永远在逃避痛苦。
有多大的思想，才有多大的能量。
人的能量=思想+行动速度的平方。
励志是给人快乐，激励是给人痛苦。
成功者绝不给自己软弱的借口。
你只有一定要，才一定会得到。
决心是成功的开始。
当你没有借口的那一刻，就是你成功的开始。
命运是可以改变的。
成功者绝不放弃。
成功永远属于马上行动的人。
下定决心一定要，才是成功的关键。
成功等于目标，其他都是这句话的注解。
成功是一个过程，并不是一个结果。
成功者学习别人的经验，一般人学习自己的经验。
只有第一名可以教你如何成为第一名。
学习需要有计划。
完全照成功者的方法来执行。
九十九次的理论不如一次的行动来得实际。
一个胜利者不会放弃，而一个放弃者永远不会胜利。
信心、毅力、勇气三者具备，则天下没有做不成的事。
如果你想得到，你就会得到，你所需要付出的只是行动。
一个缺口的杯子，如果换一个角度看它，它仍然是圆的。
对于每一个不利条件，都会存在与之相对应的有利条件。
一个人的快乐，不是因为他拥有的多，而是他计较的少。
世间成事，不求其绝对圆满，留一份不足，可得无限美好。
记住：你是你生命的船长；走自己的路，何必在乎其它。
你要做多大的事情，就该承受多大的压力。
如果你相信自己，你可以做任何事。
天空黑暗到一定程度，星辰就会熠熠生辉。
时间顺流而下，生活逆水行舟。
生活充满了选择，而生活的态度就是一切。
人各有志，自己的路自己走。
别人的话只能作为一种参考，是不能左右自己的。
成功来自使我们成功的信念。
相互了解是朋友，相互理解是知己。
没有所谓失败，除非你不再尝试。
有时可能别人不在乎你，但你不能不在乎自己。
你必须成功，因为你不能失败。
羡慕别人得到的，不如珍惜自己拥有的。
喜欢一个人，就该让他（她）快乐。
别把生活当作游戏，谁游戏人生，生活就惩罚谁，这不是劝诫，而是--规则！
你要求的次数愈多，你就越容易得到你要的东西，而且连带地也会得到更多乐趣。
把气愤的心境转化为柔和，把柔和的心境转化为爱，如此，这个世间将更加完美。
一份耕耘，一份收获，付出就有回报永不遭遇过失败，因我所碰到的都是暂时的挫折。
心如镜，虽外景不断变化，镜面却不会转动，这就是一颗平常心，能够景转而心不转。
每件事情都必须有一个期限，否则，大多数人都会有多少时间就花掉多少时间。
人，其实不需要太多的东西，只要健康地活着，真诚地爱着，也不失为一种富有。
生命之长短殊不重要，只要你活得快乐，在有生之年做些有意义的事，便已足够。
活在忙与闲的两种境界里，才能俯仰自得，享受生活的乐趣，成就人生的意义。
一个从来没有失败过的人，必然是一个从未尝试过什么的人。
待人退一步，爱人宽一寸，人生自然活得很快乐。
经验不是发生在一个人身上的事件，而是一个人如何看待发生在他身上的事。
加倍努力，证明你想要的不是空中楼阁。胜利是在多次失败之后才姗姗而来。
只要能执着远大的理想，且有不达目的绝不终止的意愿，便能产生惊人的力量。
一个人，只要知道付出爱与关心，她内心自然会被爱与关心充满。
如果我们可以改变情绪，我们就可以改变未来。
明白事理的人使自己适应世界，不明事理的人硬想使世界适应自己。
当困苦姗姗而来之时，超越它们会更有余味。
"""


def rand_sent() -> str:
    return random.choice(TEXT.splitlines())


def send_code(acc, email_type, storage=True):
    # 发信方的信息：发信邮箱，QQ 邮箱授权码
    from_addr = 'diadoc@163.com'
    password = 'UTXGEJFQTCJNDAHQ'

    # 收信方邮箱
    to_addr = acc

    # 发信服务器
    smtp_server = 'smtp.163.com'

    # 生成随机验证码
    code_list = []
    for i in range(10):  # 0~9
        code_list.append(str(i))
    key_list = []
    for i in range(65, 91):  # A-Z
        key_list.append(chr(i))
    for i in range(97, 123):  # a-z
        key_list.append(chr(i))

    content = r"""
    您好：
    <br>
    <br>
    
    您的%s为：<b> %s </b> (有效期五分钟)
    
    <br>
    
    <br>
    
    <br>
    
    <br>
    
    <br>
    
    <br>
    
    <br>
    %s
    <br>
    
    <br>
    <i>%s --  DiaDoc </i>
    <br>
    
    <br>
    
    <br>
    """
    sent = rand_sent()
    print(f'[sent] = {sent}')

    if email_type == 'register':
        code = random.sample(code_list, 6)  # 随机取6位数
        code_num = ''.join(code)
        # 数据库保存验证码！！！！！！！！！！！
        storage_code = code_num
        # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
        msg = MIMEText(content % ('验证码', code_num, "-" * 3 * len(sent), sent), 'html', 'utf-8')
        msg['Subject'] = Header('DiaDoc 注册验证码' + random.choice(HELL_WORDS))
    else:
        code = random.sample(key_list, 10)
        code_num = ''.join(code)

        storage_code = '/forget/set?acc=' + acc + '&key=' + code_num
        msg = MIMEText(content % ('找回密码的链接', storage_code, "-" * 3 * len(sent), sent), 'html', 'utf-8')
        msg['Subject'] = Header('DiaDoc 找回密码' + random.choice(HELL_WORDS))

    # 邮件头信息
    msg['From'] = Header(from_addr)
    msg['To'] = Header(to_addr)

    # 开启发信服务，这里使用的是加密传输
    server = smtplib.SMTP_SSL(host='smtp.163.com')
    server.connect(smtp_server, 465)
    # 登录发信邮箱
    server.login(from_addr, password)
    # 发送邮件
    server.sendmail(from_addr, to_addr, msg.as_string())
    # 关闭服务器
    server.quit()

    if storage:
        from user.models import EmailRecord
        ver_code = EmailRecord()
        ver_code.code = storage_code
        ver_code.acc = acc
        ver_code.send_time = datetime.now()
        ver_code.expire_time = datetime.now() + timedelta(minutes=60)
        ver_code.email_type = email_type
        try:
            ver_code.save()
        except:
            return False
    return True


if __name__ == '__main__':
    # req()
    send_code('1016194674@qq.com', 'register', storage=False)

    # print(rand_sent())
    # print(rand_sent())
    # print(rand_sent())
