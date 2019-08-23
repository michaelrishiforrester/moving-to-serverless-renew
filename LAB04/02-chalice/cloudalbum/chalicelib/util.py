"""
    cloudalbum/chalicelib/util.py
    ~~~~~~~~~~~~~~~~~~~~~~~
    Utility functions

    :description: CloudAlbum is a fully featured sample application for 'Moving to AWS serverless' training course
    :copyright: © 2019 written by Dayoungle Jun, Sungshik Jou.
    :license: MIT, see LICENSE for more details.
"""

from datetime import datetime
from tzlocal import get_localzone
from chalicelib.config import conf
from PIL import Image
from io import BytesIO
# from jose import jwt
# from http.cookies import SimpleCookie
# import requests
import sys
import time
import os
import boto3
import cgi

current_milli_time = lambda: int(round(time.time() * 1000))


def get_parts(app):
    rfile = BytesIO(app.current_request.raw_body)
    content_type = app.current_request.headers['content-type']
    _, parameters = cgi.parse_header(content_type)
    parameters['boundary'] = parameters['boundary'].encode('utf-8')
    parsed = cgi.parse_multipart(rfile, parameters)
    return parsed


def get_password_reset_url():
    password_reset = "https://" \
                     "{0}/forgotPassword?response_type=code&client_id=" \
                     "{1}&redirect_uri=" \
                     "{2}" \
        .format(conf['COGNITO_DOMAIN'],
                conf['COGNITO_CLIENT_ID'],
                conf['BASE_URL'] + '/callback')

    return password_reset


# def verify(token, access_token=None):
#     """Verify a cognito JWT"""
#
#     ### load and cache cognito JSON Web Key (JWK)
#     # https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-with-identity-providers.html
#     JWKS_URL = "https://cognito-idp.{0}.amazonaws.com/{1}/.well-known/jwks.json". \
#         format(conf['AWS_REGION'], conf['COGNITO_POOL_ID'])
#
#     JWKS = requests.get(JWKS_URL).json()["keys"]
#
#     # get the key id from the header, locate it in the cognito keys
#     # and verify the key
#     header = jwt.get_unverified_header(token)
#     key = [k for k in JWKS if k["kid"] == header['kid']][0]
#     id_token = jwt.decode(token, key, audience=conf['COGNITO_CLIENT_ID'], access_token=access_token)
#
#     return id_token


def email_normalize(email):
    """
    Email normalization to get unique path.
    :param email: user email address.
    :return: normalized string value
    """
    return email.replace('@', '_at_').replace('.', '_dot_')


def save_s3(upload_file_stream, filename, email, app):
    prefix = "photos/{0}/".format(email_normalize(email))
    prefix_thumb = "photos/{0}/thumbnails/".format(email_normalize(email))

    key = "{0}{1}".format(prefix, filename)
    key_thumb = "{0}{1}".format(prefix_thumb, filename)

    s3_client = boto3.client('s3')
    original_bytes = upload_file_stream.stream.read()

    try:
        # Save original file
        s3_client.put_object(
            Bucket=conf['S3_PHOTO_BUCKET'],
            Key=key,
            Body=original_bytes,
            ContentType='image/jpeg',
            StorageClass='STANDARD'
        )

        app.logger.debug('s3://{0}/{1} uploaded'.format(conf['S3_PHOTO_BUCKET'], key))

        # Save thumbnail file
        upload_file_stream.stream.seek(0)
        s3_client.put_object(
            Bucket=conf['S3_PHOTO_BUCKET'],
            Key=key_thumb,
            # Body=resize_image(upload_file_stream, (conf['THUMBNAIL_WIDTH'], conf['THUMBNAIL_HEIGHT'])),
            Body=make_thumbnails_s3(upload_file_stream, app),
            ContentType='image/jpeg',
            StorageClass='STANDARD'
        )

        app.logger.debug('s3://{0}/{1} uploaded'.format(conf['S3_PHOTO_BUCKET'], key_thumb))
        upload_file_stream.stream.seek(0)

    except Exception as e:
        app.logger.error('Error occurred while saving file:%s', e)
        raise e

    return len(original_bytes)


