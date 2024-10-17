
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from aiearth.analytics import Analytics
from aiearth.analytics.raster import RasterCollection

# 初始化Analytics对象
analytics = Analytics()

# 定义太湖的边界（假设已经有了太湖的边界数据）
taihu_geom = analytics.read_vector("path/to/taihu_boundary.geojson")

# 设置时间范围
start_date = datetime(2021, 1, 1)
end_date = datetime(2021, 12, 31)

# 获取MODIS影像集合
modis_collection = RasterCollection.from_modis(
    product="MOD09GA",
    start_time=start_date,
    end_time=end_date,
    geometry=taihu_geom
)

# 定义云掩膜函数
def mask_clouds(image):
    qa = image.select('state_1km')
    cloud_bit_mask = 1 << 10
    mask = (qa & cloud_bit_mask) == 0
    return image.updateMask(mask)

# 定义NDCI计算函数
def calculate_ndci(image):
    b01 = image.select('sur_refl_b01').astype(float)
    b03 = image.select('sur_refl_b03').astype(float)
    b04 = image.select('sur_refl_b04').astype(float)
    
    ndci = (b01 - b04) / (b01 + b04)
    ndci = ndci.rename('NDCI')
    
    return image.addBands(ndci)

# 应用云掩膜和计算NDCI
processed_collection = modis_collection.map(mask_clouds).map(calculate_ndci)

# 筛选蓝藻面积大于100平方公里的影像
def filter_algal_bloom(image):
    algal_area = image.select('NDCI').gt(0.1).multiply(image.pixelArea()).reduceRegion(
        reducer='sum',
        geometry=taihu_geom,
        scale=500,
        maxPixels=1e9
    ).get('NDCI')
    
    return image.set('algalArea', algal_area)

algal_bloom_images = processed_collection.map(filter_algal_bloom).filter(lambda img: img.get('algalArea') > 100000000)

# 可视化参数
ndci_viz_params = {
    'bands': ['NDCI'],
    'min': -0.5,
    'max': 0.5,
    'palette': ['white', 'white', 'white', 'white', 'white', 'white', 'green', 'yellow', 'red']
}

# 获取符合条件的影像列表
image_list = algal_bloom_images.getInfo()

# 遍历并可视化每个影像
for i, image in enumerate(image_list):
    date = datetime.fromtimestamp(image['properties']['system:time_start'] / 1000).strftime('%Y-%m-%d')
    
    # 可视化NDCI图层
    fig, ax = plt.subplots(figsize=(12, 8))
    algal_bloom_images[i].visualize(bands=['NDCI'], vis_params=ndci_viz_params, ax=ax)
    ax.set_title(f'Image {i+1} NDCI ({date})')
    plt.show()
    
    print(f'Image {i+1} Date: {date}')

# 保存结果（如果需要）
# algal_bloom_images.save("path/to/save/results")