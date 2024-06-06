import requests
import time
from pydub import AudioSegment
from io import BytesIO
import copy

def download_file(url, filename):
	response = requests.get(url)
	with open(filename, "wb") as f:
		f.write(response.content)


def get_session_id(headers):
	url = "https://clerk.suno.com/v1/client?_clerk_js_version=4.73.2"
	response = requests.get(url, headers=headers)
	data = response.json()
	r = data.get("response")
	sid = r.get("last_active_session_id")
	return sid

def get_token(headers, sid):
	# 构建url
	url = f"https://clerk.suno.com/v1/client/sessions/{sid}/tokens?_clerk_js_version=4.73.2"

	# POST这个url，post的参数就是_clerk_js_version=4.73.2
	response = requests.post(url, headers=headers)
	data = response.json()

	token = data['jwt']

	return token

def get_song_info(headers, token, song_create_params):
	# 请求的url
	url = "https://studio-api.suno.ai/api/generate/v2/"

	# header增加Authorization字段为Bearer token
	headers['Authorization'] = f"Bearer {token}"

	# post请求
	response = requests.post(url, headers=headers, json=song_create_params)

	# 返回的数据
	data = response.json()

	# 流式id：data['clips'][i]['id']
	stream_ids = []
	for i in range(len(data['clips'])):
		stream_ids.append(data['clips'][i]['id'])

	return stream_ids


def process_audio(headers, token, stream_ids):
	# 请求的url
	url = f"https://studio-api.suno.ai/api/feed/?ids={stream_ids[0]}%2C{stream_ids[1]}"

	# header增加Authorization字段为Bearer token
	headers['Authorization'] = f"Bearer {token}"

	songs = ""

	while True:
		# GET请求
		response = requests.get(url, headers=headers)
		data = response.json()

		# 判断一下data是否有detail
		if 'detail' in data:
			# 生成完成了
			print("歌曲生成完成，等待20s开始下载")
			time.sleep(20)

			for song in songs:

				# 获取song的id
				song_id = song['id']

				# 开始下载

				if song['audio_url'] != "":
					print(f"Downloading {song_id}_audio.mp3...")
					download_file(song['audio_url'], f"{song_id}_audio.mp3")

				if song['video_url'] != "":
					print(f"Downloading {song_id}_video.mp4...")
					download_file(song['video_url'], f"{song_id}_video.mp4")

				if song['image_url'] != "":
					print(f"Downloading {song_id}_image.jpg...")
					download_file(song['image_url'], f"{song_id}_image.jpg")

			break


		else:
			# hard copy data
			songs = copy.deepcopy(data)

			# 生成还没完成，等待10s
			time.sleep(10)

if __name__ == '__main__':

	# 读取cookie.text
	with open("cookie.txt", "r") as f:
		cookie = f.read()

	headers = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'Accept-Language': 'zh-CN,zh;q=0.9',
		'Cache-Control': 'max-age=0',
		'Cookie': cookie,
		'Priority': 'u=0, i',
		'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
		'Sec-Ch-Ua-Mobile': '?0',
		'Sec-Ch-Ua-Platform': '"Windows"',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'none',
		'Sec-Fetch-User': '?1',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
	}

	# 第一步，获取session id
	session_id = get_session_id(headers)

	# 第二步，获取token
	token = get_token(headers, session_id)

	# 第三步，输入参数
	song_create_params = {
		"prompt":"", # 歌词，置空则为纯音乐否则不是纯音乐
		"tags":"piano, piano, {{guitar}}", # tags，用逗号隔开
		"mv":"chirp-v3-5", # 模型：v3.5模型可生成4分钟
		"title":"爱你V21", # 歌曲的标题
		# "continue_clip_id":None, # 继续创作的歌曲id
		# "continue_at":None, # 继续创作的时间点
		# "infill_start_s":None, # 填充到某个时刻
		# "infill_end_s":None, # 填充结束的时刻
		# "gpt_description_prompt": "如果你突然打了个喷嚏，那一定就是我在想你", # 如果同时填写title和这个字段，那么标题由这个字段决定，如果同时填写prompt和这个字段，那么歌词也是由这个字段决定的！
		# "audio_prompt_id":None, # 发送到GPT的ID
		# "history":None, # 处理的历史记录
		# "concat_history":None, # 拼接的历史记录
		# "type":"gen", # 类型，gen为生成
		# "duration":100, # 时长，如果设置太低那么就会有一首歌生成失败从而导致退款，因此不建议设置
		# "refund_credits":None, # 生成失败的退款
		# "stream":True, # 是否流式生成，默认为True，即通过轮询的方式流式生成，不建议修改
		# "error_type":None, # 错误类型
		# "error_message":None # 错误信息
	}
	stream_ids = get_song_info(headers, token, song_create_params)

	print(stream_ids)

	# 对data进行轮询并且下载歌曲到本地
	process_audio(headers, token, stream_ids)
