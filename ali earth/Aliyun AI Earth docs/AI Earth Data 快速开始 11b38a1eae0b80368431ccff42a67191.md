# AI Earth Data 快速开始

```python
python -m pip install -U "aie-sdk[data]"
```

**鉴权**

```python
from aiearth import core
core.Authenticate()
```

**搜索数据并获取一个切片**

```python
from aiearth import core

from aiearth.data.search import opendata_client
from aiearth.data.loader import DataLoader
from aiearth.data.stac_id import OpenStacId
from datetime import datetime
import numpy as np

# 鉴权
core.Authenticate()
# 获取公开数据检索的client
client_opendata = opendata_client()
# bbox为检索区域，目标是 Sentinel-MSIL2A 数据，时间范围为 2022-1-1 到 2022-03-01的数据，
# 最后按照云量数据从小到大排序
bbox = [116.30526075575888, 39.856226715750836, 116.45625485992359, 39.96534081463834]
search_req = client_opendata.search(collections=['SENTINEL_MSIL2A'], bbox=bbox,
                                    sortby=['+eo:cloud_cover'],
                                    datetime=(datetime(2022, 1, 1), datetime(2022, 3, 1)))
# 获取搜索结果数据的第一个
item = list(search_req.items())[0]
# 打印数据的ID
print(item.id)

# 下面进行数据的获取
# 构建DataLoader
dataloader = DataLoader(OpenStacId(item.id))
dataloader.load()

# 目标为了获取 B4, B3, B2波段的数据，这三个数据长宽一致，使用B4为例
shape = item.assets['B4'].extra_fields['proj:shape']
width, height = shape
print(width, height)

# 切这张影像的中间的1024* 1024的一片
# 我们建议每次切片offset和size都是128的倍数
x_offset = 1024 * 5
y_offset = 1024 * 5
x_size = 1024
y_size = 1024

img = np.ndarray(shape=(y_size, x_size, 3))
for band_idx, band_name in enumerate(('B4', 'B3', 'B2')):
    block = dataloader.block(band_name = band_name, offset_size=(x_offset, y_offset, x_size, y_size))
    img[:, :, band_idx] = block

# 将切片内容按照RGB打印为图片
from matplotlib import pyplot as plt
img[img > 3500] = 3500
img[img < 0] = 0
normed_img = img / 3500
plt.imshow(normed_img)
```

**属性过滤查询**

```python
from datetime import datetime

from aiearth import core
from aiearth.data.search import opendata_client

# 鉴权
core.Authenticate()
# 获取 STAC 客户端
client_opendata = opendata_client()

date1 = datetime(2023, 1, 15)
date2 = datetime(2023, 1, 30)
# bbox格式: [经度_min，纬度_min，经度_max，纬度_max]
bbox = [112.46, 4.86, 112.55, 4.95]
# 属性参考数据集资源页的数据属性: https://engine-aiearth.aliyun.com/#/dataset/SENTINEL_MSIL2A
query=['eo:cloud_cover<=100', "sat:relative_orbit=118"]
geojson={"type":"Polygon","coordinates":[[[115.5023,49.1866],[118.8966,49.1866],[118.8966,51.3419],[115.5023,51.3419],[115.5023,49.1866]]]}
# 限制查询结果总个数
max_items=23
search_req = client_opendata.search(collections=['SENTINEL_MSIL2A'],
                                    intersects=geojson,
                                    query=query,
                                    sortby=['+eo:cloud_cover'],
                                    datetime=(date1, date2),
                                    max_items=max_items)
req_list = list(search_req.items())
print(len(req_list))
for item in req_list:
    print(item.id)
```

**AI Earth Data 使用案例-搜索公开数据，获取一张切片并展示**