def save_s3_chalice(bytes, filename, email, app):
    prefix = "photos/{0}/".format(email_normalize(email))
    prefix_thumb = "photos/{0}/thumbnails/".format(email_normalize(email))

    key = "{0}{1}".format(prefix, filename)
    key_thumb = "{0}{1}".format(prefix_thumb, filename)

    s3_client = boto3.client('s3')
    # original_bytes = upload_file_stream.read()

    try:
        temp_file = '/tmp/' + filename
        with open(temp_file, 'wb') as f:
            f.write(bytes)
            statinfo = os.stat(temp_file)
            app.log.debug(statinfo)

        s3_client.upload_file(temp_file, conf['S3_PHOTO_BUCKET'], key)
        thumb_path = make_thumbnails('/tmp', temp_file, app)
        app.log.debug('thumb_path for upload: {0}'.format(thumb_path))
        app.log.debug('prefix_thumb: {0}'.format(prefix_thumb))

        statinfo = os.stat(temp_file)
        app.log.debug(statinfo)

        s3_client.upload_file(thumb_path, conf['S3_PHOTO_BUCKET'], key_thumb)

    except Exception as e:
        app.log.error('Error occurred while saving file:%s', e)
        raise e

    return len(bytes)


def delete_s3(app, filename, current_user):
    prefix = "photos/{0}/".format(email_normalize(current_user.email))
    prefix_thumb = "photos/{0}/thumbnails/".format(email_normalize(current_user.email))

    key = "{0}{1}".format(prefix, filename)
    key_thumb = "{0}{1}".format(prefix_thumb, filename)

    s3_client = boto3.client('s3')
    try:
        s3_client.delete_object(Bucket=conf['S3_PHOTO_BUCKET'], Key=key)
        s3_client.delete_object(Bucket=conf['S3_PHOTO_BUCKET'], Key=key_thumb)
    except Exception as e:
        app.logger.error('Error occurred while deleting file:%s', e)
        raise e


def make_thumbnails(path, filename, app):
    """
    Generate thumbnail from original image file.
    :param path: target path
    :param filename: secure file name
    :param app: Falsk.application
    :return: None
    """
    thumb_full_path = '/tmp/thumbnail.jpg'

    try:
        im = Image.open(os.path.join(path, filename))
        im = im.convert('RGB')
        im.thumbnail((int(conf['THUMBNAIL_WIDTH']), int(conf['THUMBNAIL_HEIGHT']), Image.ANTIALIAS))
        im.save(thumb_full_path)

    except Exception as e:
        app.log.error("Thumbnails creation error : %s, %s", thumb_full_path, e)
        raise e

    return thumb_full_path


def make_thumbnails_s3(file_p, app):
    result_bytes_stream = BytesIO()

    try:
        im = Image.open(file_p)
        im = im.convert('RGB')
        im.thumbnail([int(conf['THUMBNAIL_WIDTH']), int(conf['THUMBNAIL_HEIGHT'])], Image.ANTIALIAS)
        im.save(result_bytes_stream, 'JPEG')
    except Exception as e:
        app.log.debug(e)

    return result_bytes_stream.getvalue()


def the_time_now():
    # utc_tz = pytz.timezone('UTC')
    local_tz = get_localzone()
    return datetime.now(local_tz)


def resize_image(file_p, size):
    """Resize an image to fit within the size, and save to the path directory"""
    dest_ratio = size[0] / float(size[1])
    try:
        image = Image.open(file_p)
    except IOError:
        print("Error: Unable to open image")
        return None

    source_ratio = image.size[0] / float(image.size[1])

    # the image is smaller than the destination on both axis
    # don't scale it
    if image.size < size:
        new_width, new_height = image.size
    elif dest_ratio > source_ratio:
        new_width = int(image.size[0] * size[1] / float(image.size[1]))
        new_height = size[1]
    else:
        new_width = size[0]
        new_height = int(image.size[1] * size[0] / float(image.size[0]))
    image = image.resize((new_width, new_height), resample=Image.LANCZOS)

    final_image = Image.new("RGB", size)
    topleft = (int((size[0] - new_width) / float(2)),
               int((size[1] - new_height) / float(2)))
    final_image.paste(image, topleft)
    bytes_stream = BytesIO()
    # final_image = final_image.convert('RGB')
    final_image.save(bytes_stream, 'JPEG')
    return bytes_stream.getvalue()


def presigned_url(filename, email, Thumbnail=True):
    prefix = "photos/{0}/".format(email_normalize(email))
    prefix_thumb = "photos/{0}/thumbnails/".format(email_normalize(email))

    try:
        s3_client = boto3.client('s3')

        if Thumbnail:
            key_thumb = "{0}{1}".format(prefix_thumb, filename)
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': conf['S3_PHOTO_BUCKET'],
                        'Key': key_thumb})
        else:
            key = "{0}{1}".format(prefix, filename)
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': conf['S3_PHOTO_BUCKET'],
                        'Key': key})

    except Exception as e:
        # flash('Error occurred! Please try again : {0}'.format(e))
        raise e

    return url
