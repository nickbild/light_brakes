import time
import Jetson.GPIO as GPIO
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from imutils import contours
from skimage import measure
import numpy as np
import argparse
import imutils
import cv2


min_pixels_for_masking = 300        # Min. number of connected bright pixels to get a mask.
min_bright_pixel_value = 200        # Pixel intensity > this will be considered bright.

# GPIO pin numbers.
SCLK = 4
DIN = 17
DC = 23
RST = 24
CS = 8


def clear_lcd(disp, image):
	draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
	disp.image(image)
	disp.display()


def draw_point(disp, image):
	draw.point((10,10), fill=None)
	draw.point((20,20), fill=None)
	disp.image(image)
	disp.display()

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True)
args = vars(ap.parse_args())

# LCD initialization.
disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)
disp.begin(contrast=60)
disp.clear()
disp.display()
lcd_image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
draw = ImageDraw.Draw(lcd_image)

# Convert image to grayscale and apply blur.
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (11, 11), 0)

# Find bright regions with a threshold.
thresh = cv2.threshold(blurred, min_bright_pixel_value, 255, cv2.THRESH_BINARY)[1]

# Remove noise.
thresh = cv2.erode(thresh, None, iterations=2)
thresh = cv2.dilate(thresh, None, iterations=4)

# Connected components analysis.
labels = measure.label(thresh, neighbors=8, background=0)

# Loop through components.
mask = np.zeros(thresh.shape, dtype="uint8")
for label in np.unique(labels):
	# Ignore background.
	if label == 0:
		continue

	# Build mask for current label.
	labelMask = np.zeros(thresh.shape, dtype="uint8")
	labelMask[labels == label] = 255
	numPixels = cv2.countNonZero(labelMask)

	# If minimum size requirement met, add current label
    # mask to global mask.
	if numPixels > min_pixels_for_masking:
		mask = cv2.add(mask, labelMask)

# for r in range(len(mask)):
#     for c in range(len(mask[r])):
#         print(mask[r][c])

# cv2.imshow("Image", mask)
# cv2.waitKey(0)

clear_lcd(disp, lcd_image)
draw_point(disp, lcd_image)