```python
from aiearth import core

from aiearth.data.search import opendata_client
from aiearth.data.loader import DataLoader
from aiearth.data.stac_id import OpenStacId
from datetime import datetime
import numpy as np

# 鉴权
core.Authenticate()
# 获取公开数据检索的client
client_opendata = opendata_client()
# bbox为检索区域，目标是 Sentinel-MSIL2A 数据，时间范围为 2022-1-1 到 2022-03-01的数据，
# 最后按照云量数据从小到大排序
bbox = [116.30526075575888, 39.856226715750836, 116.45625485992359, 39.96534081463834]
search_req = client_opendata.search(collections=['SENTINEL_MSIL2A'], bbox=bbox,
                                    sortby=['+eo:cloud_cover'],
                                    datetime=(datetime(2022, 1, 1), datetime(2022, 3, 1)))
# 获取搜索结果数据的第一个
item = list(search_req.items())[0]
# 打印数据的ID
print(item.id)

# 下面进行数据的获取
# 构建DataLoader
dataloader = DataLoader(OpenStacId(item.id))
dataloader.load()

# 目标为了获取 B4, B3, B2波段的数据，这三个数据长宽一致，使用B4为例
shape = item.assets['B4'].extra_fields['proj:shape']
width, height = shape
print(width, height)

# 切这张影像的中间的1024* 1024的一片
# 我们建议每次切片offset和size都是128的倍数
x_offset = 1024 * 5
y_offset = 1024 * 5
x_size = 1024
y_size = 1024

img = np.ndarray(shape=(y_size, x_size, 3))
for band_idx, band_name in enumerate(('B4', 'B3', 'B2')):
    block = dataloader.block(band_name = band_name, offset_size=(x_offset, y_offset, x_size, y_size))
    img[:, :, band_idx] = block

# 将切片内容按照RGB打印为图片
from matplotlib import pyplot as plt
img[img > 3500] = 3500
img[img < 0] = 0
normed_img = img / 3500
plt.imshow(normed_img)
```

**搜索个人数据，获取一张切片并展示**

```python
import numpy as np
from aiearth import core
import aiearth.data.search
from aiearth.data.search import PersonalQueryBuilder, personaldata_client, opendata_client
from aiearth.data.loader import DataLoader
from aiearth.data.stac_id import PersonalStacId, OpenStacId
from matplotlib import pyplot as plt

from datetime import datetime
import numpy as np

# 鉴权
core.Authenticate()
# 获取 STAC 客户端
client_personal = personaldata_client()
# 查询名称中包含 test_name，并且发布时间在 2023-07-16 到 2023-07-18之间的数据
queryBuilder = PersonalQueryBuilder().and_name_contains("test_name")\
    .and_upload_datetime_between(datetime(2023, 7, 16), datetime(2023, 7 , 18))
search_req = personaldata_client().search(query=queryBuilder.build())

# 获取查询结果的第一个
item = list(search_req.items())[0]
print(item.id)

# 使用B1, B2, B3 查询所有数据
dataloader = DataLoader(PersonalStacId(item.id))
dataloader.load()

# 举个例子，我们想获取下面这个BBOX的数据
x_min = (item.bbox[2] - item.bbox[0]) / 10 * 5 + item.bbox[0]
y_min = (item.bbox[3] - item.bbox[1]) / 10 * 5 + item.bbox[1]
x_max = (item.bbox[2] - item.bbox[0]) / 10 * 7 + item.bbox[0]
y_max = (item.bbox[3] - item.bbox[1]) / 10 * 7 + item.bbox[1]
aoi_bbox = x_min, y_min, x_max, y_max
# aoi_bbox is in CRS EPSG:4326

channels = list()
for idx, band_name in enumerate(('B1', 'B2', 'B3')):
    channel = dataloader.block(band_name, bbox=aoi_bbox, bbox_crs=4326)
    channels.append(channel)
img = np.ndarray(shape=(channels[0].shape[0], channels[0].shape[1], 3))
for i in range(3):
    img[:, :, i] = channels[i]
newimg = ((img - np.amin(img)) / (np.amax(img) - np.amin(img)) * 255).astype('uint8')
plt.imshow(newimg)
```

## **属性过滤查询**

```python
from datetime import datetime

from aiearth import core
from aiearth.data.search import opendata_client

# 鉴权
core.Authenticate()
# 获取 STAC 客户端
client_opendata = opendata_client()

date1 = datetime(2023, 1, 15)
date2 = datetime(2023, 1, 30)
# bbox格式: [经度_min，纬度_min，经度_max，纬度_max]
bbox = [112.46, 4.86, 112.55, 4.95]
# 属性参考数据集资源页的数据属性: https://engine-aiearth.aliyun.com/#/dataset/SENTINEL_MSIL2A
# 支持的比较操作包括：>=, <=, >, <, =
query=['eo:cloud_cover<=100', "sat:relative_orbit=118"]
geojson={"type":"Polygon","coordinates":[[[115.5023,49.1866],[118.8966,49.1866],[118.8966,51.3419],[115.5023,51.3419],[115.5023,49.1866]]]}
# 限制查询结果总个数
max_items=23
search_req = client_opendata.search(collections=['SENTINEL_MSIL2A'],
                                    intersects=geojson,
                                    query=query,
                                    sortby=['+eo:cloud_cover'],
                                    datetime=(date1, date2),
                                    max_items=max_items)
req_list = list(search_req.items())
print(len(req_list))
for item in req_list:
    print(item.id)

```