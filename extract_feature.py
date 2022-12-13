# SJTU EE208

import time

import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
from torchvision.datasets.folder import default_loader
import PIL
import os


print('Load model: ResNet50')
model = torch.hub.load('pytorch/vision', 'resnet50', pretrained=True)
#model = torchvision.models.resnet50(pretrained=False)

normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225])
trans = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    normalize,
])

def extract(img):
    print('Prepare image data!')
    test_image = default_loader(img)
    input_image = trans(test_image)
    input_image = torch.unsqueeze(input_image, 0)


    def features(x):
        x = model.conv1(x)
        x = model.bn1(x)
        x = model.relu(x)
        x = model.maxpool(x)
        x = model.layer1(x)
        x = model.layer2(x)
        x = model.layer3(x)
        x = model.layer4(x)
        x = model.avgpool(x)

        return x


    print('Extract features!')
    start = time.time()
    image_feature = features(input_image)
    image_feature = image_feature.detach()
    image_feature = torch.reshape(image_feature, ((2048, )))

    print('Time for extracting features: {:.2f}'.format(time.time() - start))
    return np.array(image_feature)

target_feature = extract('panda.png')
print(target_feature.shape)

def similarity(feature1, feature2):
    feature1 = np.array(feature1)
    feature2 = np.array(feature2)
    result = (feature1 - feature2)**2
    result = np.sum(result, axis=1)
    result = np.sqrt(result)
    return result

test_feature = []
test_name = []
for root, dir, files in os.walk('train_data', topdown=False):
    for name in files:
        try:
            img_feature = extract(os.path.join(root, name))
            test_feature.append(img_feature)
            test_name.append(os.path.join(root, name))
        except:
            PIL.UnidentifiedImageError

test_feature = np.array(test_feature)
test_similarity = similarity(target_feature, test_feature)
match_position = np.array(np.where(test_similarity < 2))[0]

match_result = np.array([[test_similarity[i], test_name[i]] for i in match_position])
match_result = match_result[np.lexsort(match_result[:,::-1].T)]

times = 0
for i in match_result:
    print(i[1], "        ", i[0])
    times += 1
    if (times == 10):
        break

# print(len(match_position))

# print('Save features!')
# np.save('features.npy', image_feature)
