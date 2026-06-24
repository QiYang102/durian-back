import unicodedata
from hashids import Hashids
from django.utils.http import urlquote
from django.conf import settings
import os
import shutil
import pytz
from decimal import Decimal

from django.apps import apps
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import exception_handler as drf_exception_handler
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


def get_hashids(prefix=None):
    salt = '{0}-{1}'.format(prefix or '', settings.SECRET_KEY)
    return Hashids(salt=salt, alphabet='ABCDEFGHJKLMNPRSTVWXYZ23456789', min_length=5)


def hashid_encode(prefix, classname, *values):
    hashids = get_hashids(classname)
    return '{0}{1}'.format(prefix, hashids.encode(*values))


def hashid_decode(hashid):
    prefix = hashid[0:3]
    hashids = get_hashids(prefix)
    return hashids.decode(hashid[3:])


def rfc5987_content_disposition(file_name):
    ascii_name = unicodedata.normalize(
        'NFKD', file_name).encode('ascii', 'ignore').decode()
    header = 'attachment; filename="{}"'.format(ascii_name)
    if ascii_name != file_name:
        quoted_name = urlquote(file_name)
        header += '; filename*=UTF-8\'\'{}'.format(quoted_name)

    return header


def remove_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def to_localtime(dt, tz='Asia/Kuala_Lumpur'):
    if not dt:
        return None

    try:
        tz = pytz.timezone(tz)
    except:
        tz = pytz.timezone('Asia/Kuala_Lumpur')

    dt = dt.astimezone(tz)
    return dt


def excel_localtime(dt, tz='Asia/Kuala_Lumpur'):
    if dt:
        return to_localtime(dt, tz).strftime(r'%Y-%m-%d %I:%M:%S %p')

    return ''


def hostname_from_request(request):
    # split on `:` to remove port
    return request.get_host().split(':')[0].lower()


def mask(text, length=None):
    length = length or 6

    return text[:length].ljust(len(text), '*') if text else ''


def exception_handler(exc, context):
    """Handle Django ValidationError as an accepted exception
    Must be set in settings:
    >>> REST_FRAMEWORK = {
    ...     # ...
    ...     'EXCEPTION_HANDLER': 'ecom.utility.exception_handler',
    ...     # ...
    ... }
    For the parameters, see ``exception_handler``
    """

    if hasattr(exc, 'message_dict'):
        exc = DRFValidationError(detail=exc.message_dict)
    elif hasattr(exc, 'message'):
        exc = DRFValidationError(detail=exc.message)

    return drf_exception_handler(exc, context)


def csv_int(row, index):
    return int(row[index].strip().replace(',', '')) if row[index] else 0


def csv_float(row, index):
    return float(row[index].strip().replace(',', '')) if row[index] else 0


def csv_text(row, index):
    if index < len(row):
        return row[index].strip() if row[index] else ''

    return ''


def csv_decimal(row, index):
    return Decimal(row[index].strip().replace(',', '')) if row[index] else Decimal(0)


def round_percentage(percentages: [float]) -> [float]:
    total_percent = 0
    result = []

    for item in percentages:
        cur_percent = int(item * 10000)
        result.append(cur_percent)
        total_percent += cur_percent

    for index in range(abs(10000 - total_percent)):
        if total_percent < 10000:
            result[index] += 1

        if total_percent > 10000:
            result[-index] -= 1

    return [item / 100 for item in result]


def text_to_boolean(text: str) -> bool:
    return text and text.lower() in ['y', 'yes', 'true', 'active']


def tenant_from_request(request):
    Tenant = apps.get_model('core', 'Tenant')

    return Tenant.objects.first()

def resize_image(file, max_size_kb=300, max_dimension_pixel=600):
    file.seek(0, os.SEEK_END)
    size = (file.tell() >> 10)
    file.seek(0, os.SEEK_SET)

    if size > max_size_kb:
        image = Image.open(file)
        image = image.convert('RGB')

        # rotate the image based on exif orientation info,
        # especially photo taken from phone camera
        exif_orientation_tag = 0x0112
        exif = image.getexif()
        if exif_orientation_tag in exif:
            orientation = exif[exif_orientation_tag]
            if orientation == 3:
                image = image.transpose(Image.ROTATE_180)
            elif orientation == 6:
                image = image.transpose(Image.ROTATE_270)
            elif orientation == 8:
                image = image.transpose(Image.ROTATE_90)

        if max(image.size) > max_dimension_pixel:
            ratio = float(max_dimension_pixel / max(image.size))
            new_size = tuple([int(x * ratio) for x in image.size])
            image.thumbnail(new_size, Image.Resampling.LANCZOS)

        compress_io = BytesIO()
        image.save(compress_io, format='JPEG', quality=80)

        return InMemoryUploadedFile(compress_io, None, file.name, 'image/jpeg', compress_io.tell(), None)

    return file

def has_key_in_list(dictionary, key_list):
    """
    Check if any key in dictionary found in the key_list
    """
    return any(key in key_list for key in dictionary)