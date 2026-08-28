# AOABot

[ADOFAI Offset analyzer](https://github.com/sleepingcui/adofai_offset_analyzer)的discord机器人

## 安装

```bash
git clone https://github.com/SleepingCui/AOABot.git
cd AOABot
pip install -r requirements.txt
```

## 安装&使用

### CLI

```bash
# 分析记录并生成全部默认图表（scatter, dist, pie, xacc）
python -m cli record.tlog

# 将所有图表拼合为一张大图
python -m cli record.tlog --combined

# 指定图表类型
python -m cli record.json -c scatter
```


### Discord 机器人

```bash
python -m main
# 编辑 config.yml，填入你的机器人token，然后重新启动
```

支持的文件格式： tlog,tlog.gz,json,crpl2

## ScreenShots
<img width="929" height="919" alt="屏幕截图 2026-08-27 194850" src="https://github.com/user-attachments/assets/9662d3c6-838e-4b3a-a60a-ec75f1c788f2" />
<img width="939" height="854" alt="屏幕截图 2026-08-27 194754" src="https://github.com/user-attachments/assets/00fd0cf5-e603-4184-aff3-ab1698192518" />

## 扩展

### 新建一个扩展

`myext.py`：

```python
import logging

from discord.ext import commands

logger = logging.getLogger(__name__)


class XxxCog(commands.Cog, name="Xxx"):
    """插件描述（必填）"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="xxx", aliases=["xx"])
    async def xxx_cmd(self, ctx):
        """命令描述（必填）"""
        await ctx.send("hello")


async def setup(bot):
    await bot.add_cog(XxxCog(bot))
```

把文件放进 `cogs/` 即可，启动时 `main.py` 会自动发现并加载

**命令必须加入 `allowed_commands` 才能被使用**（白名单检查在 `main.py` 的 `whitelist_check`）


## License
MIT
