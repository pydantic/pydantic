import os
import sys
from pathlib import Path


def error(msg: str):
    print(f'ERROR: {msg}', file=sys.stderr)
    exit(1)


try:
    import requests
except ImportError:
    error("requests not installed, you'll need to run `pip install requests`")


def main():
    root_dir = Path(__file__).parent.parent
    try:
        wheel_file = next(p for p in (root_dir / 'dist').iterdir() if p.name.endswith('wasm32.whl'))
    except StopIteration:
        error('No wheel found in "dist" directory')
    else:
        uploader = Uploader()

        wheel_url = uploader.upload_file(wheel_file)
        print(f'Wheel uploaded ✓, URL: "{wheel_url}"')


class Uploader:
    def __init__(self):
        try:
            auth_key = os.environ['SMOKESHOW_AUTH_KEY']
        except KeyError:
            raise RuntimeError('No auth key provided, please set SMOKESHOW_AUTH_KEY')
        else:
            self.client = requests.Session()
            r = self.client.post('https://smokeshow.helpmanual.io/create/', headers={'Authorisation': auth_key})
            if r.status_code != 200:
                raise ValueError(f'Error creating ephemeral site {r.status_code}, response:\n{r.text}')

            obj = r.json()
            self.secret_key: str = obj['secret_key']
            self.url: str = obj['url']
            assert self.url.endswith('/'), self.url

    def upload_file(self, file: Path) -> str:
        headers = {'Authorisation': self.secret_key, 'Response-Header-Access-Control-Allow-Origin': '*'}

        url_path = file.name
        url = self.url + file.name
        r = self.client.post(url, data=file.read_bytes(), headers=headers)
        if r.status_code == 200:
            upload_info = r.json()
            print(f'    uploaded {url_path} size={upload_info["size"]:,}')
        else:
            print(f'    ERROR! {url_path} status={r.status_code} response={r.text}')
            error(f'invalid response from "{url_path}" status={r.status_code} response={r.text}')
        return url


if __name__ == '__main__':
    main()
