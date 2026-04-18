"""Generate a blog post using Anthropic Claude (or configured endpoint) and create a title image via Canva API or Pillow fallback.

Writes a Jekyll post to _posts/ and saves image to assets/images/blog/.
"""
import os
import sys
import argparse
import datetime
import json
import requests
from slugify import slugify
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont