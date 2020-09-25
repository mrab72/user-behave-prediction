from django.conf import settings
import os

PREDICTION_MODEL_PATH = os.path.join(settings.BASE_DIR, "tubp/apps/dpu/assets/models/the_model.pkl")
FLOWS_TEMP_DIR = "/mnt/temp_dir"
FLOWS_IMAGE_DIR = "mnt/temp_img_dir"
TRAFFIC_CLASSES = ['Database_png',
                   'VPN_png',
                   'Email_png',
                   'Chat_png',
                   'Media_png',
                   'RPC_png',
                   'Game_png',
                   'Streaming_png',
                   'Web_png',
                   'SoftwareUpdate_png',
                   'DataTransfer_png',
                   'SocialNetwork_png',
                   'Network_png',
                   'Download-FileTransfer-FileSharing_png',
                   'Collaborative_png',
                   'Cloud_png',
                   'VoIP_png',
                   'RemoteAccess_png'
                   ]
