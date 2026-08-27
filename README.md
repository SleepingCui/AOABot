# AOABot

[ADOFAI Offset analyzer](https://github.com/sleepingcui/adofai_offset_analyzer)的discord机器人

## 安装

```bash
pip install -r requirements.txt
```

## 安装&使用

### CLI

```bash
# 分析记录并生成全部默认图表（scatter, dist, pie, xacc）
python -m cli record.tlog

# 将所有图表拼合为一张大图
python -m acli record.tlog --combined

# 指定图表类型
python -m cli record.json -c scatter
```


### Discord 机器人

```bash
python -m main
# 编辑 `config.yml`，填入你的机器人 `token`，然后重新启动：
```

支持的文件格式： tlog,tlog.gz,json,crpl2
