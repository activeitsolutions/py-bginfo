import os
import sys
import psutil
import socket
import ctypes
from PIL import Image, ImageDraw, ImageFont
import struct
import time
import shutil

# Function to get the directory where the script is running
def get_script_directory():
    if getattr(sys, 'frozen', False):  # If the script is compiled to an EXE
        return os.path.dirname(sys.executable)
    else:  # If the script is run as a .py file
        return os.path.dirname(os.path.abspath(__file__))

# Function to get the system information
def get_system_info():
    computer_name = os.environ['COMPUTERNAME']
    user_domain = os.environ.get('USERDOMAIN', 'NoDomain')
    username = os.environ['USERNAME']
    full_username = f"{user_domain}\\{username}"

    drives = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        usage = psutil.disk_usage(partition.mountpoint)
        drive_info = {
            "device": partition.device,
            "mountpoint": partition.mountpoint,
            "used": f"{usage.used // (2**30)} GB",
            "free": f"{usage.free // (2**30)} GB",
            "total": f"{usage.total // (2**30)} GB",
        }
        drives.append(drive_info)
    
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    cidr = None

    for interface, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family == socket.AF_INET and address.address == ip_address:
                subnet_mask = address.netmask
                cidr = sum([bin(int(x)).count('1') for x in subnet_mask.split('.')])
                break
        if cidr:
            break

    ip_with_cidr = f"{ip_address}/{cidr}" if cidr else ip_address

    system_info = {
        "Hostname": hostname,
        "Computer Name\\User": full_username,
        "IP Address": ip_with_cidr,
        "Drives": drives
    }
    return system_info

# Function to get the current wallpaper (Windows)
def get_current_wallpaper():
    SPI_GETDESKWALLPAPER = 0x0073
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buffer, 0)
    return buffer.value

# Function to check if the current wallpaper is set to a color
def is_wallpaper_color():
    SPI_GETDESKWALLPAPER = 0x0073
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buffer, 0)
    return not bool(buffer.value)

# Function to create a gradient image if wallpaper is set to a color
def create_gradient_background(script_folder):
    width, height = 1920, 1080  # Adjust size as needed
    img = Image.new("RGB", (width, height), "#2982ff")
    draw = ImageDraw.Draw(img)

    start_color = (0x21, 0x6a, 0xd1)  # #216ad1
    end_color = (0x18, 0x3f, 0x76)    # #183f76

    for i in range(width):
        for j in range(height):
            ratio = (i + j) / (width + height)
            r = int(start_color[0] + ratio * (end_color[0] - start_color[0]))
            g = int(start_color[1] + ratio * (end_color[1] - start_color[1]))
            b = int(start_color[2])
            draw.point((i, j), fill=(r, g, b))

    gradient_path = os.path.join(script_folder, "original_wallpaper.jpg")
    img.save(gradient_path)
    return gradient_path

# Function to copy the current wallpaper to the script's folder
def copy_wallpaper_to_script_folder(wallpaper_path, script_folder):
    wallpaper_copy_path = os.path.join(script_folder, "original_wallpaper.jpg")
    shutil.copy2(wallpaper_path, wallpaper_copy_path)
    return wallpaper_copy_path

# Function to draw text with an outline
def draw_text_with_outline(draw, position, text, font, outline_color="black", fill_color="white", outline_width=1):
    x, y = position
    draw.text((x - outline_width, y - outline_width), text, font=font, fill=outline_color)
    draw.text((x + outline_width, y - outline_width), text, font=font, fill=outline_color)
    draw.text((x - outline_width, y + outline_width), text, font=font, fill=outline_color)
    draw.text((x + outline_width, y + outline_width), text, font=font, fill=outline_color)
    draw.text(position, text, font=font, fill=fill_color)

# Function to create an overlay image on the current wallpaper
def create_overlay_image(info, wallpaper_path, image_path="overlay.png"):
    img = Image.open(wallpaper_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arialbd.ttf", 16)

    width, height = img.size
    text_margin = 50
    y = height // 2
    x = width - text_margin

    lines = [
        "Managed by Active IT Solutions",
        "(951)742-8020",
        "support@activeitsolutions.com",
        " ",
        " ",
        f"Hostname: {info['Hostname']}",
        f"{info['Computer Name\\User']}",
        f"IP Address: {info['IP Address']}",
        " ",
        " ",
        ".:: Disk Drives ::."
    ]

    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw_text_with_outline(draw, (x - text_width, y), line, font)
        y += text_height + 5

    for drive in info['Drives']:
        drive_info = f"{drive['device']} ({drive['mountpoint']}) - Used: {drive['used']}, Free: {drive['free']}, Total: {drive['total']}"
        text_bbox = draw.textbbox((0, 0), drive_info, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw_text_with_outline(draw, (x - text_width, y), drive_info, font)
        y += text_height + 5

    img.save(image_path)

# Function to set the image as wallpaper (Windows)
def set_wallpaper(image_path):
    abs_path = os.path.abspath(image_path)
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    if not result:
        raise Exception(f"Failed to set wallpaper with error code: {ctypes.GetLastError()}")

# Main loop to update the wallpaper periodically
script_folder = get_script_directory()
current_wallpaper = get_current_wallpaper()

# Check if the current wallpaper is already overlay.png
if not current_wallpaper.endswith("overlay.png"):
    if is_wallpaper_color():
        wallpaper_copy_path = create_gradient_background(script_folder)
    else:
        wallpaper_copy_path = copy_wallpaper_to_script_folder(current_wallpaper, script_folder)
else:
    wallpaper_copy_path = os.path.join(script_folder, "original_wallpaper.jpg")

while True:
    system_info = get_system_info()
    create_overlay_image(system_info, wallpaper_copy_path)
    set_wallpaper("overlay.png")
    time.sleep(3600)  # Update every hour
