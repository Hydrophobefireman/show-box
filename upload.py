import cloudinary.uploader
import os

import set_env

set_env.set_env_vars()


def upload(imgurl: str) -> dict:
    clapi_key = os.environ.get("clapi_key")
    clapi_secret = os.environ.get("cl_secret")
    if clapi_key is None:
        raise Exception("no key provided")
    cloudinary.config(
        cloud_name="media-proxy", api_key=clapi_key, api_secret=clapi_secret
    )
    a = cloudinary.uploader.upload(imgurl)
    return a


if __name__ == "__main__":
    data = upload(input("enter url:"))
    print("Raw Data:%s\n\n" % (data))
    print(data.get("secure_url"))
