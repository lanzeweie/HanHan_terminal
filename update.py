import json
from itertools import zip_longest

import requests


class VersionChecker:
    GITHUB_RELEASES_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
    GITEE_RELEASES_URL = "https://gitee.com/api/v5/repos/{owner}/{repo}/releases/latest?access_token={access_token}"
    GITHUB_OWNER = "lanzeweie"
    GITHUB_REPO = "HanHan_terminal"
    GITEE_OWNER = "buxiangqumingzi"
    GITEE_REPO = "han-han_terminal"
    CURRENT_VERSION = "1.2.3"
    TIMEOUT = 0.5

    def __init__(self):
        self.github_owner = self.GITHUB_OWNER
        self.github_repo = self.GITHUB_REPO
        self.gitee_owner = self.GITEE_OWNER
        self.gitee_repo = self.GITEE_REPO
        self.current_version = self.CURRENT_VERSION
        self.access_token = "10ca1c7562fd92a87c3205d7af8ba01d"  # Your access token

    def fetch_latest_release(self, url):
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            return response.json() if response.ok else None
        except requests.RequestException:
            return None

    def compare_versions(self, current_version, release_version):
        try:
            current_tuple = tuple(map(int, current_version.split(".")))
            release_tuple = tuple(map(int, release_version.split(".")))
            for a, b in zip_longest(current_tuple, release_tuple, fillvalue=0):
                if a != b:
                    return a > b
            return True
        except ValueError:
            return False

    def check_for_updates(self):
        github_url = self.GITHUB_RELEASES_URL.format(owner=self.github_owner, repo=self.github_repo)
        latest_release = self.fetch_latest_release(github_url)

        if not latest_release:
            gitee_url = self.GITEE_RELEASES_URL.format(owner=self.gitee_owner, repo=self.gitee_repo, access_token=self.access_token)
            latest_release = self.fetch_latest_release(gitee_url)

        if latest_release:
            release_version = latest_release["tag_name"].lstrip('v')
            if not self.compare_versions(self.current_version, release_version):
                print(f"发现新版本(v{release_version})！")
                return False
            else:
                print("当前已是最新版本。")
                return True
        else:
            print("网络错误，无法访问GitHub或Gitee Release API。")
            return True


if __name__ == "__main__":
    checker = VersionChecker()
    checker.check_for_updates()
