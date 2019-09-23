import time
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
from picamera import PiCamera
from picamera.array import PiRGBArray
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from imutils import contours
from skimage import measure
import numpy as np
import imutils
import cv2


min_pixels_for_masking = 20         # Min. number of connected bright pixels to get a mask.
min_bright_pixel_value = 200        # Pixel intensity > this will be considered bright.

# GPIO pin numbers (BCM mode, board mode shown in comments).
SCLK = 11 # 23
DIN = 10 # 19
DC = 23 # 16
RST = 24 # 18
CS = 8 # 24

SPI_PORT = 0
SPI_DEVICE = 0

def clear_lcd(disp, image):
	draw.rectangle((0,0,LCD.LCDWIDTH,LCD.LCDHEIGHT), outline=255, fill=255)
	disp.image(image)
	disp.display()


def draw_points(disp, image, data, old_data):
	for r in range(len(data)):
		for c in range(len(data[r])):
			# Skip updates if data hasn't changed.
			if data[r][c] == old_data[r][c]:
				continue

			if data[r][c] == 255:
				draw.point((c, r), fill=0)
			elif data[r][c] == 0:
				draw.point((c, r), fill=255)

	disp.image(image)
	disp.display()


# LCD initialization.
disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
# disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)
disp.begin(contrast=60)
disp.clear()
disp.display()
lcd_image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
draw = ImageDraw.Draw(lcd_image)

camera = PiCamera(resolution=(96,48))
cap = PiRGBArray(camera)

old_mask = np.zeros((48, 84), dtype="uint8")

clear_lcd(disp, lcd_image)

while True:
	camera.capture(cap, format="bgr")
	img_in = cap.array

	img_in = img_in[0:48, 6:90] # Crop.
	cv2.imwrite("out.jpg", img_in)
	image = cv2.imread('out.jpg')

	cap.truncate(0)

	# Convert image to grayscale and apply blur.
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
			print("OK")

	draw_points(disp, lcd_image, mask, old_mask)
	old_mask = mask
