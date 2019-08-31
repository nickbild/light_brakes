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
import imutils
import cv2


# Size of image to capture (should match size of LCD display).
img_width = 84
img_height = 48

min_pixels_for_masking = 20         # Min. number of connected bright pixels to get a mask.
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


def gstreamer_pipeline (capture_width=1050, capture_height=600, display_width=img_width, display_height=img_height, framerate=21, flip_method=2) :
    return ('nvarguscamerasrc ! '
    'video/x-raw(memory:NVMM), '
    'width=(int)%d, height=(int)%d, '
    'format=(string)NV12, framerate=(fraction)%d/1 ! '
    'nvvidconv flip-method=%d ! '
    'video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! '
    'videoconvert ! '
    'video/x-raw, format=(string)BGR ! appsink'  % (capture_width,capture_height,framerate,flip_method,display_width,display_height))


# LCD initialization.
# disp = LCD.PCD8544(DC, RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=4000000))
disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)
disp.begin(contrast=60)
disp.clear()
disp.display()
lcd_image = Image.new('1', (LCD.LCDWIDTH, LCD.LCDHEIGHT))
draw = ImageDraw.Draw(lcd_image)

cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=2), cv2.CAP_GSTREAMER)
old_mask = np.zeros((LCD.LCDHEIGHT, LCD.LCDWIDTH), dtype="uint8")

clear_lcd(disp, lcd_image)

if cap.isOpened():
	while True:
		ret_val, img_in = cap.read()
		cv2.imwrite("out.jpg", img_in)
		image = cv2.imread('out.jpg')

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

		draw_points(disp, lcd_image, mask, old_mask)
		old_mask = mask

else:
	print('Unable to open camera.')
