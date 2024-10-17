# AI Earth Deeplearning 快速开始

```python
import aie

aie.Authenticate()
aie.Initialize()

work_dir = "./work_dirs/tutorial"

# 下载云平台开放数据集
from aiearth.deeplearning.cloud.datasets import LandcoverDataset, PublicDatasetMeta
gid_15_train_dataset = LandcoverDataset(PublicDatasetMeta.GID_15_TRAIN["dataset_id"], data_root=work_dir)

# 将数据集拆分成训练集、验证集
from aiearth.deeplearning.sampler import RandomNonGeoDatasetSampler
# 随机按照80%， 20%进行切分成两个新样本集
train_dataset, val_dataset = RandomNonGeoDatasetSampler.split_by_percent(gid_15_train_dataset, 0.8)
# 随机提取20张图生成新样本集
test_dataset = RandomNonGeoDatasetSampler.sample_by_count(gid_15_train_dataset, 20) 

# 加载预训练模型

from aiearth.deeplearning.trainer.mmseg import LandcoverTrainer

trainer = LandcoverTrainer(work_dir=work_dir, config_name="fcn_hr48_1024x1024_16k_landcover")

# 设置样本集
trainer.setup_datasets(train_dataset)
trainer.setup_datasets(val_dataset, data_type="val")
trainer.setup_datasets(test_dataset, data_type="test")

# 设置pretrained model
from aiearth.deeplearning.model_zoo.model import PretrainedModel
model = PretrainedModel("aie://LandCover/landcover_v1.6.pth")
trainer.load_from(model.local_path)

# 设置训练参数
trainer.cfg.runner["max_iters"] = 2  
trainer.cfg.checkpoint_config["interval"]=1
trainer.cfg.data.samples_per_gpu = 1

# 训练
trainer.train(validate=False)

# 训练完成之后，会按照设置生成相应的checkpoint
import os
# 保存的训练checkpoint路径
checkpoint = os.path.join(work_dir, "latest.pth")

# 模型测试
trainer.test(checkpoint, output_dir="test_ret")

# 模型导出
onnx_path = checkpoint.replace(".pth", ".onnx")

trainer.export_onnx(output_file=onnx_path, checkpoint_path=checkpoint,shape=(1024, 1024))

```

**AI Earth Deeplearning 使用案例**

```python
from aiearth.deeplearning.job import TrainJob
from aiearth.deeplearning.cloud.datasets import LandcoverDataset, PublicDatasetMeta
from aiearth.deeplearning.trainer.mmseg import LandcoverTrainer
from aiearth.deeplearning.sampler import RandomNonGeoDatasetSampler
from aiearth.deeplearning.model_zoo.model import PretrainedModel

class Job(TrainJob):
    work_dir = "./work_dirs/tutorial"
    classes = ['背景', 'industrial_land', 'garden_land', 'urban_residential', 'arbor_forest', 'rural_residential', 'shrub_land', 'traffic_land', 'natural_meadow', 'paddy_field', 'artificial_meadow', 'irrigated_land', 'river', 'dry_cropland', 'lake', 'pond']
    def set_trainer(self):
        trainer = LandcoverTrainer(work_dir=self.work_dir, config_name="fcn_hr48_1024x1024_16k_landcover")

        # 设置pretrained model
        model = PretrainedModel("aie://LandCover/landcover_v1.6.pth")
        trainer.load_from(model.local_path)

        trainer.cfg.runner["max_iters"] = 2  
        trainer.cfg.checkpoint_config["interval"]=1
        trainer.cfg.data.samples_per_gpu = 1
        return trainer

    def set_datasets(self):
        # dataset from AIEarth platform
        gid_15_train_dataset = LandcoverDataset(PublicDatasetMeta.GID_15_TRAIN["dataset_id"], data_root=self.work_dir)

        # 随机按照80%， 20%进行切分成两个新样本集
        train_dataset, val_dataset = RandomNonGeoDatasetSampler.split_by_percent(gid_15_train_dataset, 0.8)
        self.datasets["train"].append(train_dataset)
        self.datasets["val"].append(val_dataset)
        
import aie
from aiearth.deeplearning.cloud.trainer import JobCloudWrap

if __name__ == '__main__':
    # 必须设置aie参数
    aie.Authenticate()
    aie.Initialize()

    # 创建任务实例
    job = Job()

    job = JobCloudWrap(
        job=job,
        model_name="landcover_0.1",
        code_dir='.',
        desc="from sdk",
    )

    # 启动云上模型训练
    job.run()

```