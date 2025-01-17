import os
import pickle
import json
import hashlib
import logging
import re
import warnings
from pathlib import Path
import gzip

log = logging.getLogger(__name__)


class Cache(object):
    """Cache: Handle storing and loading request info and responses in the cache"""

    def __init__(self, payload, safe_exit, cache_dir=None):
        # generating key
        key_str = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.key = hashlib.md5(key_str).hexdigest()
        print(f'Response cache key: {self.key}')

        # create cache folder
        self.folder = str(cache_dir) if cache_dir else "./cache"
        try:
            Path(self.folder).mkdir(exist_ok=True, parents=True)
        except Exception as exc:
            log.debug(f'Folder creation failed - {exc}')

        self.response_cache = []
        self.size = 0
        if safe_exit:
            self.check_cache()

    def cache_responses(self, responses):
        if responses:
            num_resp = len(responses)
            checkpoint = len(self.response_cache) + 1
            self.size += num_resp
            log.info(
                f'File Checkpoint {checkpoint}:: Caching {num_resp} Responses')

            filename = f'{checkpoint}-{self.key}-{num_resp}.pickle.gz'
            self.response_cache.append(filename)

            with gzip.open(f'{self.folder}/{filename}', 'wb') as handle:
                pickle.dump(responses, handle,
                            protocol=pickle.HIGHEST_PROTOCOL)

    def load_info(self):
        try:
            with gzip.open(f'{self.folder}/{self.key}_info.pickle.gz', 'rb') as handle:
                return pickle.load(handle)
        except Exception:
            log.info('No previous requests to load')

    def load_resp(self, cache_num):
        filename = self.response_cache[cache_num]
        try:
            with gzip.open(f'{self.folder}/{filename}', 'rb') as handle:
                return pickle.load(handle)
        except Exception as exc:
            warnings.warn(f'Failed to load responses from {filename} - {exc}')

    def save_info(self, **kwargs):
        filename = f'{self.folder}/{self.key}_info.pickle.gz'
        with gzip.open(filename, 'wb') as handle:
            pickle.dump(kwargs, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def check_cache(self):
        for filename in os.listdir(self.folder):
            m = re.match(f"\d+-{self.key}-(\d+).pickle.gz", filename)
            if m:
                self.response_cache.append(m.group(0))
                self.size += int(m.group(1))
