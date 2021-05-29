#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   XueWeiHan
#   E-mail  :   595666367@qq.com
#   Date    :   2020-05-19 15:27
#   Desc    :   获取最新的 GitHub 相关域名对应 IP
import os
import re
import json
import traceback

from datetime import datetime, timezone, timedelta
from collections import Counter

from retry import retry

import requests

RAW_URL = [
    "alive.github.com", "live.github.com", "github.githubassets.com",
    "central.github.com", "desktop.githubusercontent.com",
    "assets-cdn.github.com", "camo.githubusercontent.com",
    "github.map.fastly.net", "github.global.ssl.fastly.net", "gist.github.com",
    "github.io", "github.com", "api.github.com", "raw.githubusercontent.com",
    "user-images.githubusercontent.com", "favicons.githubusercontent.com",
    "avatars5.githubusercontent.com", "avatars4.githubusercontent.com",
    "avatars3.githubusercontent.com", "avatars2.githubusercontent.com",
    "avatars1.githubusercontent.com", "avatars0.githubusercontent.com",
    "avatars.githubusercontent.com", "codeload.github.com",
    "github-cloud.s3.amazonaws.com", "github-com.s3.amazonaws.com",
    "github-production-release-asset-2e65be.s3.amazonaws.com",
    "github-production-user-asset-6210df.s3.amazonaws.com",
    "github-production-repository-file-5c1aeb.s3.amazonaws.com",
    "githubstatus.com", "github.community", "media.githubusercontent.com"
]

IPADDRESS_PREFIX = ".ipaddress.com"

HOSTS_TEMPLATE = """# GitHub520 Host Start
{content}

# Update time: {update_time}
# Star me GitHub url: https://github.com/521xueweihan/GitHub520
# GitHub520 Host End\n"""


def write_file(hosts_content: str, update_time: str):
    output_doc_file_path = os.path.join(os.path.dirname(__file__), "README.md")
    template_path = os.path.join(os.path.dirname(__file__),
                                 "README_template.md")
    # 应该取消 write yaml file，改成 gitee gist 地址同步（国内访问流畅）
    write_yaml_file(hosts_content)
    with open(output_doc_file_path, "r") as old_readme_fb:
        old_content = old_readme_fb.read()
        old_hosts = old_content.split("```bash")[1].split("```")[0].strip()
        old_hosts = old_hosts.split("# Update time:")[0]
    if old_hosts == hosts_content:
        print("host not change")
        return False

    with open(template_path, "r") as temp_fb:
        template_str = temp_fb.read()
        hosts_content = template_str.format(hosts_str=hosts_content,
                                            update_time=update_time)
        with open(output_doc_file_path, "w") as output_fb:
            output_fb.write(hosts_content)
    return True


def write_yaml_file(hosts_content: str, ):
    output_yaml_file_path = os.path.join(os.path.dirname(__file__), 'hosts')
    with open(output_yaml_file_path, "w") as output_yaml_fb:
        output_yaml_fb.write(hosts_content)


def make_ipaddress_url(raw_url: str):
    """
    生成 ipaddress 对应的 url
    :param raw_url: 原始 url
    :return: ipaddress 的 url
    """
    dot_count = raw_url.count(".")
    if dot_count > 1:
        raw_url_list = raw_url.split(".")
        tmp_url = raw_url_list[-2] + "." + raw_url_list[-1]
        ipaddress_url = "https://" + tmp_url + IPADDRESS_PREFIX + "/" + raw_url
    else:
        ipaddress_url = "https://" + raw_url + IPADDRESS_PREFIX
    return ipaddress_url


@retry(tries=3)
def get_ip(session: requests.session, raw_url: str):
    url = make_ipaddress_url(raw_url)
    try:
        rs = session.get(url, timeout=5)
        pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ip_list = re.findall(pattern, rs.text)
        ip_counter_obj = Counter(ip_list).most_common(1)
        if ip_counter_obj:
            return raw_url, ip_counter_obj[0][0]
        raise Exception("ip address empty")
    except Exception as ex:
        print("get: {}, error: {}".format(url, ex))
        raise Exception


@retry(tries=3)
def update_gitee_gist(session: requests.session, host_content):
#     gitee_token = os.getenv("gitee_token")
    gitee_gist_id = os.getenv("gitee_gist_id")
    gist_file_name = os.getenv("gitee_gist_file_name")
    print(f'1. {os.getenv("gitee_token")} \n2. {os.getenv("gitee_gist_id")} \n3. {os.getenv("gitee_gist_file_name")} \n}') 
    #     gitee_token = "d2bf9f4136a13a7d284aa71fb1d62a16"
    #     gitee_gist_id = "h4dre3mblf8uknvx9y2wq35"
    print(os.environ,"os.environ")
    gist_file_name = "host"
    url = "https://gitee.com/api/v5/gists/{}".format(gitee_gist_id)
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Referer": "https://gitee.com/api/v5/swagger"
    }
    data = {
        "access_token": gitee_token,
        "files": {
            gist_file_name: {
                "content": host_content
            }
        },
        # "public": "true"
        # default private
    }
    json_data = json.dumps(data)
    print(url, json_data)
    try:
        response = session.patch(url,
                                 data=json_data,
                                 headers=headers,
                                 timeout=20)
        if response.status_code == 200:
            print("update gitee gist success")
        else:
            print("update gitee gist fail: {} {}".format(
                response.status_code, response.content))
    except Exception as e:
        traceback.print_exc(e)
        raise Exception(e)


def main():
    session = requests.session()
    content = ""
    for raw_url in RAW_URL:
        try:
            host_name, ip = get_ip(session, raw_url)
            content += ip.ljust(30) + host_name + "\n"
        except Exception:
            continue

    if not content:
        return
    update_time = datetime.utcnow().astimezone(timezone(
        timedelta(hours=8))).replace(microsecond=0).isoformat()
    hosts_content = HOSTS_TEMPLATE.format(content=content,
                                          update_time=update_time)
    has_change = write_file(hosts_content, update_time)
    if has_change:
        try:
            update_gitee_gist(session, hosts_content)
        except Exception as e:
            print("update gitee gist fail:{}".format(e))
    print(hosts_content)


if __name__ == '__main__':
    main()
