from django.test import TestCase
from PIL import Image
from torchvision import transforms
import torch
from tubp.core.utils.prediction_model import PredictionModel
from django.conf import settings
import os


class ModelPredictionTest(TestCase):

    def test_load_image(self):
        pass

    def test_predict_image_type(self):
        im_dir = os.path.join(settings.BASE_DIR, "tubp/apps/dpu/assets/models/test_image.png")
        image = Image.open(im_dir)
        image = transforms.ToTensor()(image)
        model = PredictionModel()
        model.load_state_dict(torch.load(settings.PREDICTION_MODEL_PATH, map_location=torch.device('cpu')))
        assert list(model.forward(image).view(18, -1).argmax().numpy().reshape(-1,))[0] == 15
