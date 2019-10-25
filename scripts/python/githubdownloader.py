"""

    GitHub Downloader Module

    Allows you to download and install a github hosted Houdini library

        >>> gdtUrl = "https://github.com/sideeffects/GameDevelopmentToolset"
        >>> github_repo = GitHubDownloader(gdtUrl)
        >>> github_repo.install_latest_release()

    You can also query the repo for releases

        >>> releases = github_repo.list_releases()

    Install a specific release

        >>> github_repo.install_release(releases[0])

    And Determine which version is currently installed

        >>> installed_version = github_repo.get_installed_version()


"""

import os
import shutil
import urllib
import json
import zipfile
import platform
import re
import logging
from collections import OrderedDict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# you can add an api token from github while testing, github has a limit of 60 calls per hour
# the syntax is ?client_id=YOURCLIENTID&client_secret=YOURCLIENTSECRET
CLIENT_SECRET = ""

HOUDINI_DIR = os.getenv("HOUDINI_USER_PREF_DIR", "")

if not HOUDINI_DIR and platform.system() == "Windows":
    HOUDINI_DIR = os.path.join(os.getenv("USERPROFILE", ""), "Documents", "Houdini16.5")

HOUDINI_ENV = os.path.join(HOUDINI_DIR, "houdini.env")

if platform.system() == "Windows":
    HOU_TEMP_PATH = os.path.join(os.getenv("APPDATA"), "SideFX")
else:
    HOU_TEMP_PATH = os.path.join(os.getenv("HOUDINI_USER_PREF_DIR"))


