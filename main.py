import os
import time
import requests
from colorama import Fore, Style, init

init()

IMGBB_API_KEY = '' # Add your Imgbb API key
IMGBB_UPLOAD_URL = 'https://api.imgbb.com/1/upload'
FACE_SWAP_URL = "https://api.aiunivers.net/v2/faceswap"
JOB_STATUS_URL = "https://api.aiunivers.net/v2/jobId"
API_TOKEN = ''  # Add your Aiunivers API token

# Fixed swap image URL
SWAP_IMAGE_URL = "" # Add your target swap image Url

headers = {
    'X-API-KEY': API_TOKEN
}

# Function to upload image to ImgBB
def upload_image_to_imgbb(image_path):
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            IMGBB_UPLOAD_URL,
            files={'image': image_file},
            data={'key': IMGBB_API_KEY}
        )
    result = response.json()
    if response.status_code == 200 and result.get('data'):
        return result['data']['url']
    else:
        return None

# Function to start a face swap job
def start_face_swap(target_image_url):
    payload = {
        "target_image": target_image_url,
        "swap_image": SWAP_IMAGE_URL
    }
    response = requests.post(FACE_SWAP_URL, json=payload, headers=headers)
    response_data = response.json()
    if response.status_code == 200:
        return response_data.get("job"), response_data.get("status")
    else:
        print(Fore.RED + "Failed to start face swap job." + Style.RESET_ALL)
        return None, None

def check_job_status(job_id):
    payload = {
        "job": job_id
    }
    response = requests.post(JOB_STATUS_URL, json=payload, headers=headers)
    return response.json()

def main():

    image_folder = "images"
    out_folder = "out"
    os.makedirs(out_folder, exist_ok=True)

    # Get all images in the folder
    images = [img for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]

    for image in images:
        # Upload image to ImgBB and get the URL
        target_image_path = os.path.join(image_folder, image)
        target_image_url = upload_image_to_imgbb(target_image_path)
        if not target_image_url:
            print(Fore.RED + f"Failed to upload image: {image}" + Style.RESET_ALL)
            continue
        print(f"Processing image: {image}")

        # Start face swap job
        job_id, status = start_face_swap(target_image_url)
        if not job_id:
            print(Fore.RED + f"Failed to start face swap job for image: {image}" + Style.RESET_ALL)
            continue
        print(f"Job ID: {job_id}, Initial Status: {status}")

        # Poll job status every 8 seconds
        while status == "queued" or status == "generating":
            time.sleep(8)
            job_status = check_job_status(job_id)
            status = job_status.get("status")
            print(f"Job {job_id} status: {status}")

        # Check final status
        if status == "succeeded":
            image_url = job_status.get("imageUrl")
            if not image_url:
                print(Fore.RED + f"Image URL is missing for Job ID: {job_id}" + Style.RESET_ALL)
                continue

            print(f"Downloading final image from: {image_url}")
            response = requests.get(image_url)
            output_image_path = os.path.join(out_folder, image)
            with open(output_image_path, 'wb') as f:
                f.write(response.content)
            print(Fore.GREEN + f"Job {job_id} completed: {output_image_path}" + Style.RESET_ALL)
        elif status == "failed":
            print(Fore.RED + f"Job {job_id} failed." + Style.RESET_ALL)

    print(Fore.YELLOW + """
█▀▀ █▄ █ █▀▄ 
██▄ █ ▀█ █▄▀
""" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
