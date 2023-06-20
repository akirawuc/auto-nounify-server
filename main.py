from google.cloud import vision
import io
from flask_cors import CORS
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
import os
from math import atan2, degrees
from PIL import Image, ImageDraw

app = Flask(__name__)
CORS(app)

def detect_face(image_path):
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
    print(img.size)

    # Load glasses, which is in svg
    glasses = Image.open('./glasses-red.png')

    for face in faces:
        # Calculate position and size of glasses
        left_eye = face.landmarks[0]
        right_eye = face.landmarks[1]
        print(left_eye)


        scaling_factor = 2.7  # Increase this as needed
        width = int((right_eye.position.x - left_eye.position.x) * scaling_factor)
        height = int(width * glasses.size[1] / glasses.size[0])  # Maintain the aspect ratio
        size = (width, height)

        midpoint = ((left_eye.position.x + right_eye.position.x) / 2,
                    (left_eye.position.y + right_eye.position.y) / 2)

        # Adjust the position to account for the temple of the glasses
        temple_factor = 18 / 140  # As provided by you
        shift = int(temple_factor * width)

        # Correct the position to align the glasses properly
        pos = (int(midpoint[0] - size[0]/2 - shift), int(midpoint[1] - 1.4*(size[1]/2)))

        print(f'adding the glasses at {pos} with size {size}')
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
        # draw = ImageDraw.Draw(img)
        # draw.line([(left_eye.position.x, left_eye.position.y), (right_eye.position.x, right_eye.position.y)], fill="blue", width=3)
        # img.show()

    return img


app.config['UPLOAD_FOLDER'] = './uploads/'

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        faces = detect_face('./uploads/' + filename)
        img = overlay_glasses('./uploads/' + filename, faces)
        img.show()
        img.save('./uploads/face_with_glasses_' + filename)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='JPEG')
        byte_arr =  byte_arr.getvalue()
        return send_file(io.BytesIO(byte_arr), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(port=5000)
