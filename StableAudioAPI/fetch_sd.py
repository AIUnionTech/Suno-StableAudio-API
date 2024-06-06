import requests
import json
import time
import os

def read_token():
    with open(os.path.join(os.path.dirname(__file__), 'token.json'), 'r', encoding='utf8') as f:
        token_data = json.load(f)
    return token_data['token']

def download_file(url, file_path):
    try:
        token = read_token()
        retry_count = 0
        max_retries = 50
        retry_delay = 3  # 3 seconds

        while retry_count < max_retries:
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            response = requests.get(url, headers=headers, stream=True)

            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print('File downloaded successfully!')
                return
            elif response.status_code == 202:
                print('Generation in progress, retrying in 3 seconds...')
                time.sleep(retry_delay)
                retry_count += 1
            else:
                print(f'Error downloading file: {response.status_code}')
                return

        print('Maximum number of retries reached, unable to download file.')
    except Exception as e:
        print(f'Error downloading file: {e}')

def generate_audio(prompt, length_seconds=178, seed=123):
    try:
        token = read_token()
        url = 'https://api.stableaudio.com/v1alpha/generations/stable-audio-audiosparx-v2-0/text-to-music'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        data = {
            "data": {
                "type": "generations",
                "attributes": {
                    "prompts": [
                        {
                            "text": prompt,
                            "weight": 1
                        }
                    ],
                    "length_seconds": length_seconds,
                    "seed": seed
                }
            }
        }

        response = requests.post(url, headers=headers, json=data)
        print(f'Status Code: {response.status_code}')

        print(response.json())

        # Extract the result URL from the response
        result_url = response.json()['data'][0]['links']['result']

        # Download the result file
        file_path = os.path.join(os.path.dirname(__file__), 'audio_file.mp3')
        download_file(result_url, file_path)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    # first param: prompt, second is the length (seconds) (optional)
    # and the rest is the seed (optional)
    generate_audio("prompt", 180, 123)  # Prompt (required) | Length (optional) | Seed (optional)