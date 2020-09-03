"""This module defines my_images endpoints.
"""

import datetime
import json
import os
from flask import Blueprint
from flask import render_template
from flask import request
from google.cloud import datastore
from google.cloud import storage
from google.cloud import vision


my_images = Blueprint('my_images', __name__)
datastore_client = datastore.Client()
storage_client = storage.Client()

DATASTORE_KIND_NAME = 'image'
datastore_bucket_name = 'gti-gcp10-whatizit.google.com.a.appspot.com'
UPLOAD_FOLDER = '/tmp'
USER_HEADER = 'X-Appengine-User-Nickname'


@my_images.route('/my_images')
def get_my_images():
  """Endpoint to list all exisiting images."""
  user_name = request.headers.get(USER_HEADER, 'gcp-10')

  query = datastore_client.query(kind=DATASTORE_KIND_NAME)
  query.order = ['-upload_ts']
  my_images_itrs = query.fetch(limit=100)
  my_images_list = []

  for my_image in my_images_itrs:
    upload_ts = my_image['upload_ts'] - datetime.timedelta(hours=7, minutes=0)
    my_image['upload_ts_str'] = upload_ts.strftime('%Y-%m-%d (%H:%M:%S)')
    my_images_list.append(my_image)

  return render_template(
      'my_images.html', user_name=user_name, my_images=my_images_list)


@my_images.route('/my_images/delete/<image_id>', methods=['POST'])
def delete_image(image_id):
  image_id = int(image_id)
  image_key = datastore_client.key(DATASTORE_KIND_NAME, image_id)
  datastore_client.delete(image_key)

  return (json.dumps({'success': True}), 200, {
      'ContentType': 'application/json'
  })


@my_images.route('/my_images/post', methods=['POST'])
def post_new_image():
  """Endpoint to upload a new image."""
  if 'file' not in request.files:
    return (json.dumps({
        'success': False,
        'reason': 'empty file'
    }), 400, {
        'ContentType': 'application/json'
    })
  uploaded_file = request.files['file']
  if not uploaded_file.filename:
    return (json.dumps({
        'success': False,
        'reason': 'empty file'
    }), 400, {
        'ContentType': 'application/json'
    })

  # Save new entity to datastore
  owner = request.headers.get(USER_HEADER, 'gcp-10')
  content = uploaded_file.read()
  uploaded_file.seek(0)
  image = vision.types.Image(content=content)
  response = vision_client.label_detection(image=image)
  labels = response.label_annotations
  tags = []
  for label in labels:
    tags.append(label.description)
  new_image_key = datastore_client.key(DATASTORE_KIND_NAME)
  new_image = datastore.Entity(key=new_image_key)
  new_image['upload_ts'] = datetime.now()
  new_image['owner'] = owner
  new_image['tags'] = tags
  
  datastore_client.put(new_image)

  # Save file locally
  new_image_id = str(new_image.id)
  temp_file_name = '{0}.jpg'.format(new_image_id)
  temp_file_path = os.path.join(UPLOAD_FOLDER, temp_file_name)
  uploaded_file.save(temp_file_path)

  # Upload to cloud storage
  bucket = storage_client.bucket(datastore_bucket_name)
  blob = bucket.blob(temp_file_name)
  blob.upload_from_filename(temp_file_path)

  return (json.dumps({'success': True}), 200, {
      'ContentType': 'application/json'
  })
