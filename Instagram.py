# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     Instagram
   Description :
   Author :        JHao
   date：          2020/4/17
-------------------------------------------------
   Change Activity:
                   2020/4/17:
-------------------------------------------------
"""
__author__ = 'JHao'

import os
import re
import sys
import json
import time
from urllib.request import urlretrieve

from Common.SpiderBase import SpiderBase
from Crawler.Instagram.user_name import USER_NAMES

BASE_URL = "https://www.instagram.com"
USER_INDEX_URL = "https://www.instagram.com/{user_name}/"
USER_MEDIA_API_URL = "https://www.instagram.com/graphql/query/"


def cbk(a, b, c):
    """
    回调函数
    Args:
        a: 已经下载的数据块
        b: 数据块的大小
        c: 远程文件的大小
    Returns:
    """
    output = sys.stdout
    per = 100.0 * a * b / c
    if per > 100:
        per = 100
    output.write('\r complete percent:%.0f%%' % per)
    output.flush()


class Instagram(SpiderBase):
    name = "instagram"

    def __init__(self):
        SpiderBase.__init__(self, self.name)
        self.max_count = 1000
        self.count = 0

    def get_user_id_and_encrypt_js(self, user_name):
        """
        get user ID and encrypt js url
        :param user_name:
        :return:
        """
        url = USER_INDEX_URL.format(user_name=user_name)
        self.log.info("request user index: %s" % url)
        res = self.request.get(url).text
        if "页面不存在" in res:
            self.log.info("user: %s not exists!" % user_name)
        user_id = "".join(re.findall(r"\"profilePage_(.*?)\"", res)).strip()
        encrypt_js = "".join(re.findall(r"(/static/[0-9A-Za-z/]*?/ProfilePageContainer\.js/.*?\.js)\",", res)).strip()
        if not user_id:
            self.log.error("get user ID error")
        if not encrypt_js:
            self.log.error("get encrypt js error")
        return user_id, encrypt_js

    def get_query_hash(self, encrypt_js):
        """
        get query hash from encrypt_js file
        :param encrypt_js:
        :return:
        """
        url = BASE_URL + encrypt_js
        self.log.info("request encrypt_js: %s" % url)
        res = self.request.get(url).text
        query_hash = "".join(re.findall(r"profilePosts.*?queryId:\"([0-9A-Za-z/]*?)\",", res))
        if not query_hash:
            self.log.error("get query hash error")
        return query_hash

    def get_media_url(self, user_id, query_hash, cursor):
        """
        fetch user pic & video
        :param user_id:
        :param query_hash:
        :param cursor:
        :return:
        """
        variable = {"id": user_id, "first": 12,
                    "after": cursor}
        params = {"query_hash": query_hash,
                  "variables": json.dumps(variable)}
        self.log.info("request user media, params: %s" % json.dumps(params))
        res = self.request.get(USER_MEDIA_API_URL, params=params)
        if res.status_code == 200:
            user_data = res.json().get("data", {}).get("user", {})
            edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
            page_info = user_data.get("edge_owner_to_timeline_media", {}).get("page_info", {})
            for entry in edges:
                media_id = entry.get("node", {}).get("id")
                media_code = entry.get("node", {}).get("shortcode")
                is_video = entry.get("node", {}).get("is_video")
                self.count += 1
                if is_video:
                    media_url = entry.get("node", {}).get("video_url")
                else:
                    media_url = entry.get("node", {}).get("display_url")
                yield {"id": media_id, "code": media_code, "url": media_url}
            if page_info.get("has_next_page") and self.max_count > self.count:
                time.sleep(3)
                yield from self.get_media_url(user_id, query_hash, page_info.get("end_cursor"))
        else:
            self.log.error("request user media error, http status %s" % res.status_code)

    def download_media(self, media_info):
        """
        download pic & video
        :param media_info:
        :return:
        """
        url = media_info.get("url")
        file_name = url.split("?")[0].split("/")[-1]
        dir_name = os.path.join("./data", media_info.get("user_name"))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        file_name = os.path.join(dir_name, file_name)
        self.log.info("download media: %s to %s" % (media_info.get("id"), file_name))
        retry = 5
        while retry > 0:
            try:
                urlretrieve(url, file_name, cbk)
                break
            except Exception as e:
                self.log.error(str(e))
                retry -= 1
                self.log.error('download error, retry')
                time.sleep(3)
        print()

    def main(self, user_name):
        self.log.info("enter main")
        # for user_name in USER_NAMES:
        self.log.info("start crawl user: %s" % user_name)
        user_id, encrypt_js = self.get_user_id_and_encrypt_js(user_name)
        if user_id and encrypt_js:
            self.log.info("get user ID: %s" % user_id)
            self.log.info("get encrypt js: %s" % encrypt_js)
            query_hash = self.get_query_hash(encrypt_js)
            if query_hash:
                self.log.info("get query_hash: %s" % query_hash)
                for media_info in self.get_media_url(user_id, query_hash, ""):
                    media_info.update({"user_name": user_name})
                    self.download_media(media_info)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        username = sys.argv[1]
        i = Instagram()
        i.main(username)
