import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt
import pytesseract
import re
import requests
import json

# --------------------------
# 1. Read and preprocess image
# --------------------------
img = cv.imread("/kaggle/input/reciept/reciept.jpg")
original = img.copy()
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# Edge detection and find contours for receipt
edges = cv.Canny(gray, 50, 150, apertureSize=3)
kernel = np.ones((5,5), np.uint8)
edges = cv.dilate(edges, kernel, iterations=1)
contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

receipt_contour = None
max_area = 0
for cnt in contours:
    area = cv.contourArea(cnt)
    if area > max_area and area > 1000:
        peri = cv.arcLength(cnt, True)
        approx = cv.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            max_area = area
            receipt_contour = approx

# Perspective transform if receipt detected
if receipt_contour is not None:
    pts = receipt_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")
    M = cv.getPerspectiveTransform(rect, dst)
    warped = cv.warpPerspective(original, M, (maxWidth, maxHeight))
    gray = cv.cvtColor(warped, cv.COLOR_BGR2GRAY)

# --------------------------
# 2. Enhanced preprocessing
# --------------------------
gray = cv.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv.INTER_CUBIC)
gray = cv.fastNlMeansDenoising(gray, None, 10, 7, 21)
kernel_sharp = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
gray = cv.filter2D(gray, -1, kernel_sharp)
thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv.THRESH_BINARY, 15, 8)
kernel = np.ones((2,2), np.uint8)
thresh = cv.morphologyEx(thresh, cv.MORPH_CLOSE, kernel)
thresh = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel)

# --------------------------
# 3. OCR
# --------------------------
custom_config = r'--oem 3 --psm 6'
text = pytesseract.image_to_string(thresh, config=custom_config)
print("DETECTED RECEIPT TEXT:")
print(text)

# --------------------------
# 4. Basic parsing
# --------------------------
# Extract total amount
total_match = re.search(r'Total\s*[:]?[\s$]*([0-9]+[.,]?[0-9]*)', text, re.IGNORECASE)
total_amount = float(total_match.group(1).replace(',', '.')) if total_match else 0.0

# Extract date (simple pattern: dd/mm/yyyy or yyyy-mm-dd)
date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})', text)
receipt_date = date_match.group(1) if date_match else None

# Extract store name (take first line)
store_name = text.split('\n')[0].strip() if text else "Unknown Store"

# Extract items: very basic regex, assumes "item_name price"
items = []
for line in text.split('\n')[1:]:
    line = line.strip()
    match = re.match(r'(.+?)\s+([0-9]+[.,]?[0-9]*)$', line)
    if match:
        item_name = match.group(1).strip()
        price = float(match.group(2).replace(',', '.'))
        items.append({"name": item_name, "quantity": 1, "unit_price": price})

# --------------------------
# 5. Send to Spring Boot backend
# --------------------------
data = {
    "storeName": store_name,
    "receiptDate": receipt_date,
    "totalAmount": total_amount,
    "items": items
}

# Example: your Spring Boot endpoint

url = "http://localhost:8081/api/receipts"

headers = {'Content-Type': 'application/json'}
response = requests.post(url, data=json.dumps(data), headers=headers)

print("Response from backend:", response.status_code, response.text)
