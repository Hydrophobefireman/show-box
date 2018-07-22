import cloudinary.uploader
import os


def upload(imgurl):
    clapi_key = os.environ.get("key")
    clapi_secret = os.environ.get("cl_secret")
    if clapi_key is None: 
        try:
            with open("a.cloudinary", "r") as f:
                clapi_key = f.read()
            with open("b.cloudinary", "r") as f:
                clapi_secret = f.read()
        except:
            raise Exception("no key provided")
    cloudinary.config(
        cloud_name="media-proxy",
        api_key=clapi_key,
        api_secret=clapi_secret
    )
    a = cloudinary.uploader.upload(imgurl)
    return a


if __name__ == "__main__":
    data = upload(input("enter url:"))
    print("Raw Data:%s\n\n" % (data))
    print(data.get('secure_url'))
