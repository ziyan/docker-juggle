import tarfile
import subprocess

import logging
log = logging.getLogger(__name__)

def get_image_history(image):
    output = subprocess.check_output(['docker', 'history', '-q', '--no-trunc', image])
    images = filter(None, output.split())
    assert len(images) > 0
    return images

def save_image(image):
    process = subprocess.Popen(['docker', 'save', image], stdout=subprocess.PIPE)
    return tarfile.open(fileobj=process.stdout, mode='r|')
