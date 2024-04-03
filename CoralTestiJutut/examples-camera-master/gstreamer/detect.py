# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo which runs object detection on camera frames using GStreamer.

Run default object detection:
python3 detect.py

Choose different camera and input encoding
python3 detect.py --videosrc /dev/video1 --videofmt jpeg

TEST_DATA=../all_models
Run face detection model:
python3 detect.py \
  --model ${TEST_DATA}/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite

Run coco model:
python3 detect.py \
  --model ${TEST_DATA}/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ${TEST_DATA}/coco_labels.txt
"""
##Tunnistaa kuvasta objectin, laskee onko objecti enemman vasemmalla vai oikealla ja kytkee sen puolen ledin on.

import argparse
import gstreamer
import os
import time

from periphery import GPIO ##tuodaan periphery kirjastosta GPIO.

from common import avg_fps_counter, SVG
from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference

##Maaritetaan ledien pinnit
led = GPIO("/dev/gpiochip2", 13, "out")  #pin 37 led outputtina
led2 = GPIO("/dev/gpiochip4", 13, "out") #pin 36 led2 outputtina. 

def generate_svg(src_size, inference_box, objs, labels, text_lines): ##generate_svg lisää tunnistetun kohteen ympärille punaisen laatikon sekä tekstin, mikä kohde on ja millä varmuudella.
    svg = SVG(src_size)
    src_w, src_h = src_size
    box_x, box_y, box_w, box_h = inference_box
    
    scale_x, scale_y = src_w / box_w, src_h / box_h

    for y, line in enumerate(text_lines, start=1):
        svg.add_text(10, y * 20, line, 20)
    for obj in objs:
        bbox = obj.bbox
        if not bbox.valid:
            continue
        # Absolute coordinates, input tensor space.
        x, y = bbox.xmin, bbox.ymin
        w, h = bbox.width, bbox.height
        
        # Subtract boxing offset.
        x, y = x - box_x, y - box_y
        # Scale to source coordinate space.
        x, y, w, h = x * scale_x, y * scale_y, w * scale_x, h * scale_y
        percent = int(100 * obj.score) ##Alkuperaista koodia, tassa kohteen "treshold" pisteet kerrotaan 100 jolloin saadaan prosenttiluku
        percent2= int(100*obj.score) ##vastaava kun ylla, mutta tata kaytetaan omassa koodissa
        label = '{}% {}'.format(percent, labels.get(obj.id, obj.id)) ##Tunnistetulle kohteelle luodaan "label" teksti. Haetaan labels tiedostosta obj.id arvolla
        svg.add_text(x, y - 5, label, 20)##label teksti lisataan kuvaan
        svg.add_rect(x, y, w, h, 'red', 2) #Asetetaa neliö tunnistetun kohteen ympärille.
        
        ##Tassa esimerkissa tarkistetaan obj.id, ja objektin "varmuus". 
        ##Jos videosta tunnistetaan kohde riittavalla varmuudella, ohjataan ledeja. 
        midle=w/2+x ##Lasketaan missa kohtaa kuvaa, tunnistetun kohteen keskikohta on.
        if obj.id==43 and percent2>=50: #jos obj.id=43 eli "bottle", yli 50% varmuudella,
          print(src_w,midle)##Debug viesti, videon leveys seka tunnistetun kohteen keskikohta.
          print("X koordinaatti:",x, " box leveys:",w)##Debug viesti
          if midle<320:##Jos kohteen keskikohta on alle 320= kohda kuvassa vasemmalla, sytytetaan led, muuten led2.
            led.write(True)
          else:
            led2.write(True)
          time.sleep(2) ##Tama on vain hidastamassa koodia helpomman testailun takia.
          led.write(False) #sammutetaan molemmat ledit.
          led2.write(False)
          time.sleep(0.5)
          
    return svg.finish()

def main():
    default_model_dir = '../all_models' #Kansio josta malli ladataan
    default_model = 'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite' #käytettava malli
    default_labels = 'coco_labels.txt' #label tiedosto, mallista palautetaan pelkkä indeksi, label tiedostossa indeksille annetaan selitys esim koira
    ##Default argumentit milla ohjelma ajetaan. Nama voi myos antaa ohjelmaa kaynnistaessa.
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    parser.add_argument('--top_k', type=int, default=3, ##maaritetaan montako "parasta" tulosta naytetaan, eli ne x objektia jotka on suurimmalla varmuudella tunnistettu
                        help='number of categories with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.1, ##Minimi treshold eli "varmuus" jolla objekti on tunnistettu. 0.1 = 10% ja 1.0=100%
                        help='classifier score threshold')
    parser.add_argument('--videosrc', help='Which video source to use. ', ##käytettävä videolähde.
                        default='/dev/video1') 
    parser.add_argument('--videofmt', help='Input video format.', 
                        default='raw',
                        choices=['raw', 'h264', 'jpeg'])
    args = parser.parse_args()

    print('Loading {} with {} labels.'.format(args.model, args.labels))
    interpreter = make_interpreter(args.model)
    interpreter.allocate_tensors()
    labels = read_label_file(args.labels)
    inference_size = input_size(interpreter)

    # Average fps over last 30 frames.
    fps_counter = avg_fps_counter(30)

    ##Kaytannossa ohjelma pyorittaa tata osiota uudestaan ja uudestaa ja kutsuu "generate_svg" ohjelmaa joka kierroksella kaikkien tunnistettujen kohteiden erikseen.
    def user_callback(input_tensor, src_size, inference_box):
      nonlocal fps_counter
      start_time = time.monotonic()
      run_inference(interpreter, input_tensor)
      # For larger input image sizes, use the edgetpu.classification.engine for better performance
      objs = get_objects(interpreter, args.threshold)[:args.top_k]
      end_time = time.monotonic()
      text_lines = [
          'Inference: {:.2f} ms'.format((end_time - start_time) * 1000),
          'FPS: {} fps'.format(round(next(fps_counter))),
      ]
      print(' '.join(text_lines))
      return generate_svg(src_size, inference_box, objs, labels, text_lines)

    result = gstreamer.run_pipeline(user_callback,
                                    src_size=(640, 480),
                                    appsink_size=inference_size,
                                    videosrc=args.videosrc,
                                    videofmt=args.videofmt)

if __name__ == '__main__':
    main()
