import aie

aie.Authenticate()
aie.Initialize()

# 定义太湖的边界
taihu = aie.FeatureCollection("projects/ee-chinayaoyuting/assets/taihu")

# 获取最新的MODIS影像集合
modis_collection = (aie.ImageCollection('MODIS/061/MOD09GA')
    .filterDate('2021-01-01', '2021-12-31')
    .filterBounds(taihu))

# 定义云掩膜函数
def mask_clouds(image):
    qa = image.select('state_1km')
    cloud_bit_mask = 1 << 10
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0)
    return image.updateMask(mask)

# 定义NDCI (归一化叶绿素指数)计算函数
def calculate_ndci(image):
    b01 = image.select('sur_refl_b01').float()
    b03 = image.select('sur_refl_b03').float()
    b04 = image.select('sur_refl_b04').float()
    
    ndci = b01.subtract(b04).divide(b01.add(b04)).rename('NDCI')
    
    return image.addBands(ndci).select(['sur_refl_b01', 'sur_refl_b03', 'sur_refl_b04', 'NDCI']).float()

# 应用云掩膜和计算NDCI
processed_collection = (modis_collection
    .map(mask_clouds)
    .map(calculate_ndci)
    .map(lambda image: image.reproject('EPSG:4326', None, 500))
    .map(lambda image: image.clip(taihu).reproject('EPSG:4326', None, 500)))

# 筛选蓝藻面积大于100平方公里的影像
def filter_algal_bloom(image):
    algal_area = image.select('NDCI').gt(0.1).multiply(aie.Image.pixelArea()).reduceRegion(
        reducer=aie.Reducer.sum(),
        geometry=taihu,
        scale=500,
        maxPixels=1e9
    ).get('NDCI')
    return image.set('algalArea', algal_area)

algal_bloom_images = processed_collection.map(filter_algal_bloom).filter(aie.Filter.gt('algalArea', 100000000))

# 定义可视化参数
viz_params = {
    'bands': ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03'],
    'min': 0,
    'max': 3000,
    'gamma': 1.4
}

ndci_viz_params = {
    'bands': ['NDCI'],
    'min': -0.5,
    'max': 0.5,
    'palette': ['white','white','white', 'white','white','white','green', 'yellow', 'red']
}

# 在地图上添加所有符合条件的影像
Map = aie.Map()
Map.centerObject(taihu, 9)

# 使用getInfo()来获取影像集合的大小
count = algal_bloom_images.size().getInfo()

# 遍历并添加每个影像到地图
for i in range(count):
    image = aie.Image(algal_bloom_images.toList(count).get(i))
    date = aie.Date(image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
    
    # 添加NDCI图层
    Map.addLayer(image, ndci_viz_params, f'Image {i + 1} NDCI ({date})')
    
    # 打印图像的时间戳
    print(f'Image {i + 1} Date: {date}')

# 显示地图
Map.getMapId()