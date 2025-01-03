from django.conf import settings
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
from io import BytesIO
import base64
import os
import datetime
from geopy.geocoders import Nominatim


def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_datas(directory):
    # 지원하는 이미지 파일 확장자
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp"}

    files = [os.path.join(directory, file) for file in os.listdir(directory) if
             os.path.isfile(os.path.join(directory, file))]
    files.sort(key=lambda x: os.path.getctime(x))
    image_datas = [get_image_base64(file) for file in files if os.path.splitext(file)[-1].lower() in image_extensions]
    return image_datas


def get_folder_path(ss_no):
    ss_year = ss_no[2:6]
    ss_month = ss_no[6:8]
    ss_day = ss_no[8:10]
    ss_number = ss_no[10:]
    return f'/{ss_year}/{ss_month}/{ss_day}/{ss_number}/'


def check_file_extension(uploaded_file: InMemoryUploadedFile):
    # 파일 이름에서 확장자를 추출
    extension = uploaded_file.name.split('.')[-1].lower()
    return extension


def is_valid_image(files):
    valid_image = []
    for file in files:
        if not check_file_extension(file) in {"jpg", "jpeg", "png", "bmp"}:
            continue
        try:
            img = Image.open(file)
            img.verify()  # 이미지 파일이 유효한지 확인합니다.
            valid_image.append(file)
        except (IOError, SyntaxError):
            continue
    return valid_image


def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)


def get_address_gps(gps_info):
    latitude = convert_to_degrees(gps_info[2])
    lat_ref = gps_info[1]

    # 남위인 경우 음수로 변환
    if lat_ref != "N":
        latitude = -latitude

    longitude = convert_to_degrees(gps_info[4])
    lon_ref = gps_info[3]

    # 서경(West)인 경우 음수로 변환
    if lon_ref != "E":
        longitude = -longitude

    geolocoder = Nominatim(user_agent='South Korea', timeout=None)
    location = geolocoder.reverse(f'{latitude}, {longitude}', exactly_one=True)
    return location.address


def trans_image(file, ss_user):
    img = Image.open(file)

    watermark = ''
    img_datetime = ''
    exif = img._getexif()
    if exif:
        exif = {
            TAGS.get(tag): value
            for tag, value in exif.items()
            if tag in TAGS
        }

        orientation = exif.get("Orientation")
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)

        try:
            address = get_address_gps(exif.get("GPSInfo"))
        except:
            address = ''

        img_datetime = exif.get("DateTimeOriginal")
        watermark += address + '\n'

    if not img_datetime:
        img_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    watermark += img_datetime + '\n' + ss_user

    maxDimension = 1920

    width = img.width
    height = img.height

    if width > height:
        if width > maxDimension:
            height *= maxDimension / width
            width = maxDimension
    else:
        if height > maxDimension:
            width *= maxDimension / height
            height = maxDimension

    newSize = (int(width), int(height))

    img = img.resize(newSize)

    img = img.convert("RGBA")
    text_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)

    font_size = int(width/40)
    font = ImageFont.truetype('static/font/malgun.ttf', size=font_size)

    draw.text((20, 20), watermark, fill=(255, 255, 255) + (200,), font=font)

    img = Image.alpha_composite(img, text_layer)

    img_io = BytesIO()
    img = img.convert("RGB")
    img.save(img_io, format='JPEG')
    return img_io


def imglist(request):
    req = request.GET
    ss_no = req.get('ss_no')
    ss_uuid = req.get('ss_uuid')
    ss_user = req.get('ss_user')

    folder_path = f'{settings.MEDIA_ROOT}{get_folder_path(ss_no)}'
    os.makedirs(folder_path, exist_ok=True)

    image_datas = get_image_datas(folder_path)
    context = {
        'ss_uuid': ss_uuid,
        'ss_no': ss_no,
        'ss_user': ss_user,
        'image_datas': image_datas
    }
    return render(request, 'imglist.html', context)


def imgupload(request):
    if request.GET:
        req = request.GET
        ss_no = req.get('ss_no')
        ss_uuid = req.get('ss_uuid')
        ss_user = req.get('ss_user')

        context = {
            'ss_uuid': ss_uuid,
            'ss_no': ss_no,
            'ss_user': ss_user
        }
        return render(request, 'imgupload.html', context)

    if request.POST:
        req = request.POST
        ss_no = req.get('ss_no')
        ss_uuid = req.get('ss_uuid')
        ss_user = req.get('ss_user')
        context = {
            'ss_uuid': ss_uuid,
            'ss_no': ss_no,
            'ss_user': ss_user,
        }

        files = request.FILES.getlist('file')
        files = is_valid_image(files)[:40]

        try:
            for file in files:
                img_io = trans_image(file, ss_user)

                file_path = get_folder_path(ss_no) + ss_no + '.jpg'

                fs = FileSystemStorage()
                fs.save(file_path[1:], img_io)

            context['status'] = 1
            context['message'] = f"총 {len(files)}장의 사진을 등록하였습니다."
        except:
            context['status'] = 0
            context['message'] = f"서버 오류로 실패하였습니다. 관리자에게 문의바랍니다."

        return render(request, 'upload_status.html', context)
