import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn as nn
import torchvision.transforms as transforms
from typing import Optional, Callable

from src.noiseprint_creation.utilityRead import imread2f, jpeg_qtableinv

torch.set_printoptions(precision=8)


class AddBias(nn.Module):
    """A customized layer to add bias"""

    def __init__(self, num_features: int):
        super().__init__()
        self.bias = nn.Parameter(torch.zeros(num_features))

    def forward(self, x):
        return x + self.bias.view(1, -1, 1, 1).expand_as(x)


class CustomBatchNorm(nn.Module):
    def __init__(self, num_features, bnorm_init_gamma, bnorm_init_var, bnorm_decay, bnorm_epsilon):
        super().__init__()
        self.num_features = num_features
        self.bnorm_decay = bnorm_decay
        self.bnorm_epsilon = bnorm_epsilon

        self.gamma = nn.Parameter(torch.ones(num_features))
        self.moving_mean = nn.Parameter(torch.ones(num_features))
        self.moving_variance = nn.Parameter(torch.ones(num_features))

    def forward(self, x):
        _, C, _, _ = x.shape

        x = (x - self.moving_mean.reshape((1, C, 1, 1))) / torch.pow(
            self.moving_variance.reshape((1, C, 1, 1)) + self.bnorm_epsilon,
            0.5,
        )
        return self.gamma.reshape((1, C, 1, 1)) * x


class FullConvNet(nn.Module):
    def __init__(self, bnorm_decay, flag_train, num_levels: int = 17):
        super().__init__()

        self._num_levels = num_levels
        self._actfun = [nn.ReLU()] * (self._num_levels - 1) + [nn.Identity()]
        self._f_size = [3] * self._num_levels
        self._f_num_in = [1] + [64] * (self._num_levels - 1)
        self._f_num_out = [64] * (self._num_levels - 1) + [1]
        self._f_stride = [1] * self._num_levels
        self._bnorm = [False] + [True] * (self._num_levels - 2) + [False]
        self.conv_bias = [True] + [False] * (self._num_levels - 2) + [True]
        self._bnorm_init_var = 1e-4
        self._bnorm_init_gamma = torch.sqrt(torch.tensor(2.0 / (9.0 * 64.0)))
        self._bnorm_epsilon = 1e-5
        self._bnorm_decay = bnorm_decay

        self.level = [None] * self._num_levels
        self.flag_train = flag_train
        self.extra_train = []
        self.conv_layers = nn.ModuleList()

        for i in range(self._num_levels):
            self.conv_layers.append(
                self._conv_layer(
                    self._f_size[i],
                    self._f_num_in[i],
                    self._f_num_out[i],
                    self._f_stride[i],
                    self._bnorm[i],
                    self.conv_bias[i],
                    self._actfun[i],
                )
            )

    def forward(self, x):
        for i in range(self._num_levels):
            x = self.conv_layers[i](x)
            self.level[i] = x

        return x

    def _batch_norm(self, out_filters):
        batch_norm = CustomBatchNorm(
            out_filters,
            self._bnorm_init_gamma,
            self._bnorm_init_var,
            self._bnorm_decay,
            self._bnorm_epsilon,
        )
        return batch_norm

    def _conv_layer(self, filter_size, in_filters, out_filters, stride, apply_bnorm, conv_bias, actfun):
        layers = []
        layers.append(
            nn.Conv2d(
                in_channels=in_filters,
                out_channels=out_filters,
                kernel_size=filter_size,
                stride=stride,
                padding="same",
                bias=conv_bias,
            )
        )

        if apply_bnorm:
            layers.append(self._batch_norm(out_filters))

        # if the bias was not already added with Conv2d, we add it manually
        if not conv_bias:
            layers.append(AddBias(out_filters))

        layers.append(actfun)  # activation function

        return nn.Sequential(*layers)


def getNoiseprint(image_path: str, progress_callback: Optional[Callable[[float], None]] = None):
    """
    Compute the noiseprint for the given image using the pretrained model.

    This implementation is adapted from the original Noiseprint code by
    GRIP-UNINA (University Federico II of Naples).
    """

    img, mode = imread2f(image_path, channel=1)

    slide = 1024
    largeLimit = 1050000
    overlap = 34
    transform = transforms.ToTensor()

    try:
        QF = jpeg_qtableinv(image_path)
    except Exception:
        QF = 101

    net = FullConvNet(0.9, torch.tensor(False), num_levels=17)

    # Resolve pretrained weights path robustly
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # src/noiseprint_creation -> src
    project_root = project_root.parent        # src -> project_root

    model_path = project_root / "src" / "noiseprint_creation" / "pretrained_weights" / f"model_qf{int(QF)}.pth"
    file_path = str(model_path)

    if not os.path.exists(file_path):
        alt_path = Path("src") / "noiseprint_creation" / "pretrained_weights" / f"model_qf{int(QF)}.pth"
        if alt_path.exists():
            file_path = str(alt_path)
        else:
            raise FileNotFoundError(
                f"Noiseprint model file not found: {file_path}\n"
                f"Also tried: {alt_path}\n"
                f"Please ensure the pretrained weights are in: "
                f"{project_root / 'src' / 'noiseprint_creation' / 'pretrained_weights'}"
            )

    state_dict = torch.load(file_path, map_location="cpu")
    net.load_state_dict(state_dict)
    net.eval()

    with torch.no_grad():
        if img.shape[0] * img.shape[1] > largeLimit:
            print(" %dx%d large %3d" % (img.shape[0], img.shape[1], QF))
            # for large image the network is executed on windows with partial overlapping
            res = torch.zeros((img.shape[0], img.shape[1]), dtype=torch.float32).numpy()
            total_rows = img.shape[0]
            for index0 in range(0, img.shape[0], slide):
                # Calculate and report progress
                if progress_callback:
                    progress = (index0 / total_rows) * 100
                    progress_callback(progress)
                
                index0start = index0 - overlap
                index0start = index0 - overlap
                index0end = index0 + slide + overlap

                for index1 in range(0, img.shape[1], slide):
                    index1start = index1 - overlap
                    index1end = index1 + slide + overlap
                    clip = img[
                        max(index0start, 0) : min(index0end, img.shape[0]),
                        max(index1start, 0) : min(index1end, img.shape[1]),
                    ]

                    tensor_image = transform(clip)
                    tensor_image = tensor_image.reshape(1, 1, tensor_image.shape[1], tensor_image.shape[2])
                    resB = net(tensor_image)

                    resB = resB[0][0]

                    if index0 > 0:
                        resB = resB[overlap:, :]
                    if index1 > 0:
                        resB = resB[:, overlap:]
                    resB = resB[: min(slide, resB.shape[0]), : min(slide, resB.shape[1])]

                    res[
                        index0 : min(index0 + slide, res.shape[0]),
                        index1 : min(index1 + slide, res.shape[1]),
                    ] = resB
        else:
            print(" %dx%d small %3d" % (img.shape[0], img.shape[1], QF))
            if progress_callback:
                progress_callback(50.0) # Indicate halfway
            tensor_image = transform(img)
            tensor_image = tensor_image.reshape(1, 1, tensor_image.shape[1], tensor_image.shape[2])
            res = net(tensor_image)
            res = (res[0][0]).numpy()
            if progress_callback:
                progress_callback(100.0)

    return img, res

