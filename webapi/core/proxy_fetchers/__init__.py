from os import listdir, getcwd
from os.path import isfile, join

def get_fetcher_script_list():
    self_path=f'{getcwd()}/core/proxy_fetchers/'
    only_files = [f.split('.py')[0] for f in listdir(self_path) if isfile(join(self_path, f)) and f not in ['__init__.py','fetch.py']]
    return only_files

__all__ = get_fetcher_script_list()

# __all__ = [
#     'freedashproxydashlistnet',
#     'freeproxylistsnet',
#     'proxy11com',
#     'proxydashlistdownload',
#     'proxynovacom',
#     'spysone',
#     'xroxycom'
# ]