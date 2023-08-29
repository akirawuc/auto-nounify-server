from google.cloud import vision
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore
from flask import abort
import functions_framework
import io
from flask_cors import CORS
from flask import Flask, request, send_from_directory, make_response
from werkzeug.utils import secure_filename
import os
from math import atan2, degrees
from PIL import Image, ImageDraw


def detect_face(image_path):
    print(image_path)
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.face_detection(image=image)
    faces = response.face_annotations

    return faces

def calculate_angle(left_eye, right_eye):
    dx = right_eye.position.x - left_eye.position.x
    dy = right_eye.position.y - left_eye.position.y
    angle = degrees(atan2(dy, dx))
    return angle

def overlay_glasses(image_path, faces):
    # Load image
    img = Image.open(image_path)
    print(image_path)
    print(img.size)

    # Load glasses, which is in svg
    glasses = Image.open('./glasses-red.png')

    for face in faces:
        # Calculate position and size of glasses
        left_eye = face.landmarks[0]
        right_eye = face.landmarks[1]
        nose_tip = face.landmarks[7]
        print(left_eye)


        scaling_factor = 2.7  # Increase this as needed to make the noggle bigger or smaller
        width = abs(int((right_eye.position.x - left_eye.position.x) * scaling_factor))
        height = abs(int(width * glasses.size[1] / glasses.size[0]))  # Maintain the aspect ratio
        size = (width, height)

        midpoint = ((left_eye.position.x + right_eye.position.x) / 2,
                    (left_eye.position.y + right_eye.position.y) / 2)

        # Adjust the position to account for the temple of the glasses
        temple_factor = 18 / 140  # As provided by you
        shift = int(temple_factor * width)

        # Correct the position to align the glasses properly
        pos = (int(midpoint[0] - size[0]/2 - shift), int(nose_tip.position.y - size[1]))

        # Calculate the angle of rotation
        angle = calculate_angle(left_eye, right_eye)

        # Resize glasses
        resized_glasses = glasses.resize(size, Image.ANTIALIAS)

        # Rotate glasses according to the angle
        rotated_glasses = resized_glasses.rotate(-angle, expand=True)

        mask = rotated_glasses.convert('RGBA').split()[3]

        # Check if glasses cover both eyes
        glasses_start_x = pos[0]
        glasses_end_x = pos[0] + rotated_glasses.size[0]

        if glasses_start_x <= left_eye.position.x and glasses_end_x >= right_eye.position.x:
            print("Glasses cover both eyes.")
        else:
            print("Glasses do not cover both eyes. Adjust the size or position.")

        # Overlay glasses onto image
        img.paste(rotated_glasses, pos, mask=mask)
    return img


@functions_framework.http
def add_noggles(request):
    db = firestore.Client()
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type,  x-wallet-address',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)


    fields = {}
    data = request.form.to_dict()
    for field in data:
        fields[field] = data[field]

    files = request.files.to_dict()
    for filename, file in files.items():
        filename = file.filename
        file.save(os.path.join('/tmp/', filename))
        faces = detect_face('/tmp/' + filename)
        img = overlay_glasses('/tmp/' + filename, faces)
        img.save('/tmp/face_with_glasses_' + filename)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format=img.format)
        byte_arr.seek(0)
        if img.format == 'PNG':
            mimetype = 'image/png'
        elif img.format == 'JPEG':
            mimetype = 'image/jpeg'
        else:
            mimetype = 'image/' + img.format.lower()
        print('returning file')
        response = make_response(send_from_directory('/tmp/', 'face_with_glasses_' + filename, as_attachment=True, mimetype=mimetype))
        response.headers.set('Access-Control-Allow-Origin', '*')
        response.headers.set('Access-Control-Allow-Methods', 'GET, POST')
        return response
