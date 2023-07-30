import requests
import time
import pathlib as Path

def make_request(url):
	"""
	Make get request to basketball-references.com
	"""
	try:
		response = requests.get(url)
		if response.status_code == 429:
			raise requests.exceptions.HTTPError("Rate limit exceeded")
		response.raise_for_status()
		return response
	except requests.exceptions.RequestException as e:
		print(f"Network request error: {e}")
		return None

def retry_request(url, max_retries=3):
	"""
	Retry on get requests
	"""
	retries = 0
	while retries < max_retries:
		response = make_request(url)
		if response.status_code == 429:
			retries += 1
			sleep_duration = int(response.headers.get("Retry-After", 1))
			print(f"Retrying after {sleep_duration} seconds")
			time.sleep(sleep_duration)
		else:
			return response

def file_writer(dir_name, file_name, response, target_dir=None, parsed=False):
	"""
	Write HTML files to directory
	"""
	if target_dir is None:
		target_dir = Path.cwd()
	else:
		target_dir = Path(target_dir)
		
	target_dir = target_dir / dir_name
	target_dir.mkdir(parents=True, exist_ok=True)

	file_path = target_dir / f"{file_name}.html"
	with open(file_path, "w+") as file:
		if parsed:
			file.write(str(response))
		else:		
			file.write(response.text)		
	# Read and return the content of the file
	with open(file_path) as file:
		page = file.read()

	return page

def fetch_paths(is_dir=False, target_dir=None, contains=None):
	if target_dir:
		dir = Path(f"{Path.cwd()}/{target_dir}")
	else:
		dir = Path(f"{Path.cwd()}")
	if is_dir:
		items = [item.as_posix() for item in dir.iterdir() if item.is_dir()]
	else:
		items = [item.as_posix() for item in dir.iterdir() if item.is_file()]
		
	if contains:
		items = [item for item in items if f"{contains}" in item]
		
	return items
