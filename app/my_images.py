from flask import Blueprint, render_template

my_images = Blueprint('my_images', __name__)


@my_images.route('/my_images')
def get_my_images():
    return render_template("my_images.html")
