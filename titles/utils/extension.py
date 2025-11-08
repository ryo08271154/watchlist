import requests
MIN_SUPPORTED_VERSION = "0.1"
MAX_SUPPORTED_VERSION = "0.99"


def is_extension_version_supported(version: str) -> bool:
    def version_to_tuple(ver: str, length: int = 3):
        parts = ver.split(".")
        parts += ["0"] * (length - len(parts))
        return tuple(map(int, parts[:length]))

    min_version = version_to_tuple(MIN_SUPPORTED_VERSION)
    max_version = version_to_tuple(MAX_SUPPORTED_VERSION)
    target_version = version_to_tuple(version)

    return min_version <= target_version <= max_version


def get_extension_download_url():
    api_url = "https://api.github.com/repos/ryo08271154/watchlist-extension/releases"
    response = requests.get(api_url)
    if response.status_code != 200:
        return None
    releases = response.json()
    if not releases:
        return None
    for release in releases:
        if is_extension_version_supported(release["tag_name"].replace("v", "")):
            return release["zipball_url"]
    return None
