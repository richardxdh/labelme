#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as osp
import json
import numpy as np


def extract_shape_from_labelme_json(labelme_json, labels):
    shapes = {}
    with open(labelme_json, 'r') as f:
        j = json.load((f))
        for shape in j["shapes"]:
            if shape["label"] in labels:
                shapes[shape["label"]] = shape["points"]

    return shapes


if __name__ == "__main__":

    json_path = osp.expanduser("~/Downloads/data/disco/issue_1218/S11/20201218T111146/S11_1/2.json")
    npz_path = osp.expanduser("~/code/github/labelme/labelme/config/basic_shapes.npz")

    shapes = {}
    if osp.exists(npz_path):
        shapes = dict(np.load(npz_path))

    new_shape = extract_shape_from_labelme_json(json_path, ["apple body",])
    shapes.update(new_shape)

    np.savez(npz_path, **shapes)

    npz_shape = np.load(npz_path)
    for f in npz_shape.files:
        d = npz_shape[f]
        print(f, type(d), d.shape, d.dtype)