class GitHubDownloader(object):
    """
        Helper class to download versions from GitHub


    """

    def __init__(self, repo_url):
        if not repo_url:
            raise ValueError("Invalid Repository: %s " % repo_url)

        self.repo_url = repo_url

        self.api_url = self.repo_url.replace("github.com", "api.github.com/repos")
        self.repo_name = self.repo_url.split("/")[-1]

        self.releases = []
        self.releases_dict = OrderedDict()

        logger.debug("Github Downloader Initialized with Repo: %s" % repo_url)

    def list_releases(self, version_filter=None, production_only=False):

        # if we don't have any release cached internally
        if not self.releases:
            self.releases = self.__get_release_list_from_github()
            if not len(self.releases):
                self.releases = self.__get_release_list_from_github(tags=True)

        filtered_release_list = self.releases
        if version_filter and len(self.releases):
            if "tag_name" in self.releases[0]:
                filtered_release_list = [release for release in filtered_release_list if
                                         re.match(version_filter, release["tag_name"])]
            else:
                filtered_release_list = [release for release in filtered_release_list if
                                         re.match(version_filter, release["name"])]

        if production_only:
            filtered_release_list = [release for release in filtered_release_list if "prerelease" in release.keys()
                                     and not release["prerelease"]]

        self.releases_dict.clear()
        for release in filtered_release_list:
            if "tag_name" in release:
                self.releases_dict[release["tag_name"]] = release
            else:
                self.releases_dict[release["name"]] = release

        return self.releases_dict.keys()

    def get_installed_version(self):
        logger.debug("Getting Installed Version...")
        version_line = ""
        with open(HOUDINI_ENV, "r") as fp:
            read_next_line = False
            for line in fp.readlines():
                if "# " + self.repo_name.upper() in line:
                    read_next_line = True
                    continue

                if read_next_line:
                    version_line = line
                    break

        if version_line:
            version_number = version_line.split()[-1].split(";")[0].split("\\")[-1]

            logger.debug("Found Installed Version : %s" % version_number)
            return version_number
        else:
            logger.debug("No Version found in local houdini.env file")

            return None

    def install_latest_release(self):

        release_list = self.list_releases()
        if len(release_list):
            self.install_release(release_list[0])
        else:
            self.install_from_source()

    def install_from_source(self):
        url = self.__get_source_download_url()

        default_branch = self.__get_default_branch_from_github()

        release_version = self.__get_latest_commit_from_github(default_branch)[:7]

        local_path = self.__download_zip_file(url, HOU_TEMP_PATH)

        self.__install_release_from_zip_file(local_path, release_version)

    def install_release(self, release_name):
        self.list_releases(version_filter=release_name)
        if release_name in self.releases_dict:

            release = self.releases_dict[release_name]
            url = self.__get_release_download_url(release, app_version_filter="16.5")
            if "tag_name" in release:
                release_version = release["tag_name"]
            else:
                release_version = release["name"]
            local_path = self.__download_zip_file(url, HOU_TEMP_PATH)

            self.__install_release_from_zip_file(local_path, release_version)

    def __install_release_from_zip_file(self, zip_file, release_version, force=True):

        local_extract_path = os.path.join(HOU_TEMP_PATH, self.repo_name, release_version)

        # clear local path in case of reinstallation
        if os.path.exists(local_extract_path):

            # if we're not reinstalling, move along
            if not force:
                return

            # if we are, clear the local directory
            shutil.rmtree(local_extract_path)

        self.__unzip_file(zip_file, local_extract_path)

        contents = os.listdir(local_extract_path)
        if len(contents) == 1:
            self.__move_files_up_a_folder(os.path.join(local_extract_path, contents[0]))

        self.__patch_houdini_env(local_extract_path)

    def __get_default_branch_from_github(self):

        logger.debug("Getting Default Branch from Github")

        response = urllib.urlopen(self.api_url + CLIENT_SECRET)
        data = response.read()
        if data == "":
            raise ValueError("Unable to get the default branch")

        j_data = json.loads(data.decode('utf-8'))
        branch = j_data["default_branch"]

        logger.debug("Default Branch is : %s" % branch)

        return branch

    def __get_latest_commit_from_github(self, branch):

        response = urllib.urlopen(self.api_url + "/branches" + CLIENT_SECRET)
        data = response.read()
        if data == "":
            raise ValueError("Unable to get the release list")

        j_data = json.loads(data.decode('utf-8'))
        for branch_data in j_data:
            if branch_data["name"] == branch:
                return branch_data["commit"]["sha"]
        return None

    def __get_release_list_from_github(self, tags=False):

        data_type = "releases"
        if tags:
            data_type = "tags"

        response = urllib.urlopen(self.api_url + "/" + data_type + CLIENT_SECRET)
        data = response.read()
        if data == "":
            raise ValueError("Unable to get the release list")

        j_data = json.loads(data.decode('utf-8'))
        return j_data

    def __get_source_download_url(self):
        return self.api_url + "/zipball" + CLIENT_SECRET

    @staticmethod
    def __get_release_download_url(release, app_version_filter=None, old_version_safeguard=False):
        """
            for a given release dictionary entry, get the url to download it
        """
        if "assets" in release.keys():
            for asset in release["assets"]:

                url = os.path.basename(asset["browser_download_url"])

                if app_version_filter:
                    # If we find something named HoudiniXX.X-Y.YY.zip that's the one we want
                    if ("Houdini" + app_version_filter) in url and "zip" in url:
                        return asset["browser_download_url"]

                if old_version_safeguard:
                    # For older versions we want to grab the Development branch of that version by default
                    if "Development" in url and "zip" in url:
                        return asset["browser_download_url"]

        # fall back in case there aren't any assets (just download the source zip file)
        return release["zipball_url"] + CLIENT_SECRET

    def __patch_houdini_env(self, local_path, mode="change"):

        filepath = HOUDINI_ENV
        if platform.system() == "Windows":
            sep = ";"
            quote_char = ""
        else:
            sep = ":"
            quote_char = "\""

        to_write = []
        has_houdini_path_defined = False

        with open(filepath, "r") as fp:
            skip_next_line = False
            skipped_lines = 0
            for line in fp.readlines():
                if skip_next_line:
                    skipped_lines += 1

                    if skipped_lines == 3:
                        skip_next_line = False
                        skipped_lines = 0
                    continue

                if "# " + self.repo_name.upper() in line:
                    skip_next_line = True
                    continue

                if "HOUDINI_PATH" in line:
                    has_houdini_path_defined = True

                to_write.append(line)

        if to_write[-1][-1] != "\n":
            to_write[-1] += "\n"
            to_write.append("\n")

        if to_write[-1] != "\n":
            to_write.append("\n")

        if mode == "change":
            to_write.append("# " + self.repo_name.upper() + "\n")

            entry = "HOUDINI_PATH = "
            entry += quote_char + local_path
            if has_houdini_path_defined:
                entry += sep + "$HOUDINI_PATH" + quote_char + "\n"
            else:
                entry += sep + "&" + quote_char + "\n"

            to_write.append(entry)

        with open(filepath, "w") as fp:
            for line in to_write:
                fp.write(line)

    @staticmethod
    def __unzip_file(zip_file, destination_path):
        zipf = zipfile.ZipFile(zip_file, 'r', zipfile.ZIP_DEFLATED)
        zipf.extractall(destination_path)

    @staticmethod
    def __download_zip_file(url, local_dir):

        filename = os.path.basename(url)
        if not filename.endswith(".zip"):
            filename = filename.split("?")[0] + ".zip"

        local_path = os.path.join(local_dir, filename)

        if not os.path.exists(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))

        urllib.urlretrieve(url, local_path)

        return local_path

    @staticmethod
    def __move_files_up_a_folder(base_dir):

        parent_dir = os.path.dirname(base_dir)
        for root, dirs, files in os.walk(base_dir, topdown=False):
            for name in files:
                current_path = os.path.join(root, name)
                rel_path = os.path.relpath(current_path, base_dir)
                new_path = os.path.join(parent_dir, rel_path)
                if not os.path.exists(os.path.dirname(new_path)):
                    os.makedirs(os.path.dirname(new_path))
                shutil.copy(current_path, os.path.join(parent_dir, rel_path))
        shutil.rmtree(base_dir)

if __name__ == "__main__":
    import doctest
    doctest.testmod()