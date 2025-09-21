import os


def get_url_prefix(url: str) -> str:
    """Get the base URL prefix without query parameters and filename

    Args:
        url (str): The full URL including query parameters and filename

    Returns:
        str: The base URL prefix without query parameters and filename
    """
    return "/".join(url.split("?")[0].split("/")[:-1])


def get_url_basename(url: str) -> str:
    """Get the basename of the URL without query parameters

    Args:
        url (str): The full URL including query parameters

    Returns:
        str: The basename of the URL
    """
    return os.path.basename(url.split("?")[0])
