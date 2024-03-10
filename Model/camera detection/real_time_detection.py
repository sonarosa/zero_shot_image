# -*- coding: utf-8 -*-
import cv2
import os
import time
from IPython.display import Image, display
from autogluon.multimodal import MultiModalPredictor
from IPython.display import display, Javascript
from google.colab.output import eval_js
from base64 import b64decode

def capture_frames(video_path, output_folder='frames'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    vidObj = cv2.VideoCapture(video_path)
    count = 0
    frame_interval = 1
    fps = int(vidObj.get(cv2.CAP_PROP_FPS))
    frame_time = 1 / fps

    frame_urls = []

    while True:
        success, image = vidObj.read()

        if not success:
            break

        current_time = vidObj.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        if current_time >= count * frame_interval:
            frame_name = os.path.join(output_folder, "frame%d.jpg" % count)
            cv2.imwrite(frame_name, image)
            frame_urls.append(frame_name)
            count += 1

    vidObj.release()

    return frame_urls

def take_photo(filename='photo.jpg', quality=0.8):
    js = Javascript('''
        async function takePhoto(quality) {
          const div = document.createElement('div');
          const capture = document.createElement('button');
          capture.textContent = 'Capture';
          div.appendChild(capture);

          const video = document.createElement('video');
          video.style.display = 'block';
          const stream = await navigator.mediaDevices.getUserMedia({video: true});

          document.body.appendChild(div);
          div.appendChild(video);
          video.srcObject = stream;
          await video.play();

          // Resize the output to fit the video element.
          google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);

          // Wait for Capture to be clicked.
          await new Promise((resolve) => capture.onclick = resolve);

          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d').drawImage(video, 0, 0);
          stream.getVideoTracks()[0].stop();
          div.remove();
          return canvas.toDataURL('image/jpeg', quality);
        }
        ''')
    display(js)
    data = eval_js('takePhoto({})'.format(quality))
    binary = b64decode(data.split(',')[1])
    with open(filename, 'wb') as f:
        f.write(binary)
    return filename

if __name__ == '__main__':
    video_path = "t_w023_converted.avi"
    output_folder = "frames"
    class_labels = ['Violence', 'Normal']
    predictor = MultiModalPredictor(problem_type="zero_shot_image_classification")

    violence_timestamps = []

    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            filename = take_photo()
            print(f'Image captured at {current_time}. Analyzing...')
            pil_img = Image(filename=filename)
            display(pil_img)

            prob = predictor.predict_proba({"image": [filename]}, {"text": class_labels})
            violence_prob = prob[0][0]

            if violence_prob > 0.5:
                print(f"Violence detected at {current_time}!")
                violence_timestamps.append(current_time)
            else:
                print(f"No violence detected at {current_time}.")

            time.sleep(1)  # Adjust this delay based on your requirements

    except KeyboardInterrupt:
        if len(violence_timestamps) > 0:
            print("Violence detected at the following timestamps:")
            for timestamp in violence_timestamps:
                print(timestamp)
        else:
            print("No violence detected.")
