from flask import Blueprint, render_template
from google.cloud import datastore
from datetime import datetime

import json

my_images = Blueprint('my_images', __name__)
datastore_client = datastore.Client()


@my_images.route('/my_images')
def get_my_images():
    return render_template("my_images.html")


@my_images.route('/my_images/post', methods=['POST'])
def post_new_image():
    owner = 'gcp-10'
    kind_name = 'image'
    new_image_key = datastore_client.key(kind_name)
    new_image = datastore.Entity(key=new_image_key)
    new_image['upload_ts'] = datetime.now()
    new_image['owner'] = owner
    new_image['status'] = 'pending'
    new_image['tags'] = ''

    datastore_client.put(new_image)

    return (
        json.dumps({'success': True}),
        200,
        {'ContentType': 'application/json'})
